"""
Main pipeline: ingest schema + rules -> generate -> resolve FKs -> messiness -> drift -> CDC -> anomalies -> validate -> export.
"""

import time
from pathlib import Path
from typing import Any

from data_forge.config import OutputFormat
from data_forge.performance import collect_performance_warnings, build_materialization_diagnostics
from data_forge.models.generation import (
    DataLayer,
    DriftProfile,
    GenerationRequest,
    GenerationResult,
    MessinessProfile,
    TableSnapshot,
)
from data_forge.models.schema import SchemaModel
from data_forge.models.rules import RuleSet
from data_forge.schema_ingest import load_schema
from data_forge.rule_engine import load_rule_set
from data_forge.generators.primitives import PrimitiveGenerator
from data_forge.generators.row_planner import default_plan_row_counts
from data_forge.generators.table import generate_table
from data_forge.generators.generation_rules import validate_generation_rule
from data_forge.generators.relationship_builder import RelationshipBuilder
from data_forge.generators.cdc_simulator import apply_mode as apply_cdc_mode
from data_forge.generators.messiness import apply_messiness
from data_forge.generators.schema_drift import apply_drift
from data_forge.generators.layers import transform_to_layer
from data_forge.anomaly_injector import inject_anomalies
from data_forge.validators.quality import compute_quality_report
from data_forge.exporters import export_tables, export_snapshots, export_table_iter
from data_forge.pii.classifier import classify_schema
from data_forge.pii.redaction import RedactionConfig
from data_forge.pipeline import (
    timed_stage,
    STAGE_GENERATE,
    STAGE_RESOLVE_FK,
    STAGE_DRIFT,
    STAGE_CDC,
    STAGE_MESSINESS,
    STAGE_QUALITY,
)


