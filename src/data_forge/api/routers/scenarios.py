"""Scenarios API router."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Body

from data_forge.models.config_schema import CONFIG_SCHEMA_VERSION
from data_forge.services import (
    create_scenario,
    get_scenario,
    list_scenarios,
    update_scenario,
    delete_scenario,
    get_masked_field_names,
    get_run,
    get_scenario_versions,
    get_scenario_version_config,
    diff_scenario_versions,
)
from data_forge.api.task_runner import execute_generation_async
from data_forge.api.routers.runs import _new_run_id
from data_forge.api.routers.benchmark import execute_benchmark_async

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

VALID_CATEGORIES = frozenset({
    "quick_start", "testing", "pipeline_simulation",
    "migration_rehearsal", "warehouse_benchmark", "privacy_uat", "contracts", "custom",
})


def _validate_scenario_payload(payload: dict[str, Any]) -> None:
    """Validate scenario payload. Raises HTTPException on invalid."""
    if not payload:
        raise HTTPException(status_code=400, detail="Empty payload")
    config = payload.get("config")
    if config is None:
        raise HTTPException(status_code=400, detail="config is required")
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="config must be an object")
    name = payload.get("name") or (config.get("name") if isinstance(config, dict) else None)
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    category = payload.get("category") or "custom"
    if category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Use: {sorted(VALID_CATEGORIES)}")


def _normalize_scenario_config(config: dict[str, Any]) -> dict[str, Any]:
    """Ensure config has schema version for export/import round-trip."""
    out = dict(config)
    if "config_schema_version" not in out:
        out["config_schema_version"] = CONFIG_SCHEMA_VERSION
    return out


@router.post("")
def create_scenario_api(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Create a new scenario from config payload."""
    _validate_scenario_payload(payload)
    config = _normalize_scenario_config(payload["config"])
    name = payload.get("name") or config.get("name", "Unnamed")
    description = payload.get("description", "")
    category = payload.get("category") or "custom"
    tags = payload.get("tags") or []
    created_from_run_id = payload.get("created_from_run_id")
    created_from_scenario_id = payload.get("created_from_scenario_id")
    record = create_scenario(
        name=name,
        config=config,
        description=description,
        category=category,
        tags=tags,
        created_from_run_id=created_from_run_id,
        created_from_scenario_id=created_from_scenario_id,
    )
    return record


@router.get("")
def list_scenarios_api(
    category: str | None = None,
    source_pack: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
    cursor: str | None = None,
) -> dict[str, Any]:
    """List scenarios with optional filters. Supports offset/limit and cursor pagination."""
    scenarios = list_scenarios(
        category=category,
        source_pack=source_pack,
        tag=tag,
        search=search,
        limit=limit,
        offset=offset,
        cursor=cursor,
    )
    next_cursor = scenarios[-1]["id"] if scenarios and len(scenarios) == limit else None
    return {
        "scenarios": scenarios,
        "limit": limit,
        "offset": offset,
        "cursor": cursor,
        "next_cursor": next_cursor,
        "has_more": len(scenarios) == limit,
    }


