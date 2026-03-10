"""CLI: generate synthetic data from schema + rules, export, report."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from data_forge import __version__
from data_forge.config import OutputFormat, Settings, SecurityError
from data_forge.models.generation import (
    DataLayer,
    DriftProfile,
    GenerationMode,
    GenerationRequest,
    MessinessProfile,
)
from data_forge.engine import run_generation, export_result
from data_forge.domain_packs import list_packs, get_pack

app = typer.Typer(
    name="data-forge",
    help="Schema-aware synthetic data platform for realistic test data.",
    add_completion=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", "-v", help="Show version"),
):
    if version:
        console.print(f"data-forge {__version__}")
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@app.command()
def generate(
    schema: Path = typer.Option(
        None,
        "--schema",
        "-s",
        path_type=Path,
        help="Path to schema file (.sql or .json)",
    ),
    rules: Path | None = typer.Option(
        None,
        "--rules",
        "-r",
        path_type=Path,
        help="Path to rules YAML",
    ),
    pack: str | None = typer.Option(
        None,
        "--pack",
        "-p",
        help="Use a domain pack (e.g. saas_billing, ecommerce) instead of --schema",
    ),
    seed: int = typer.Option(None, "--seed", help="Random seed for reproducibility"),
    scale: int = typer.Option(None, "--scale", help="Base row count scale"),
    anomalies: bool = typer.Option(False, "--anomalies", help="Inject anomaly rows"),
    anomaly_ratio: float = typer.Option(None, "--anomaly-ratio", help="Fraction of rows to corrupt"),
    output_dir: Path = typer.Option(None, "--output", "-o", path_type=Path, help="Output directory"),
    format: str = typer.Option(None, "--format", "-f", help="Export format: csv, json, jsonl, parquet, sql"),
    locale: str = typer.Option(None, "--locale", help="Locale for Faker"),
    mode: str = typer.Option("full_snapshot", "--mode", "-m", help="Generation mode: full_snapshot, incremental, cdc"),
    layer: str = typer.Option("bronze", "--layer", "-l", help="Data layer: bronze, silver, gold, all"),
    batch_id: str = typer.Option(None, "--batch-id", help="Batch ID for incremental/CDC"),
    change_ratio: float = typer.Option(None, "--change-ratio", help="Fraction of changed rows (incremental/CDC)"),
    drift_profile: str = typer.Option("none", "--drift-profile", help="Schema drift: none, mild, moderate, aggressive"),
    messiness: str = typer.Option("clean", "--messiness", help="Source messiness: clean, realistic, chaotic"),
    write_manifest: Path | None = typer.Option(None, "--write-manifest", help="Write golden manifest after generation"),
    privacy_mode: str = typer.Option(None, "--privacy-mode", help="Privacy: off, warn, strict"),
    contracts: bool = typer.Option(False, "--contracts", help="Also generate OpenAPI contract fixtures when schema is OpenAPI"),
    load: str | None = typer.Option(None, "--load", help="Load into database: sqlite, duckdb, postgres, snowflake, bigquery"),
    db_uri: str | None = typer.Option(None, "--db-uri", help="Database connection string or path"),
    chunk_size: int | None = typer.Option(None, "--chunk-size", help="Generate large tables in chunks (memory-safe)"),
    batch_size: int = typer.Option(1000, "--batch-size", help="Batch size for DB inserts"),
    sf_account: str | None = typer.Option(None, "--sf-account", help="Snowflake account"),
    sf_user: str | None = typer.Option(None, "--sf-user", help="Snowflake user"),
    sf_password: str | None = typer.Option(None, "--sf-password", help="Snowflake password"),
    sf_warehouse: str | None = typer.Option(None, "--sf-warehouse", help="Snowflake warehouse"),
    sf_database: str | None = typer.Option(None, "--sf-database", help="Snowflake database"),
    sf_schema: str | None = typer.Option(None, "--sf-schema", help="Snowflake schema"),
    sf_role: str | None = typer.Option(None, "--sf-role", help="Snowflake role"),
    bq_project: str | None = typer.Option(None, "--bq-project", help="BigQuery project"),
    bq_dataset: str | None = typer.Option(None, "--bq-dataset", help="BigQuery dataset"),
    export_dbt: bool = typer.Option(False, "--export-dbt", help="Export dbt seeds and sources"),
    dbt_dir: Path | None = typer.Option(None, "--dbt-dir", path_type=Path, help="dbt output directory"),
    export_ge: bool = typer.Option(False, "--export-ge", help="Export Great Expectations suites and checkpoint"),
    ge_dir: Path | None = typer.Option(None, "--ge-dir", path_type=Path, help="Great Expectations output directory"),
    export_airflow: bool = typer.Option(False, "--export-airflow", help="Export Airflow DAG templates"),
    airflow_dir: Path | None = typer.Option(None, "--airflow-dir", path_type=Path, help="Airflow output directory"),
    airflow_template: str = typer.Option("generate_only", "--airflow-template", help="DAG template: generate_only|generate_and_load|generate_validate_and_load|benchmark_pipeline"),
):
    """Generate synthetic data and write to output directory."""
    settings = Settings()
    seed = seed if seed is not None else settings.default_seed
    scale = scale if scale is not None else settings.default_scale
    anomaly_ratio = anomaly_ratio if anomaly_ratio is not None else settings.anomaly_ratio
    output_dir = output_dir or settings.project_root / settings.output_dir
    format = format or settings.default_format.value
    locale = locale or settings.locale
    change_ratio = change_ratio if change_ratio is not None else 0.1

    try:
        gen_mode = GenerationMode(mode)
    except ValueError:
        gen_mode = GenerationMode.FULL_SNAPSHOT
    try:
        data_layer = DataLayer(layer)
    except ValueError:
        data_layer = DataLayer.BRONZE
    try:
        drift = DriftProfile(drift_profile)
    except ValueError:
        drift = DriftProfile.NONE
    try:
        mess = MessinessProfile(messiness)
    except ValueError:
        mess = MessinessProfile.CLEAN

    _supported = ("sqlite", "duckdb", "postgres", "postgresql", "snowflake", "bigquery")
    if load and load.lower() not in _supported:
        console.print(f"[red]Unsupported database: {load}. Use: {', '.join(_supported)}[/]")
        raise typer.Exit(1)

    _db_uri = db_uri or ""
    _load_params: dict = {}
    if load:
        if load.lower() == "sqlite":
            _db_uri = _db_uri or str(output_dir / "data.db")
        elif load.lower() == "duckdb":
            _db_uri = _db_uri or str(output_dir / "data.duckdb")
        elif load.lower() in ("postgres", "postgresql") and not _db_uri:
            console.print("[red]Provide --db-uri for postgres (e.g. postgresql://user:pass@localhost:5432/db)[/]")
            raise typer.Exit(1)
        elif load.lower() == "snowflake":
            s = settings
            _load_params = {
                "snowflake_account": sf_account or s.snowflake_account,
                "snowflake_user": sf_user or s.snowflake_user,
                "snowflake_password": sf_password or s.snowflake_password,
                "snowflake_warehouse": sf_warehouse or s.snowflake_warehouse,
                "snowflake_database": sf_database or s.snowflake_database,
                "snowflake_schema": sf_schema or s.snowflake_schema,
                "snowflake_role": sf_role or s.snowflake_role,
            }
        elif load.lower() == "bigquery":
            s = settings
            _load_params = {
                "bigquery_project": bq_project or s.bigquery_project,
                "bigquery_dataset": bq_dataset or s.bigquery_dataset,
            }

    if pack:
        domain = get_pack(pack)
        if not domain:
            console.print(f"[red]Unknown pack: {pack}. Use [bold]data-forge packs[/] to list.[/]")
            raise typer.Exit(1)
        schema_obj = domain.schema
        rule_set = domain.rule_set
        schema_path = rules_path = None
    else:
        if not schema or not schema.exists():
            console.print("[red]Provide --schema PATH or --pack NAME.[/]")
            raise typer.Exit(1)
        schema_obj = None
        rule_set = None
        schema_path = schema
        rules_path = rules if rules and rules.exists() else None

    _privacy = privacy_mode or settings.privacy_mode
    req = GenerationRequest(
        schema_name=pack or (schema.name if schema else "custom"),
        rule_set_name=rules.stem if rules else None,
        seed=seed,
        scale=scale,
        include_anomalies=anomalies,
        anomaly_ratio=anomaly_ratio,
        locale=locale,
        mode=gen_mode,
        layer=data_layer,
        batch_id=batch_id or None,
        change_ratio=change_ratio,
        drift_profile=drift,
        messiness=mess,
        privacy_mode=_privacy,
        load_target=load,
        db_uri=_db_uri,
        load_params=_load_params if _load_params else None,
        chunk_size=chunk_size,
        batch_size=batch_size,
        export_format=format,
    )
    result = run_generation(
        request=req,
        schema_path=schema_path,
        rules_path=rules_path,
        schema=schema_obj,
        rule_set=rule_set,
        verbose=False,
    )
    if not result.success:
        for e in result.errors:
            console.print(f"[red]{e}[/]")
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        fmt = OutputFormat(format)
    except ValueError:
        fmt = OutputFormat.PARQUET
    paths = export_result(result, output_dir, fmt=fmt, layer=data_layer)
    if contracts and schema_path and schema_path.suffix.lower() in (".yaml", ".yml", ".json"):
        try:
            raw = schema_path.read_text(encoding="utf-8")
            if schema_path.suffix.lower() == ".json":
                import json
                data = json.loads(raw)
            else:
                import yaml
                data = yaml.safe_load(raw)
            if isinstance(data, dict) and ("openapi" in data or "swagger" in data):
                from data_forge.contracts.fixtures import generate_contract_fixtures
                settings = Settings()
                contracts_dir = output_dir / "contracts"
                paths = generate_contract_fixtures(schema_path, contracts_dir, seed=seed)
                console.print(f"[green]Contract fixtures: {len(paths)} file(s) to {contracts_dir}[/]")
        except Exception as e:
            console.print(f"[yellow]Contract generation skipped: {e}[/]")
    if export_dbt:
        from data_forge.dbt_export import export_dbt as do_export_dbt
        dbt_out = dbt_dir or (output_dir / "dbt")
        table_data = {t.table_name: t.rows for t in result.tables}
        s_for_dbt = schema_obj
        if s_for_dbt is None and schema_path and schema_path.exists():
            try:
                from data_forge.schema_ingest import load_schema
                s_for_dbt = load_schema(schema_path)
            except Exception:
                s_for_dbt = None
        dbt_report = do_export_dbt(table_data, s_for_dbt, dbt_out)
        result.quality_report["dbt_export"] = dbt_report
        console.print(f"[green]dbt export: {len(dbt_report.get('seeds_generated', []))} seeds, {dbt_report.get('sources_file', '')}[/]")
    if export_ge:
        from data_forge.ge_export import export_ge
        s_for_ge = schema_obj
        if s_for_ge is None and schema_path and schema_path.exists():
            try:
                from data_forge.schema_ingest import load_schema
                s_for_ge = load_schema(schema_path)
            except Exception:
                s_for_ge = None
        if s_for_ge:
            ge_out = ge_dir or (output_dir / "great_expectations")
            ge_report = export_ge(s_for_ge, rule_set, ge_out)
            result.quality_report["ge_export"] = ge_report
            console.print(f"[green]GE export: {ge_report['suites_generated']} suite(s) to {ge_out}[/]")
        else:
            console.print("[yellow]GE export skipped: no schema available[/]")
    if export_airflow:
        from data_forge.airflow_export import export_airflow
        tpl = airflow_template if airflow_template in ("generate_only", "generate_and_load", "generate_validate_and_load", "benchmark_pipeline") else "generate_only"
        af_out = airflow_dir or (output_dir / "airflow")
        af_report = export_airflow(tpl, af_out)
        result.quality_report["airflow_export"] = af_report
        console.print(f"[green]Airflow export: {af_report['files_generated']} DAG(s) to {af_out}[/]")
    if write_manifest:
        from data_forge.golden import create_manifest, schema_signature, write_manifest as write_manifest_file
        from data_forge.schema_ingest import load_schema as load_schema_for_manifest

        schema_sig = ""
        s_for_sig = schema_obj
        if s_for_sig is None and schema_path:
            try:
                s_for_sig = load_schema_for_manifest(schema_path)
            except Exception:
                pass
        if s_for_sig:
            schema_sig = schema_signature(s_for_sig)
        row_counts = {t.table_name: t.row_count for t in result.tables}
        manifest = create_manifest(
            seed=seed,
            mode=gen_mode.value,
            layer=data_layer.value,
            row_counts=row_counts,
            schema_sig=schema_sig,
        )
        write_manifest_file(manifest, write_manifest)
        console.print(f"[green]Manifest written to {write_manifest}[/]")
    console.print(f"[green]Generated {sum(t.row_count for t in result.tables)} rows across {len(result.tables)} tables.[/]")
    console.print(f"[green]Wrote {len(paths)} file(s) to {output_dir.absolute()}.[/]")
    if result.quality_report:
        q = result.quality_report
        console.print(f"  Referential integrity: {'OK' if q.get('referential_integrity') else 'FAIL'}")
        rv = q.get("rule_violations", {})
        total_v = rv.get("total", 0)
        console.print(f"  Rule violations: {total_v}")
        if q.get("schema_drift"):
            console.print(f"  Schema drift events: {q['schema_drift'].get('total', 0)}")
        if q.get("privacy_audit"):
            pa = q["privacy_audit"]
            console.print(f"  Privacy: {pa.get('mode', 'off')} | sensitive columns: {pa.get('sensitive_columns_detected', 0)}")
        if q.get("warehouse_load"):
            wl = q["warehouse_load"]
            status = "[green]OK[/]" if wl.get("success") else "[red]FAIL[/]"
            console.print(f"  Database load ({wl.get('target', '?')}): {status} | tables: {wl.get('tables_loaded', 0)}")
        if q.get("warehouse_validation"):
            wv = q["warehouse_validation"]
            console.print(f"  Warehouse validation: {'OK' if wv.get('checks_passed') else 'FAIL'}")
        console.print(f"  Duration: {result.duration_seconds}s")


@app.command()
def packs():
    """List available domain packs."""
    table = Table(title="Domain packs")
    table.add_column("Pack", style="cyan")
    table.add_column("Description", style="white")
    for pack_id, desc in list_packs():
        table.add_row(pack_id, desc)
    console.print(table)
    console.print("\nUse: [bold]data-forge generate --pack <pack>[/]")


@app.command()
def validate(
    schema: Path = typer.Argument(..., path_type=Path, help="Schema file"),
    data_dir: Path | None = typer.Option(None, "--data", "-d", path_type=Path, help="Dataset directory to validate"),
    rules: Path | None = typer.Option(None, "--rules", "-r", path_type=Path, help="Rules YAML for rule validation"),
    privacy_mode: str = typer.Option("off", "--privacy-mode", help="Privacy: off, warn, strict"),
):
    """Validate a schema file (and optionally generated data)."""
    from data_forge.schema_ingest import load_schema
    from data_forge.rule_engine import load_rule_set
    from data_forge.validators.quality import (
        load_dataset_from_dir,
        compute_quality_report,
    )

    if not schema.exists():
        console.print(f"[red]Not found: {schema}[/]")
        raise typer.Exit(1)
    try:
        s = load_schema(schema)
    except SecurityError as e:
        console.print(f"[red]Security: {e}[/]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(1) from e

    console.print(f"[green]Schema loaded: {s.name}, {len(s.tables)} tables, {len(s.relationships)} relationships.[/]")
    for t in s.tables:
        console.print(f"  - {t.name}: {len(t.columns)} columns")

    if data_dir and data_dir.exists():
        table_data = load_dataset_from_dir(data_dir)
        if not table_data:
            console.print("[yellow]No CSV/JSON/JSONL/Parquet files found in dataset directory.[/]")
        else:
            console.print(f"\n[bold]Dataset validation[/] ({len(table_data)} tables loaded)")
            rule_set = None
            if rules and rules.exists():
                try:
                    rule_set = load_rule_set(rules)
                except SecurityError as e:
                    console.print(f"[yellow]Rules: Security - {e}[/]")
                except Exception as e:
                    console.print(f"[yellow]Rules: {e}[/]")
            from data_forge.pii.classifier import classify_schema
            from data_forge.pii.redaction import RedactionConfig
            pii_result = classify_schema(s)
            redaction_cfg = RedactionConfig(enabled=privacy_mode in ("warn", "strict"))
            report = compute_quality_report(
                s, table_data, rule_set=rule_set,
                pii_detection=pii_result.pii_detection,
                privacy_mode=privacy_mode,
                redaction_config=redaction_cfg,
                privacy_warnings=pii_result.warnings if privacy_mode != "off" else None,
            )
            ref_ok = report.get("referential_integrity", True)
            console.print(f"  Referential integrity: {'[green]OK[/]' if ref_ok else '[red]FAIL[/]'}")
            if report.get("referential_errors"):
                for err in report["referential_errors"][:5]:
                    console.print(f"    [red]{err}[/]")
                if len(report["referential_errors"]) > 5:
                    console.print(f"    ... and {len(report['referential_errors']) - 5} more")
            rv = report.get("rule_violations", {})
            total_v = rv.get("total", 0)
            console.print(f"  Rule violations: {total_v}")
            if total_v > 0 and "by_rule" in rv:
                for rule_name, count in rv["by_rule"].items():
                    console.print(f"    - {rule_name}: {count}")
            if report.get("privacy_audit") and privacy_mode != "off":
                pa = report["privacy_audit"]
                console.print(f"  Privacy: {pa.get('mode')} | sensitive: {pa.get('sensitive_columns_detected', 0)}")


@app.command()
def validate_golden(
    manifest: Path = typer.Option(..., "--manifest", "-m", path_type=Path, help="Path to manifest.json"),
    data: Path = typer.Option(..., "--data", "-d", path_type=Path, help="Path to output directory"),
    schema: Path | None = typer.Option(None, "--schema", "-s", path_type=Path),
):
    """Validate generated output against a golden manifest."""
    from data_forge.golden import load_manifest, validate_against_manifest, schema_signature
    from data_forge.schema_ingest import load_schema

    if not manifest.exists():
        console.print(f"[red]Manifest not found: {manifest}[/]")
        raise typer.Exit(1)
    if not data.exists() or not data.is_dir():
        console.print(f"[red]Data directory not found: {data}[/]")
        raise typer.Exit(1)

    m = load_manifest(manifest)
    schema_sig = None
    if schema and schema.exists():
        try:
            s = load_schema(schema)
            schema_sig = schema_signature(s)
        except Exception:
            pass

    ok, errors = validate_against_manifest(data, m, schema_sig)
    if ok:
        console.print("[green]Validation passed: output matches manifest.[/]")
    else:
        console.print("[red]Validation failed:[/]")
        for e in errors:
            console.print(f"  - {e}")
        raise typer.Exit(1)


@app.command()
def generate_contracts(
    schema: Path = typer.Option(..., "--schema", "-s", path_type=Path, help="OpenAPI schema file (yaml/json)"),
    output: Path = typer.Option(None, "--output", "-o", path_type=Path, help="Output directory for fixtures"),
    seed: int = typer.Option(42, "--seed", help="Random seed"),
):
    """Generate API contract fixtures from OpenAPI schema."""
    from data_forge.contracts.fixtures import generate_contract_fixtures
    from data_forge.config import Settings

    if not schema.exists():
        console.print(f"[red]Schema not found: {schema}[/]")
        raise typer.Exit(1)
    settings = Settings()
    out = output or (settings.project_root / settings.contracts_dir)
    paths = generate_contract_fixtures(schema, out, seed=seed)
    console.print(f"[green]Generated {len(paths)} fixture(s) to {out.absolute()}[/]")


@app.command()
def validate_contracts(
    schema: Path = typer.Option(..., "--schema", "-s", path_type=Path, help="OpenAPI schema file"),
    data: Path = typer.Option(..., "--data", "-d", path_type=Path, help="Directory containing fixture files"),
):
    """Validate contract fixtures against OpenAPI schema."""
    from data_forge.contracts.validate import validate_contract_fixtures

    if not schema.exists():
        console.print(f"[red]Schema not found: {schema}[/]")
        raise typer.Exit(1)
    if not data.is_dir():
        console.print(f"[red]Data directory not found: {data}[/]")
        raise typer.Exit(1)
    report = validate_contract_fixtures(schema, data)
    total = report.get("total", 0)
    passed = report.get("passed", 0)
    failed = report.get("failed", 0)
    failures = report.get("failures", [])
    if failed == 0 and total > 0:
        console.print(f"[green]All {passed} fixture(s) passed validation.[/]")
    elif total == 0:
        console.print("[yellow]No fixtures found to validate.[/]")
    else:
        console.print(f"[red]{failed} of {total} fixture(s) failed.[/]")
        for f in failures[:10]:
            console.print(f"  - {f.get('fixture', '?')}: {f.get('reason', '')}")
        raise typer.Exit(1)


@app.command()
def create_manifest_cmd(
    manifest_path: Path = typer.Option(..., "--output", "-o", path_type=Path, help="Output manifest path"),
    seed: int = typer.Option(42, "--seed"),
    mode: str = typer.Option("full_snapshot", "--mode"),
    layer: str = typer.Option("bronze", "--layer"),
    schema: Path | None = typer.Option(None, "--schema"),
    row_counts: str | None = typer.Option(None, "--row-counts", help="JSON dict of table->count"),
):
    """Create a golden manifest from current generation (run generate first, then capture)."""
    from data_forge.golden import create_manifest, schema_signature, write_manifest
    from data_forge.schema_ingest import load_schema

    schema_sig = ""
    if schema and schema.exists():
        s = load_schema(schema)
        schema_sig = schema_signature(s)

    counts: dict[str, int] = {}
    if row_counts:
        import json
        counts = json.loads(row_counts)

    manifest = create_manifest(seed=seed, mode=mode, layer=layer, row_counts=counts, schema_sig=schema_sig)
    write_manifest(manifest, manifest_path)
    console.print(f"[green]Manifest written to {manifest_path}[/]")


@app.command("validate-ge")
def validate_ge(
    expectations: Path = typer.Option(..., "--expectations", "-e", path_type=Path, help="Path to GE expectations dir"),
    data: Path = typer.Option(..., "--data", "-d", path_type=Path, help="Path to data directory"),
):
    """Validate data against Great Expectations expectation suites."""
    from data_forge.ge_validation import validate_against_expectations

    if not expectations.exists() or not expectations.is_dir():
        console.print(f"[red]Expectations directory not found: {expectations}[/]")
        raise typer.Exit(1)
    if not data.exists() or not data.is_dir():
        console.print(f"[red]Data directory not found: {data}[/]")
        raise typer.Exit(1)
    exp_dir = expectations / "expectations" if (expectations / "expectations").exists() else expectations
    report = validate_against_expectations(exp_dir, data)
    ge = report.get("ge_validation", {})
    passed = ge.get("passed", 0)
    failed = ge.get("failed", 0)
    if failed == 0:
        console.print(f"[green]All {passed} suite(s) passed.[/]")
    else:
        console.print(f"[red]{failed} of {passed + failed} suite(s) failed.[/]")
        for f in ge.get("failures", [])[:10]:
            console.print(f"  - {f.get('suite')}: {f.get('expectation')} - {f.get('reason')}")
        raise typer.Exit(1)


@app.command()
def reconcile(
    manifest: Path = typer.Option(..., "--manifest", "-m", path_type=Path, help="Path to manifest.json"),
    data: Path = typer.Option(..., "--data", "-d", path_type=Path, help="Path to data directory"),
    schema: Path | None = typer.Option(None, "--schema", "-s", path_type=Path, help="Schema for column/PK checks"),
):
    """Reconcile manifest expected row counts vs actual data."""
    from data_forge.reconciliation import run_reconciliation

    if not manifest.exists():
        console.print(f"[red]Manifest not found: {manifest}[/]")
        raise typer.Exit(1)
    if not data.exists() or not data.is_dir():
        console.print(f"[red]Data directory not found: {data}[/]")
        raise typer.Exit(1)
    schema_obj = None
    if schema and schema.exists():
        try:
            from data_forge.schema_ingest import load_schema
            schema_obj = load_schema(schema)
        except Exception:
            pass
    report = run_reconciliation(manifest, data, schema=schema_obj)
    rec = report.get("reconciliation", {})
    diffs = rec.get("row_count_diffs", {})
    missing = rec.get("missing_tables", [])
    if not diffs and not missing:
        console.print("[green]Reconciliation passed: row counts match.[/]")
    else:
        if missing:
            console.print(f"[yellow]Missing tables: {missing}[/]")
        for table, d in diffs.items():
            console.print(f"[yellow]{table}: expected {d.get('expected')}, actual {d.get('actual')}[/]")
        raise typer.Exit(1)


@app.command()
def benchmark(
    schema: Path | None = typer.Option(None, "--schema", "-s", path_type=Path, help="Path to schema file"),
    rules: Path | None = typer.Option(None, "--rules", "-r", path_type=Path, help="Path to rules YAML"),
    pack: str | None = typer.Option(None, "--pack", "-p", help="Use domain pack instead of schema"),
    scale: int = typer.Option(1000, "--scale", help="Base row count scale"),
    layer: str = typer.Option("bronze", "--layer", "-l", help="Data layer"),
    mode: str = typer.Option("full_snapshot", "--mode", "-m", help="Generation mode"),
    format: str = typer.Option("parquet", "--format", "-f", help="Export format"),
    chunk_size: int | None = typer.Option(None, "--chunk-size", help="Chunk size for generation"),
    load: str | None = typer.Option(None, "--load", help="Load target: sqlite, duckdb, postgres, etc."),
    db_uri: str | None = typer.Option(None, "--db-uri", help="Database URI or path"),
    iterations: int = typer.Option(1, "--iterations", help="Number of benchmark iterations"),
    output_json: Path | None = typer.Option(None, "--output-json", help="Write benchmark results to JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose structured logging"),
):
    """Run a controlled generation benchmark and output performance metrics."""
    import json
    import tempfile
    from data_forge.domain_packs import get_pack
    from data_forge.performance import estimate_peak_memory_mb

    settings = Settings()
    try:
        data_layer = DataLayer(layer)
    except ValueError:
        data_layer = DataLayer.BRONZE
    try:
        gen_mode = GenerationMode(mode)
    except ValueError:
        gen_mode = GenerationMode.FULL_SNAPSHOT

    schema_obj = None
    rule_set = None
    schema_path = None
    rules_path = rules if rules and rules.exists() else None

    if pack:
        domain = get_pack(pack)
        if not domain:
            console.print(f"[red]Unknown pack: {pack}[/]")
            raise typer.Exit(1)
        schema_obj = domain.schema
        rule_set = domain.rule_set
    else:
        if not schema or not schema.exists():
            console.print("[red]Provide --schema PATH or --pack NAME.[/]")
            raise typer.Exit(1)
        schema_path = schema

    _supported = ("sqlite", "duckdb", "postgres", "postgresql", "snowflake", "bigquery")
    if load and load.lower() not in _supported:
        console.print(f"[red]Unsupported load target: {load}[/]")
        raise typer.Exit(1)

    output_dir = Path(tempfile.mkdtemp(prefix="data-forge-bench-"))
    _db_uri = db_uri or ""
    _load_params: dict = {}
    if load:
        if load.lower() == "sqlite":
            _db_uri = _db_uri or str(output_dir / "bench.db")
        elif load.lower() == "duckdb":
            _db_uri = _db_uri or str(output_dir / "bench.duckdb")

    req = GenerationRequest(
        schema_name=pack or (schema.name if schema else "custom"),
        rule_set_name=rules.stem if rules else None,
        seed=42,
        scale=scale,
        include_anomalies=False,
        anomaly_ratio=0.0,
        locale=settings.locale,
        mode=gen_mode,
        layer=data_layer,
        change_ratio=0.1,
        drift_profile=DriftProfile.NONE,
        messiness=MessinessProfile.CLEAN,
        privacy_mode="off",
        load_target=load,
        db_uri=_db_uri,
        load_params=_load_params if _load_params else None,
        chunk_size=chunk_size,
        batch_size=1000,
        export_format=format,
    )

    timings_out: dict[str, float] = {}
    results_list: list[dict] = []
    total_rows = 0
    gen_secs: list[float] = []
    exp_secs: list[float] = []
    load_secs: list[float] = []

    result_first = None
    for i in range(iterations):
        timings_out.clear()
        result = run_generation(
            request=req,
            schema_path=schema_path,
            rules_path=rules_path,
            schema=schema_obj,
            rule_set=rule_set,
            verbose=verbose,
            timings_out=timings_out,
        )
        if result_first is None:
            result_first = result
        if not result.success:
            console.print(f"[red]Iteration {i+1} failed: {result.errors}[/]")
            raise typer.Exit(1)
        total_rows = sum(t.row_count for t in result.tables)
        gen_secs.append(timings_out.get("generation_seconds", 0))
        try:
            fmt_enum = OutputFormat(format)
        except ValueError:
            fmt_enum = OutputFormat.PARQUET
        export_result(
            result, output_dir / str(i), fmt=fmt_enum, layer=data_layer, timings_out=timings_out
        )
        exp_secs.append(timings_out.get("export_seconds", 0))
        ld = timings_out.get("warehouse_load_seconds")
        if ld is not None:
            load_secs.append(ld)
        results_list.append({
            "iter": i + 1,
            "rows": total_rows,
            "generation_seconds": gen_secs[-1],
            "export_seconds": exp_secs[-1],
            "load_seconds": timings_out.get("warehouse_load_seconds"),
        })

    gen_avg = sum(gen_secs) / len(gen_secs) if gen_secs else 0
    exp_avg = sum(exp_secs) / len(exp_secs) if exp_secs else 0
    load_avg = sum(load_secs) / len(load_secs) if load_secs else None

    benchmark_results = {
        "iterations": iterations,
        "total_rows_generated": total_rows,
        "generation_seconds": round(gen_avg, 2),
        "export_seconds": round(exp_avg, 2) if format else None,
        "load_seconds": round(load_avg, 2) if load_avg is not None else None,
        "rows_per_second_generation": round(total_rows / gen_avg, 2) if gen_avg > 0 else 0,
        "rows_per_second_export": round(total_rows / exp_avg, 2) if exp_avg > 0 else None,
        "rows_per_second_load": round(total_rows / load_avg, 2) if load_avg and load_avg > 0 else None,
        "peak_memory_mb_estimate": round(estimate_peak_memory_mb(total_rows), 1),
    }

    perf_warnings = result_first.performance_warnings if result_first and result_first.success else []

    out = {
        "benchmark_results": benchmark_results,
        "timings": dict(timings_out),
        "performance_warnings": perf_warnings,
    }

    try:
        import shutil
        shutil.rmtree(output_dir, ignore_errors=True)
    except Exception:
        pass

    console.print(json.dumps({"benchmark_results": benchmark_results}, indent=2))
    if output_json:
        output_json.write_text(json.dumps(out, indent=2), encoding="utf-8")
        console.print(f"[green]Full results written to {output_json}[/]")


# ---- Runs / retention (API run store) ----

runs_app = typer.Typer(help="Run metadata, retention, and storage (API run store).")


@runs_app.command("storage")
def runs_storage():
    """Print storage usage summary (runs count, artifact size)."""
    from data_forge.services.retention_service import get_storage_usage
    u = get_storage_usage()
    console.print(f"Runs: {u['runs_count']}  Artifacts: {u['artifact_count']}  Total: {u['total_size_mb']} MB")
    if u.get("by_run"):
        table = Table(title="By run (first 20)")
        table.add_column("Run ID", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Status", style="white")
        table.add_column("Size (MB)", style="green")
        table.add_column("Pinned", style="yellow")
        for r in u["by_run"][:20]:
            table.add_row(
                r.get("run_id", ""),
                r.get("run_type", ""),
                r.get("status", ""),
                str(round((r.get("size_bytes") or 0) / (1024 * 1024), 2)),
                "yes" if r.get("pinned") else "no",
            )
        console.print(table)


@runs_app.command("cleanup-preview")
def runs_cleanup_preview(
    retention_count: int | None = typer.Option(None, "--count", "-n", help="Keep last N runs"),
    retention_days: float | None = typer.Option(None, "--days", "-d", help="Prune older than N days"),
):
    """Dry-run: show runs that would be removed by cleanup."""
    from data_forge.services.retention_service import preview_cleanup
    out = preview_cleanup(retention_count=retention_count, retention_days=retention_days)
    candidates = out.get("candidates", [])
    policy = out.get("policy", {})
    console.print(f"Policy: keep last {policy.get('retention_count')} runs, max age {policy.get('retention_days')} days")
    console.print(f"Candidates for removal: {len(candidates)}")
    if candidates:
        table = Table(title="Would remove")
        table.add_column("Run ID", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Status", style="white")
        table.add_column("Age (days)", style="yellow")
        for c in candidates[:30]:
            table.add_row(
                c.get("run_id", ""),
                c.get("run_type", ""),
                c.get("status", ""),
                str(round(c.get("age_days", 0), 1)),
            )
        console.print(table)


@runs_app.command("cleanup-execute")
def runs_cleanup_execute(
    retention_count: int | None = typer.Option(None, "--count", "-n", help="Keep last N runs"),
    retention_days: float | None = typer.Option(None, "--days", "-d", help="Prune older than N days"),
    delete_artifacts: bool = typer.Option(False, "--delete-artifacts", help="Also remove output dirs for pruned runs"),
):
    """Execute retention cleanup (remove run records; optionally artifact dirs)."""
    from data_forge.services.retention_service import execute_cleanup
    result = execute_cleanup(
        delete_artifacts=delete_artifacts,
        retention_count=retention_count,
        retention_days=retention_days,
    )
    console.print(f"Deleted run records: {result.get('deleted_run_records', 0)}")
    if result.get("deleted_artifact_dirs"):
        console.print(f"Deleted artifact dirs: {result['deleted_artifact_dirs']}")


@runs_app.command("archive")
def runs_archive(run_id: str = typer.Argument(..., help="Run ID to archive")):
    """Archive a run (hide from default list)."""
    from data_forge.services.retention_service import archive_run
    r = archive_run(run_id)
    if not r:
        console.print(f"[red]Run not found: {run_id}[/]")
        raise typer.Exit(1)
    console.print(f"[green]Archived {run_id}[/]")


@runs_app.command("unarchive")
def runs_unarchive(run_id: str = typer.Argument(..., help="Run ID to unarchive")):
    """Unarchive a run."""
    from data_forge.services.retention_service import unarchive_run
    r = unarchive_run(run_id)
    if not r:
        console.print(f"[red]Run not found: {run_id}[/]")
        raise typer.Exit(1)
    console.print(f"[green]Unarchived {run_id}[/]")


@runs_app.command("delete")
def runs_delete(
    run_id: str = typer.Argument(..., help="Run ID to delete"),
    delete_artifacts: bool = typer.Option(False, "--delete-artifacts", help="Also remove output dir"),
):
    """Permanently delete a run record (and optionally its output dir)."""
    from data_forge.services.retention_service import delete_run
    ok = delete_run(run_id, delete_artifacts=delete_artifacts)
    if not ok:
        console.print(f"[red]Run not found: {run_id}[/]")
        raise typer.Exit(1)
    console.print(f"[green]Deleted {run_id}[/]")


@runs_app.command("pin")
def runs_pin(run_id: str = typer.Argument(..., help="Run ID to pin")):
    """Pin a run (exclude from retention cleanup)."""
    from data_forge.services.retention_service import pin_run
    r = pin_run(run_id)
    if not r:
        console.print(f"[red]Run not found: {run_id}[/]")
        raise typer.Exit(1)
    console.print(f"[green]Pinned {run_id}[/]")


@runs_app.command("unpin")
def runs_unpin(run_id: str = typer.Argument(..., help="Run ID to unpin")):
    """Unpin a run."""
    from data_forge.services.retention_service import unpin_run
    r = unpin_run(run_id)
    if not r:
        console.print(f"[red]Run not found: {run_id}[/]")
        raise typer.Exit(1)
    console.print(f"[green]Unpinned {run_id}[/]")


app.add_typer(runs_app, name="runs")


@app.command("scaffold-pack")
def scaffold_pack(
    name: str = typer.Argument(..., help="Pack id (e.g. my_domain, use underscores)"),
    output_dir: Path | None = typer.Option(None, "--output", "-o", path_type=Path, help="Root directory (default: project root)"),
):
    """Generate a new domain pack template: schema, rules, sample scenario, and docs."""
    from data_forge.config import Settings
    settings = Settings()
    root = Path(output_dir) if output_dir else settings.project_root
    safe = name.strip().lower().replace("-", "_")
    schemas_dir = root / "schemas"
    rules_dir = root / "rules"
    examples_dir = root / "examples" / "scenarios"
    docs_dir = root / "docs"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    rules_dir.mkdir(parents=True, exist_ok=True)
    examples_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    schema_sql = f"""-- Domain pack: {safe}
