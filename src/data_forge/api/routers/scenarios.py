"""Scenarios API router."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Body

from data_forge.api.scenario_store import (
    create_scenario,
    get_scenario,
    list_scenarios,
    update_scenario,
    delete_scenario,
    get_masked_field_names,
)
from data_forge.api.run_store import get_run
from data_forge.api.task_runner import execute_generation_async
from data_forge.api.routers.runs import _new_run_id
from data_forge.api.routers.benchmark import execute_benchmark_async

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])

VALID_CATEGORIES = frozenset({
    "quick_start", "testing", "pipeline_simulation",
    "warehouse_benchmark", "privacy_uat", "contracts", "custom",
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


@router.post("")
def create_scenario_api(payload: dict[str, Any] = Body(...)) -> dict:
    """Create a new scenario from config payload."""
    _validate_scenario_payload(payload)
    config = payload["config"]
    name = payload.get("name") or config.get("name", "Unnamed")
    description = payload.get("description", "")
    category = payload.get("category") or "custom"
    tags = payload.get("tags") or []
    created_from_run_id = payload.get("created_from_run_id")
    record = create_scenario(
        name=name,
        config=config,
        description=description,
        category=category,
        tags=tags,
        created_from_run_id=created_from_run_id,
    )
    return record


@router.get("")
def list_scenarios_api(
    category: str | None = None,
    source_pack: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> dict:
    """List scenarios with optional filters."""
    scenarios = list_scenarios(
        category=category,
        source_pack=source_pack,
        tag=tag,
        search=search,
        limit=limit,
    )
    return {"scenarios": scenarios}


@router.get("/{scenario_id}")
def get_scenario_detail(scenario_id: str) -> dict:
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
def update_scenario_api(scenario_id: str, payload: dict[str, Any] = Body(...)) -> dict:
    """Update scenario metadata and/or config."""
    record = get_scenario(scenario_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scenario not found")
    updates = {}
    if "name" in payload:
        updates["name"] = payload["name"]
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
        updates["config"] = payload["config"]
    updated = update_scenario(scenario_id, **updates)
    return updated or record


@router.delete("/{scenario_id}")
def delete_scenario_api(scenario_id: str) -> dict:
    """Delete a scenario."""
    deleted = delete_scenario(scenario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"deleted": True, "id": scenario_id}


@router.post("/{scenario_id}/run")
def run_from_scenario(scenario_id: str, background_tasks: BackgroundTasks) -> dict:
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
def create_scenario_from_run(run_id: str, payload: dict[str, Any] = Body(default=None)) -> dict:
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
def import_scenario(payload: dict[str, Any] = Body(...)) -> dict:
    """Import a scenario from JSON payload."""
    _validate_scenario_payload(payload)
    config = payload["config"]
    name = payload.get("name") or config.get("name", "Imported")
    description = payload.get("description", "")
    category = payload.get("category") or "custom"
    tags = payload.get("tags") or []
    created = create_scenario(name=name, config=config, description=description, category=category, tags=tags)
    return created


@router.get("/{scenario_id}/export")
def export_scenario(scenario_id: str) -> dict:
    """Export scenario as JSON (for download/import)."""
    record = get_scenario(scenario_id)
    if not record:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {
        "id": record.get("id"),
        "name": record.get("name"),
        "description": record.get("description"),
        "category": record.get("category"),
        "tags": record.get("tags"),
        "config": record.get("config"),
        "source_pack": record.get("source_pack"),
    }