@router.get("/{scenario_id}")
def get_scenario_detail(scenario_id: str) -> dict[str, Any]:
    """Get scenario detail."""
    record = get_scenario(scenario_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scenario not found")
    config = record.get("config") or {}
    masked = get_masked_field_names(config)
    out = dict(record)
    out["has_masked_sensitive_fields"] = bool(masked)
    if masked:
        out["masked_fields"] = masked
    return out


@router.put("/{scenario_id}")
def update_scenario_api(scenario_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Update scenario metadata and/or config."""
    record = get_scenario(scenario_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scenario not found")
    updates = {}
    if "name" in payload:
        name_val = (payload["name"] or "").strip()
        if not name_val:
            raise HTTPException(status_code=400, detail="name cannot be empty")
        updates["name"] = name_val
    if "description" in payload:
        updates["description"] = payload.get("description", "")
    if "category" in payload:
        c = payload["category"]
        if c not in VALID_CATEGORIES:
            raise HTTPException(status_code=400, detail=f"Invalid category. Use: {sorted(VALID_CATEGORIES)}")
        updates["category"] = c
    if "tags" in payload:
        updates["tags"] = payload.get("tags") or []
    if "config" in payload:
        if not isinstance(payload["config"], dict):
            raise HTTPException(status_code=400, detail="config must be an object")
        updates["config"] = _normalize_scenario_config(payload["config"])
    updated = update_scenario(scenario_id, **updates)
    return updated or record


@router.delete("/{scenario_id}")
def delete_scenario_api(scenario_id: str) -> dict[str, Any]:
    """Delete a scenario."""
    deleted = delete_scenario(scenario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"deleted": True, "id": scenario_id}


@router.post("/{scenario_id}/run")
def run_from_scenario(scenario_id: str, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Start a run from a saved scenario."""
    record = get_scenario(scenario_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scenario not found")
    config = record.get("config") or {}
    run_type = "benchmark" if config.get("benchmark", {}).get("enabled") else "generate"
    run_id = _new_run_id()
    pack = config.get("pack")
    from data_forge.api.run_store import create_run
    create_run(run_id, run_type, config, selected_pack=pack, source_scenario_id=scenario_id)
    if run_type == "benchmark":
        background_tasks.add_task(execute_benchmark_async, run_id, config)
    else:
        background_tasks.add_task(execute_generation_async, run_id, config)
    return {"run_id": run_id, "status": "queued"}


@router.post("/from-run/{run_id}")
def create_scenario_from_run(run_id: str, payload: dict[str, Any] = Body(default=None)) -> dict[str, Any]:
    """Create a scenario from an existing run's config."""
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    config = record.get("config") or record.get("config_summary") or {}
    payload = payload or {}
    name = payload.get("name") or f"From run {run_id}"
    description = payload.get("description", "")
    category = payload.get("category") or "custom"
    tags = payload.get("tags") or []
    created = create_scenario(
        name=name,
        config=config,
        description=description,
        category=category,
        tags=tags,
        created_from_run_id=run_id,
    )
    masked = get_masked_field_names(config)
    out = dict(created)
    out["has_masked_sensitive_fields"] = bool(masked)
    if masked:
        out["masked_fields"] = masked
    return out


@router.post("/import")
def import_scenario(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Import a scenario from JSON payload."""
    _validate_scenario_payload(payload)
    config = payload["config"]
    name = payload.get("name") or config.get("name", "Imported")
    description = payload.get("description", "")
    category = payload.get("category") or "custom"
    tags = payload.get("tags") or []
    created = create_scenario(name=name, config=config, description=description, category=category, tags=tags)
    return created


@router.get("/{scenario_id}/versions")
def list_scenario_versions(scenario_id: str) -> dict[str, Any]:
    """List version history for a scenario."""
    record = get_scenario(scenario_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scenario not found")
    versions = get_scenario_versions(scenario_id)
    return {"scenario_id": scenario_id, "versions": versions, "current_version": record.get("version", 1)}


@router.get("/{scenario_id}/versions/{version}")
def get_scenario_version(scenario_id: str, version: str) -> dict[str, Any]:
    """Get config snapshot for a specific version."""
    try:
        version_num = int(version)
    except ValueError:
        raise HTTPException(status_code=400, detail="Version must be an integer") from None
    record = get_scenario(scenario_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scenario not found")
    config = get_scenario_version_config(scenario_id, version_num)
    if config is None:
        raise HTTPException(status_code=404, detail="Version not found")
    versions = get_scenario_versions(scenario_id)
    ver_info = next((v for v in versions if v.get("version") == version_num), {})
    return {"scenario_id": scenario_id, "version": version_num, "config": config, "updated_at": ver_info.get("updated_at")}


@router.get("/{scenario_id}/diff")
def diff_scenario(scenario_id: str, left: int, right: int) -> dict[str, Any]:
    """Compare two scenario versions. Query: ?left=1&right=2."""
    record = get_scenario(scenario_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scenario not found")
    result = diff_scenario_versions(scenario_id, left, right)
    if result is None:
        raise HTTPException(status_code=400, detail="Could not compute diff for the given versions")
    return result


@router.get("/{scenario_id}/export")
def export_scenario(scenario_id: str) -> dict[str, Any]:
    """Export scenario as JSON (for download/import). Includes version info."""
    record = get_scenario(scenario_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scenario not found")
    out = {
        "id": record.get("id"),
        "name": record.get("name"),
        "description": record.get("description"),
        "category": record.get("category"),
        "tags": record.get("tags"),
        "config": record.get("config"),
        "source_pack": record.get("source_pack"),
    }
    if record.get("version") is not None:
        out["version"] = record["version"]
    if record.get("updated_at") is not None:
        out["updated_at"] = record["updated_at"]
    return out
