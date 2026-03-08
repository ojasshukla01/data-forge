"""Preflight validation API router."""

from fastapi import APIRouter

from data_forge.domain_packs import get_pack
from data_forge.performance import estimate_peak_memory_mb, collect_performance_warnings

router = APIRouter(prefix="/api", tags=["preflight"])


def _estimate_rows(scale: int, pack_id: str | None) -> int:
    """Rough row count estimate for a pack at given scale."""
    pack = get_pack(pack_id or "") if pack_id else None
    if not pack:
        return scale * 5  # fallback
    n_tables = len(pack.schema.tables)
    base = scale
    line_items = sum(1 for t in pack.schema.tables if "line" in t.name or "item" in t.name or "detail" in t.name)
    return base * n_tables + scale * 2 * line_items


@router.post("/preflight")
def api_preflight(config: dict) -> dict:
    """
    Validate pending run config. Returns blockers, warnings, recommendations,
    estimated rows, memory, and artifact summary.
    """
    blockers: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []
    artifacts: list[str] = []
    integrations: list[str] = []

    pack = config.get("pack")
    scale = int(config.get("scale", 1000) or 1000)
    mode = config.get("mode", "full_snapshot")
    layer = config.get("layer", "bronze")
    export_format = config.get("export_format", "parquet")
    load_target = config.get("load_target")
    export_ge = config.get("export_ge", False)
    export_airflow = config.get("export_airflow", False)
    export_dbt = config.get("export_dbt", False)
    contracts = config.get("contracts", False)
    chunk_size = config.get("chunk_size")

    # Input validity
    if not pack and not config.get("schema_path") and not config.get("schema_text"):
        blockers.append("Provide a domain pack or schema.")
    elif pack:
        p = get_pack(pack)
        if not p:
            blockers.append(f"Domain pack '{pack}' not found.")

    # Mode/layer validity
    valid_modes = ("full_snapshot", "incremental", "cdc")
    if mode not in valid_modes:
        blockers.append(f"Invalid mode '{mode}'. Use: {', '.join(valid_modes)}")
    valid_layers = ("bronze", "silver", "gold", "all")
    if layer not in valid_layers:
        blockers.append(f"Invalid layer '{layer}'. Use: {', '.join(valid_layers)}")

    # Warehouse config
    if load_target:
        integrations.append(f"Load to {load_target}")
        if load_target.lower() in ("postgres", "postgresql") and not config.get("db_uri"):
            blockers.append("PostgreSQL requires --db-uri")
        if load_target.lower() == "snowflake":
            if not config.get("load_params", {}).get("snowflake_account"):
                warnings.append("Snowflake: ensure account/user/warehouse/database are configured")
        if load_target.lower() == "bigquery":
            if not config.get("load_params", {}).get("bigquery_project"):
                warnings.append("BigQuery: ensure project/dataset are configured")

    # Contracts
    if contracts:
        recommendations.append("Contracts require OpenAPI schema. Ensure schema is OpenAPI-compatible.")

    # Performance
    est_rows = _estimate_rows(scale, pack)
    est_mem = round(estimate_peak_memory_mb(est_rows), 1)
    perf_warnings = collect_performance_warnings(scale, chunk_size, export_format)
    warnings.extend(perf_warnings)

    if scale >= 50000 and not chunk_size:
        recommendations.append("Consider --chunk-size 10000 for scale >= 50k")

    # Artifacts
    artifacts.append(f"Data export ({export_format})")
    if export_ge:
        artifacts.append("Great Expectations suites")
        integrations.append("GE export")
    if export_airflow:
        artifacts.append("Airflow DAG templates")
        integrations.append("Airflow export")
    if export_dbt:
        artifacts.append("dbt seeds")
        integrations.append("dbt export")
    if contracts:
        artifacts.append("Contract fixtures")
        integrations.append("Contract generation")

    valid = len(blockers) == 0

    return {
        "valid": valid,
        "blockers": blockers,
        "warnings": warnings,
        "recommendations": recommendations,
        "estimated_rows": est_rows,
        "estimated_memory_mb": est_mem,
        "artifacts_to_generate": artifacts,
        "integrations_to_run": integrations,
        "config_summary": {
            "pack": pack,
            "scale": scale,
            "mode": mode,
            "layer": layer,
            "export_format": export_format,
            "load_target": load_target,
        },
    }
