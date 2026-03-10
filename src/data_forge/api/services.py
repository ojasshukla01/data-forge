"""API services that bridge UI requests to Data Forge backend."""

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any

from data_forge.domain_packs import get_pack
from data_forge.engine import run_generation, export_result
from data_forge.models.generation import (
    DataLayer,
    DriftProfile,
    GenerationMode,
    GenerationRequest,
    MessinessProfile,
)
from data_forge.config import OutputFormat
from data_forge.schema_ingest import load_schema
from data_forge.rule_engine import load_rule_set
from data_forge.config import Settings


def _run_integrations(
    result: Any,
    output_dir: Path,
    schema_obj: Any,
    rule_set: Any,
    schema_path: Path | None,
    req: Any,
) -> tuple[list[Path], dict[str, Any]]:
    """
    Run dbt, GE, Airflow, contracts, manifest when requested.
    Returns (additional_artifact_paths, integration_summaries).
    """
    artifact_paths: list[Path] = []
    summaries: dict[str, Any] = {}

    table_data = {t.table_name: t.rows for t in result.tables} if hasattr(result, "tables") else {}
    data_layer = getattr(result.request, "layer", None)
    layer_val = data_layer.value if hasattr(data_layer, "value") else str(data_layer or "bronze")

    # dbt export
    if getattr(req, "export_dbt", False):
        try:
            from data_forge.dbt_export import export_dbt as do_export_dbt
            dbt_out = Path(getattr(req, "dbt_dir", None) or "") or (output_dir / "dbt")
            dbt_out = dbt_out if dbt_out.is_absolute() else (output_dir / "dbt")
            report = do_export_dbt(table_data, schema_obj, dbt_out)
            summaries["dbt_export"] = report
            for seed in report.get("seeds_generated", []):
                artifact_paths.append(dbt_out / "seeds" / seed)
            if report.get("sources_file"):
                artifact_paths.append(Path(report["sources_file"]))
            if report.get("schema_tests_file"):
                artifact_paths.append(Path(report["schema_tests_file"]))
        except Exception as e:
            summaries["dbt_export"] = {"enabled": True, "error": str(e)}

    # GE export
    if getattr(req, "export_ge", False) and schema_obj:
        try:
            from data_forge.ge_export import export_ge
            ge_out = Path(getattr(req, "ge_dir", None) or "") or (output_dir / "great_expectations")
            ge_out = ge_out if ge_out.is_absolute() else (output_dir / "great_expectations")
            report = export_ge(schema_obj, rule_set, ge_out)
            summaries["ge_export"] = report
            if report.get("checkpoint_path"):
                artifact_paths.append(Path(report["checkpoint_path"]))
        except Exception as e:
            summaries["ge_export"] = {"enabled": True, "error": str(e)}

    # Airflow export
    if getattr(req, "export_airflow", False):
        try:
            from data_forge.airflow_export import export_airflow
            af_out = Path(getattr(req, "airflow_dir", None) or "") or (output_dir / "airflow")
            af_out = af_out if af_out.is_absolute() else (output_dir / "airflow")
            tpl = getattr(req, "airflow_template", "generate_only") or "generate_only"
            if tpl not in ("generate_only", "generate_and_load", "generate_validate_and_load", "benchmark_pipeline"):
                tpl = "generate_only"
            report = export_airflow(tpl, af_out)
            summaries["airflow_export"] = report
            for p in report.get("paths", []) or []:
                artifact_paths.append(Path(p))
        except Exception as e:
            summaries["airflow_export"] = {"enabled": True, "error": str(e)}

    # Contracts (requires OpenAPI schema file)
    if getattr(req, "contracts", False) and schema_path and schema_path.exists():
        try:
            raw = schema_path.read_text(encoding="utf-8")
            if schema_path.suffix.lower() in (".json",):
                data = json.loads(raw)
            elif schema_path.suffix.lower() in (".yaml", ".yml"):
                import yaml
                data = yaml.safe_load(raw)
            else:
                data = {}
            if isinstance(data, dict) and ("openapi" in data or "swagger" in data):
                from data_forge.contracts.fixtures import generate_contract_fixtures
                contracts_dir = output_dir / "contracts"
                paths_out = generate_contract_fixtures(schema_path, contracts_dir, seed=getattr(req, "seed", 42))
                summaries["contracts"] = {
                    "enabled": True,
                    "output_dir": str(contracts_dir),
                    "fixtures_generated": [str(p) for p in paths_out],
                }
                artifact_paths.extend(paths_out)
            else:
                summaries["contracts"] = {"enabled": True, "skipped": "Schema is not OpenAPI"}
        except Exception as e:
            summaries["contracts"] = {"enabled": True, "error": str(e)}

    # Manifest
    if getattr(req, "write_manifest", False):
        try:
            from data_forge.golden import create_manifest, schema_signature, write_manifest as write_manifest_file
            schema_sig = schema_signature(schema_obj) if schema_obj else ""
            row_counts = {t.table_name: t.row_count for t in result.tables}
            mode_val = getattr(result.request.mode, "value", str(getattr(result.request, "mode", "full_snapshot")))
            manifest = create_manifest(
                seed=getattr(req, "seed", 42),
                mode=mode_val,
                layer=layer_val,
                row_counts=row_counts,
                schema_sig=schema_sig,
            )
            manifest_path = output_dir / "manifest.json"
            write_manifest_file(manifest, manifest_path)
            summaries["manifest"] = {"enabled": True, "manifest_path": str(manifest_path)}
            artifact_paths.append(manifest_path)
        except Exception as e:
            summaries["manifest"] = {"enabled": True, "error": str(e)}

    return artifact_paths, summaries


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _serialize_result(result: Any) -> dict[str, Any]:
    """Convert GenerationResult to JSON-serializable dict, excluding sensitive data."""
    if hasattr(result, "model_dump"):
        d = result.model_dump()
    elif hasattr(result, "dict"):
        d = result.dict()
    else:
        d = dict(result)
    # Redact any secret-looking fields
    for k in list(d.keys()):
        if any(s in k.lower() for s in ("password", "secret", "token", "credential")):
            if isinstance(d[k], str) and d[k]:
                d[k] = "***"
    if "quality_report" in d and isinstance(d["quality_report"], dict):
        qr = d["quality_report"]
        for k in list(qr.keys()):
            if any(s in k.lower() for s in ("password", "secret", "token")):
                if isinstance(qr.get(k), str) and qr[k]:
                    qr[k] = "***"
    return d


