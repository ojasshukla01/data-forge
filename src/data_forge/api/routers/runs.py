"""Runs API router."""

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from data_forge.api.run_store import create_run, get_run, list_runs, run_cleanup
from data_forge.api.task_runner import execute_generation_async
from data_forge.api.routers.benchmark import execute_benchmark_async

router = APIRouter(prefix="/api/runs", tags=["runs"])


def _new_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:12]}"


@router.post("/benchmark")
def start_benchmark(config: dict[str, Any], background_tasks: BackgroundTasks) -> dict:
    """
    Start async benchmark run. Returns run_id immediately.
    Run appears in runs list with run_type=benchmark.
    Body: { pack?, scale?, format?, iterations? }
    """
    run_id = _new_run_id()
    pack = config.get("pack") or "saas_billing"
    create_run(run_id, "benchmark", config, selected_pack=pack)
    background_tasks.add_task(execute_benchmark_async, run_id, config)
    return {"run_id": run_id, "status": "queued"}


@router.post("/generate")
def start_generate(config: dict[str, Any], background_tasks: BackgroundTasks) -> dict:
    """
    Start async generation. Returns run_id immediately.
    Run status is polled via GET /api/runs/{id}.
    """
    run_id = _new_run_id()
    pack = config.get("pack")
    create_run(run_id, "generate", config, selected_pack=pack)
    background_tasks.add_task(execute_generation_async, run_id, config)
    return {"run_id": run_id, "status": "queued"}


@router.get("")
def list_runs_api(
    status: str | None = None,
    run_type: str | None = None,
    pack: str | None = None,
    mode: str | None = None,
    layer: str | None = None,
    limit: int = 100,
) -> dict:
    """List runs with optional filters."""
    runs = list_runs(status=status, run_type=run_type, pack=pack, mode=mode, layer=layer, limit=limit)
    return {"runs": runs}


@router.post("/cleanup")
def cleanup_runs(
    retention_count: int | None = None,
    retention_days: float | None = None,
) -> dict:
    """Manually trigger run metadata cleanup. Returns count of deleted run records."""
    deleted = run_cleanup(retention_count=retention_count, retention_days=retention_days)
    return {"deleted": deleted}


@router.get("/{run_id}")
def get_run_detail(run_id: str) -> dict:
    """Get run detail including status, stages, result summary."""
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@router.get("/{run_id}/status")
def get_run_status(run_id: str) -> dict:
    """Lightweight status check for polling."""
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": record["id"],
        "status": record.get("status"),
        "stage_progress": record.get("stage_progress"),
        "started_at": record.get("started_at"),
        "finished_at": record.get("finished_at"),
    }


@router.get("/{run_id}/logs")
def get_run_logs(run_id: str) -> dict:
    """Get run events/logs."""
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"events": record.get("events", [])}


def _has_masked_secrets(config: dict) -> bool:
    """Check if config contains masked/redacted values that would break rerun."""
    if not config:
        return False
    for k, v in config.items():
        if isinstance(v, str) and v == "***":
            return True
        if isinstance(v, dict):
            if _has_masked_secrets(v):
                return True
    return False


@router.post("/{run_id}/rerun")
def rerun_run(run_id: str, background_tasks: BackgroundTasks) -> dict:
    """Start a new run with the same config as the previous run."""
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    config = record.get("config")
    if not config or not isinstance(config, dict):
        config = record.get("config_summary") or {}
    run_type = record.get("run_type") or "generate"

    if run_type == "benchmark":
        new_id = _new_run_id()
        create_run(new_id, "benchmark", config, selected_pack=config.get("pack"))
        background_tasks.add_task(execute_benchmark_async, new_id, config)
        return {"run_id": new_id, "status": "queued"}

    load_target = config.get("load_target")
    if load_target and load_target not in ("sqlite",) and _has_masked_secrets(config):
        raise HTTPException(
            status_code=400,
            detail="Config contains masked credentials. Rerun requires full config. Use Clone to create a new run and re-enter credentials.",
        )
    new_id = _new_run_id()
    create_run(new_id, "generate", config, selected_pack=config.get("pack") or config.get("selected_pack"))
    background_tasks.add_task(execute_generation_async, new_id, config)
    return {"run_id": new_id, "status": "queued"}


@router.post("/{run_id}/clone")
def clone_config(run_id: str) -> dict:
    """Return config payload for clone (prefill wizard/advanced)."""
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    config = record.get("config") or record.get("config_summary") or {}
    return {"config": config}