def run_generation(
    request: GenerationRequest,
    schema_path: Path | str | None = None,
    rules_path: Path | str | None = None,
    schema: SchemaModel | None = None,
    rule_set: RuleSet | None = None,
    verbose: bool = False,
    timings_out: dict[str, float] | None = None,
) -> GenerationResult:
    """
    Run the full pipeline: load schema/rules if paths given, then generate,
    resolve relationships, optionally inject anomalies, validate, and attach quality report.
    """
    from data_forge.performance import verbose_log

    def _log(e: str, **kw: Any) -> None:
        verbose_log(verbose, e, **kw)

    errors: list[str] = []
    timings: dict[str, float] = {}
    if timings_out is not None:
        timings = timings_out

    if schema is None and schema_path:
        t0 = time.perf_counter()
        try:
            schema = load_schema(Path(schema_path))
            timings["schema_load_seconds"] = round(time.perf_counter() - t0, 4)
        except Exception as e:
            return GenerationResult(
                request=request,
                success=False,
                errors=[f"Schema load failed: {e}"],
            )
    if schema is None:
        return GenerationResult(request=request, success=False, errors=["No schema provided"])
    schema_errors = schema.validate_schema()
    if schema_errors:
        return GenerationResult(request=request, success=False, errors=schema_errors)
    t0 = time.perf_counter()
    if rule_set is None and rules_path:
        rule_set = load_rule_set(Path(rules_path))
    timings["rule_load_seconds"] = round(time.perf_counter() - t0, 4)
    if rule_set is None:
        rule_set = RuleSet(name="default")

    for gr in rule_set.generation_rules:
        val_errors = validate_generation_rule(gr)
        if val_errors:
            return GenerationResult(
                request=request,
                success=False,
                errors=[f"Generation rule {gr.table}.{gr.column}: " + "; ".join(val_errors)],
            )

    tables_order = schema.dependency_order()
    if request.tables_filter:
        tables_order = [t for t in tables_order if t.name in request.tables_filter]
    row_counts = default_plan_row_counts(schema, request.scale, request.tables_filter)
    approx_cols_by_table = {t.name: len(t.columns) for t in tables_order}
    materialization = build_materialization_diagnostics(
        row_counts=row_counts,
        approx_cols_by_table=approx_cols_by_table,
        layer=request.layer.value,
    )
    primitive_gen = PrimitiveGenerator(seed=request.seed, locale=request.locale)
    rel_builder = RelationshipBuilder(schema)
    table_data: dict[str, list[dict[str, Any]]] = {}
    scale = request.scale
    chunk_size = getattr(request, "chunk_size", None)
    start = time.perf_counter()
    with timed_stage(STAGE_GENERATE, timings):
        for table in tables_order:
            row_count = row_counts.get(table.name, scale)
            if chunk_size and row_count > chunk_size:
                all_rows: list[dict[str, Any]] = []
                for off in range(0, row_count, chunk_size):
                    chunk = generate_table(
                        table,
                        row_count,
                        primitive_gen,
                        rule_set,
                        parent_key_supplier=None,
                        seed=request.seed + hash(table.name),
                        offset=off,
                        limit=chunk_size,
                        locale=request.locale,
                    )
                    all_rows.extend(chunk)
                    _log("chunk_generated", table=table.name, offset=off, count=len(chunk))
                table_data[table.name] = all_rows
            else:
                rows = generate_table(
                    table,
                    row_count,
                    primitive_gen,
                    rule_set,
                    parent_key_supplier=None,
                    seed=request.seed + hash(table.name),
                    locale=request.locale,
                )
                table_data[table.name] = rows

    with timed_stage(STAGE_RESOLVE_FK, timings):
        rel_builder.assign_foreign_keys(table_data)

    drift_events: list[dict[str, Any]] = []
    with timed_stage(STAGE_DRIFT, timings):
        if request.drift_profile != DriftProfile.NONE:
            schema, table_data, drift_events = apply_drift(
                schema, table_data, request.drift_profile, request.seed
            )

    with timed_stage(STAGE_CDC, timings):
        apply_cdc_mode(
            table_data,
            request.mode,
            request.change_ratio,
            request.seed,
            request.batch_id,
        )

    with timed_stage(STAGE_MESSINESS, timings):
        apply_messiness(table_data, request.messiness, request.seed)

    anomaly_ratio = request.anomaly_ratio
    if request.messiness == MessinessProfile.CLEAN:
        anomaly_ratio = min(anomaly_ratio, 0.01)
    elif request.messiness == MessinessProfile.CHAOTIC:
        anomaly_ratio = max(anomaly_ratio, 0.05)
    if request.include_anomalies and anomaly_ratio > 0:
        for name in table_data:
            table_data[name] = inject_anomalies(
                table_data[name],
                ratio=anomaly_ratio,
                seed=request.seed + hash(name),
            )

    layers_data: dict[str, dict[str, list[dict[str, Any]]]] = {}
    layer_materialization = getattr(request, "layer_materialization", "eager") or "eager"
    if layer_materialization not in ("eager", "lazy"):
        layer_materialization = "eager"
    if request.layer == DataLayer.ALL:
        # Keep bronze as the already-generated table_data to avoid one extra full-table copy.
        layers_data["bronze"] = table_data
        if layer_materialization == "eager":
            layers_data["silver"] = transform_to_layer(layers_data["bronze"], "silver")
            layers_data["gold"] = transform_to_layer(layers_data["bronze"], "gold")
        else:
            _log("layer_materialization", strategy=layer_materialization)
    else:
        layer_name = request.layer.value
        layers_data[layer_name] = table_data

    # PII classification and privacy
    pii_result = classify_schema(schema)
    pii_detection = pii_result.pii_detection
    privacy_mode = getattr(request, "privacy_mode", "off") or "off"
    redaction_enabled = privacy_mode in ("warn", "strict")
    redaction_config = RedactionConfig(enabled=redaction_enabled)
    privacy_warnings = pii_result.warnings if privacy_mode != "off" else []

    with timed_stage(STAGE_QUALITY, timings):
        quality_report = compute_quality_report(
            schema,
            table_data,
            rule_set=rule_set,
            mode=request.mode,
            layer=request.layer,
            drift_events=drift_events,
            pii_detection=pii_detection,
            privacy_mode=privacy_mode,
            redaction_config=redaction_config,
            privacy_warnings=privacy_warnings,
            privacy_policy_mode=getattr(request, "privacy_policy_mode", "advisory") or "advisory",
            privacy_policy_max_risk_score=getattr(request, "privacy_policy_max_risk_score", None),
            privacy_policy_max_sensitive_columns=getattr(
                request, "privacy_policy_max_sensitive_columns", None
            ),
            privacy_policy_fail_on_high_risk=bool(
                getattr(request, "privacy_policy_fail_on_high_risk", False)
            ),
            privacy_policy_block_categories=getattr(
                request, "privacy_policy_block_categories", None
            ),
        )

    duration = time.perf_counter() - start
    timings["total_seconds"] = round(duration, 4)

    perf_warnings = collect_performance_warnings(
        scale, chunk_size, (request.export_format or "parquet")
    )
    if request.layer == DataLayer.ALL and layer_materialization == "lazy":
        perf_warnings.append(
            "Layer materialization strategy is lazy; silver/gold are derived at export-time."
        )
    perf_warnings.extend(materialization.get("warnings", []))
    perf_warnings = list(dict.fromkeys(perf_warnings))
    quality_report["performance_warnings"] = perf_warnings
    quality_report["materialization"] = materialization
    quality_report["materialization"]["layer_materialization"] = layer_materialization
    quality_report["timings"] = timings
    policy = quality_report.get("privacy_policy", {})
    if policy.get("policy_decision") == "block" and policy.get("enforced"):
        errors.append(
            "Privacy policy blocked run: "
            + "; ".join(policy.get("violations", []) or ["policy violation"])
        )
        return GenerationResult(
            request=request,
            quality_report=quality_report,
            duration_seconds=round(duration, 2),
            success=False,
            errors=errors,
            drift_events=drift_events,
            timings=timings,
            performance_warnings=perf_warnings,
        )

    snapshots: list[TableSnapshot] = []
    active_data = layers_data.get("bronze", layers_data.get(request.layer.value, table_data))
    for name, rows in active_data.items():
        cols = list(rows[0].keys()) if rows else []
        snapshots.append(
            TableSnapshot(
                table_name=name,
                columns=cols,
                rows=rows,
                row_count=len(rows),
                layer=request.layer.value,
            )
        )

    warehouse_load: dict[str, Any] | None = None
    load_target = getattr(request, "load_target", None)
    load_params = getattr(request, "load_params", None) or {}
    db_uri = getattr(request, "db_uri", None) or ""
    if load_target and (db_uri or load_target.lower() in ("snowflake", "bigquery")):
        from data_forge.adapters.load import load_to_database
        from data_forge.warehouse_validation import run_warehouse_validation
        res = GenerationResult(request=request, tables=snapshots, quality_report={}, success=True)
        batch_size = getattr(request, "batch_size", 1000)
        warehouse_load = load_to_database(
            res, schema, load_target, db_uri, batch_size=batch_size, load_params=load_params
        )
        quality_report["warehouse_load"] = warehouse_load
        if "load_seconds" in warehouse_load:
            timings["warehouse_load_seconds"] = warehouse_load["load_seconds"]
        if warehouse_load.get("success"):
            wv = run_warehouse_validation(warehouse_load, schema, snapshots, target=load_target)
            quality_report["warehouse_validation"] = wv
        if not warehouse_load.get("success") and warehouse_load.get("error"):
            errors.append(f"Database load failed: {warehouse_load['error']}")

    return GenerationResult(
        request=request,
        tables=snapshots,
        quality_report=quality_report,
        duration_seconds=round(duration, 2),
        success=True,
        errors=errors,
        layers_data=layers_data if request.layer == DataLayer.ALL else None,
        drift_events=drift_events,
        warehouse_load=warehouse_load,
        timings=timings,
        performance_warnings=perf_warnings,
    )