def run_generate(req: Any) -> dict[str, Any]:
    """Execute generation from API request. Returns serializable result."""
    settings = Settings()
    project_root = _project_root()
    output_dir = project_root / "output" / f"run_{uuid.uuid4().hex[:12]}"
    output_dir.mkdir(parents=True, exist_ok=True)

    schema_obj = None
    rule_set = None
    schema_path = None
    rules_path = None

    if req.pack:
        pack = get_pack(req.pack)
        if not pack:
            return {"success": False, "errors": [f"Unknown pack: {req.pack}"]}
        schema_obj = pack.schema
        rule_set = pack.rule_set
    elif req.schema_path:
        try:
            schema_path = project_root / req.schema_path.lstrip("/")
            if not schema_path.is_absolute():
                schema_path = (project_root / req.schema_path).resolve()
            schema_obj = load_schema(schema_path, project_root=project_root)
            if req.rules_path:
                rules_path = (project_root / req.rules_path).resolve()
                rule_set = load_rule_set(rules_path, project_root=project_root)
        except Exception as e:
            return {"success": False, "errors": [str(e)]}
    elif req.schema_text:
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix="." + (req.schema_format or "sql"), delete=False) as f:
                f.write(req.schema_text)
                schema_path = Path(f.name)
            schema_obj = load_schema(schema_path, project_root=project_root)
        except Exception as e:
            return {"success": False, "errors": [str(e)]}
    else:
        return {"success": False, "errors": ["Provide pack, schema_path, or schema_text"]}

    if schema_obj is None:
        return {"success": False, "errors": ["Failed to load schema"]}
    if rule_set is None:
        from data_forge.models.rules import RuleSet
        rule_set = RuleSet(name="default")

    try:
        gen_mode = GenerationMode(req.mode)
    except ValueError:
        gen_mode = GenerationMode.FULL_SNAPSHOT
    try:
        data_layer = DataLayer(req.layer)
    except ValueError:
        data_layer = DataLayer.BRONZE
    try:
        drift = DriftProfile(req.drift_profile)
    except ValueError:
        drift = DriftProfile.NONE
    try:
        mess = MessinessProfile(req.messiness)
    except ValueError:
        mess = MessinessProfile.CLEAN

    gen_req = GenerationRequest(
        schema_name=req.pack or (schema_obj.name if schema_obj else "custom"),
        rule_set_name=req.rules_path,
        seed=req.seed,
        scale=req.scale,
        include_anomalies=req.include_anomalies,
        anomaly_ratio=req.anomaly_ratio,
        locale=settings.locale,
        mode=gen_mode,
        layer=data_layer,
        batch_id=req.batch_id,
        change_ratio=req.change_ratio,
        drift_profile=drift,
        messiness=mess,
        privacy_mode=req.privacy_mode or "warn",
        load_target=req.load_target,
        db_uri=req.db_uri or (str(output_dir / "data.db") if req.load_target == "sqlite" else None),
        load_params=req.load_params,
        chunk_size=req.chunk_size,
        batch_size=req.batch_size,
        export_format=req.export_format,
    )

    result = run_generation(
        request=gen_req,
        schema_path=schema_path,
        rules_path=rules_path,
        schema=schema_obj,
        rule_set=rule_set,
    )

    if not result.success:
        return {"success": False, "errors": result.errors, "output_dir": str(output_dir), "run_id": output_dir.name}

    try:
        fmt = OutputFormat(req.export_format)
    except ValueError:
        fmt = OutputFormat.PARQUET
    paths = list(export_result(result, output_dir, fmt=fmt, layer=data_layer))

    # Run integrations (dbt, GE, Airflow, contracts, manifest) when requested
    integration_paths: list[Path] = []
    integration_summaries: dict[str, Any] = {}
    try:
        schema_path_resolved = None
        if schema_path and Path(schema_path).exists():
            schema_path_resolved = Path(schema_path)
        extra_paths, integration_summaries = _run_integrations(
            result, output_dir, schema_obj, rule_set, schema_path_resolved, req
        )
        integration_paths = extra_paths
    except Exception as e:
        integration_summaries = {"_error": str(e)}

    out = _serialize_result(result)
    out["output_dir"] = str(output_dir)
    out["run_id"] = output_dir.name
    out["export_paths"] = [str(p) for p in paths] + [str(p) for p in integration_paths]
    out["integration_summaries"] = integration_summaries
    out["success"] = True
    return out