-- Add your table definitions (DDL) here. Example:

CREATE TABLE entities (
    id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add more tables and relationships as needed.
"""
    (schemas_dir / f"{safe}.sql").write_text(schema_sql, encoding="utf-8")

    rules_yml = f"""# Rules for pack: {safe}
name: {safe}
description: Validation and generation rules for {safe}

rules: []
# Add rules: uniqueness, ranges, referential, etc.
"""
    (rules_dir / f"{safe}.yaml").write_text(rules_yml, encoding="utf-8")

    scenario_json = {
        "name": f"{safe.replace('_', ' ').title()} quick start",
        "description": f"Quick start scenario for {safe} pack",
        "category": "quick_start",
        "tags": [safe, "demo"],
        "config": {
            "pack": safe,
            "scale": 1000,
            "mode": "full_snapshot",
            "layer": "bronze",
            "config_schema_version": 1,
        },
    }
    import json
    (examples_dir / f"{safe}_quick_start.json").write_text(json.dumps(scenario_json, indent=2), encoding="utf-8")

    readme = f"""# Pack: {safe}

## Schema

- `schemas/{safe}.sql` — table definitions.

## Rules

- `rules/{safe}.yaml` — validation/generation rules.

## Register the pack

1. Add to `src/data_forge/domain_packs/__init__.py` in `list_packs()`:
   `("{safe}", "Your description"),`
2. Add to `PACK_METADATA` dict with name, category, key_entities, etc.
3. Run: `data-forge generate --pack {safe} --scale 100` to test.
"""
    (docs_dir / f"pack_{safe}.md").write_text(readme, encoding="utf-8")

    console.print(f"[green]Scaffolded pack [bold]{safe}[/] at {root}[/]")
    console.print(f"  schemas/{safe}.sql")
    console.print(f"  rules/{safe}.yaml")
    console.print(f"  examples/scenarios/{safe}_quick_start.json")
    console.print(f"  docs/pack_{safe}.md")
    console.print("[yellow]Next: register the pack in src/data_forge/domain_packs/__init__.py (list_packs and PACK_METADATA).[/]")


if __name__ == "__main__":
    app()