def export_result(
    result: GenerationResult,
    output_dir: Path | str,
    fmt: OutputFormat | str = "parquet",
    sql_dialect: str = "postgresql",
    layer: DataLayer | None = None,
    timings_out: dict[str, float] | None = None,
) -> list[Path]:
    """Export a GenerationResult to files. When layer=ALL, exports to output/bronze, output/silver, output/gold.
    If timings_out is provided, records export_seconds."""
    import time
    output_dir = Path(output_dir)
    paths: list[Path] = []
    t0 = time.perf_counter()
    if result.layers_data:
        # Lazy strategy stores only bronze and derives silver/gold at export-time.
        if result.request.layer == DataLayer.ALL and "silver" not in result.layers_data:
            bronze = result.layers_data.get("bronze", {})
            bronze_dir = output_dir / "bronze"
            paths.extend(export_tables(bronze, bronze_dir, fmt=fmt, sql_dialect=sql_dialect))
            for target_layer in ("silver", "gold"):
                layer_dir = output_dir / target_layer
                layer_dir.mkdir(parents=True, exist_ok=True)
                for table_name, rows in bronze.items():
                    transformed_rows = transform_to_layer({table_name: rows}, target_layer)[table_name]
                    path = export_table_iter(
                        iter(transformed_rows),
                        layer_dir / table_name,
                        fmt=fmt,
                        table_name=table_name,
                        sql_dialect=sql_dialect,
                    )
                    if path:
                        paths.append(path)
        else:
            for layer_name, table_data in result.layers_data.items():
                layer_dir = output_dir / layer_name
                paths.extend(export_tables(table_data, layer_dir, fmt=fmt, sql_dialect=sql_dialect))
    else:
        # Export snapshots directly to avoid rebuilding a duplicate full table_data mapping.
        paths = export_snapshots(result.tables, output_dir, fmt=fmt, sql_dialect=sql_dialect)
    if timings_out is not None:
        timings_out["export_seconds"] = round(time.perf_counter() - t0, 4)
    return paths
