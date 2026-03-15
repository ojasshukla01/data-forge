"""Lineage: run -> scenario -> version -> pack -> artifacts."""

from typing import Any, cast

from data_forge.services import get_run, get_scenario
from data_forge.config import Settings
from data_forge.api import custom_schema_store


def get_run_lineage(run_id: str) -> dict[str, Any] | None:
    """Return lineage for a run: run, scenario (if any), scenario version, pack, artifact_run_id."""
    record = get_run(run_id)
    if not record:
        return None
    summary = record.get("result_summary") or {}
    scenario_id = record.get("source_scenario_id")
    scenario = None
    scenario_version = None
    if scenario_id:
        scenario = get_scenario(scenario_id)
        if scenario:
            scenario_version = scenario.get("version", 1)
    cfg = record.get("config") or record.get("config_summary") or {}
    pack = record.get("selected_pack") or cfg.get("pack")
    custom_schema_id = cfg.get("custom_schema_id")
    custom_schema_version = cfg.get("custom_schema_version") or (summary.get("custom_schema_version") if summary else None)
    custom_schema_name = summary.get("custom_schema_name") if summary else None
    output_run_id = summary.get("artifact_run_id") or summary.get("output_run_id") or run_id
    schema_missing = False
    if custom_schema_id:
        try:
            if custom_schema_store.get_custom_schema(custom_schema_id) is None:
                schema_missing = True
        except Exception:
            schema_missing = True
    out: dict[str, Any] = {
        "run_id": run_id,
        "run_type": record.get("run_type"),
        "scenario_id": scenario_id,
        "scenario": {"id": scenario_id, "name": scenario.get("name"), "version": scenario_version} if scenario else None,
        "pack": pack,
        "custom_schema_id": custom_schema_id,
        "custom_schema_version": custom_schema_version,
        "custom_schema_name": custom_schema_name,
        "schema_source_type": "custom_schema" if custom_schema_id else "pack",
        "artifact_run_id": output_run_id,
        "output_dir": record.get("output_dir") or summary.get("output_dir"),
    }
    if custom_schema_id:
        out["schema_missing"] = schema_missing
        if summary.get("custom_schema_snapshot_hash") is not None:
            out["custom_schema_snapshot_hash"] = summary["custom_schema_snapshot_hash"]
        if summary.get("custom_schema_table_names") is not None:
            out["custom_schema_table_names"] = summary["custom_schema_table_names"]
    return out


def get_run_manifest_from_disk(run_id: str) -> dict[str, Any] | None:
    """Load manifest.json from output/<artifact_run_id>/ if present."""
    record = get_run(run_id)
    if not record:
        return None
    summary = record.get("result_summary") or {}
    output_run_id = summary.get("artifact_run_id") or summary.get("output_run_id") or run_id
    settings = Settings()
    output_dir = settings.project_root / settings.output_dir / output_run_id
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        import json

        return cast(dict[str, Any], json.loads(manifest_path.read_text(encoding="utf-8")))
    except Exception:
        return None
