"""Runs API router."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException

from data_forge.services import create_run, get_run, list_runs, get_masked_field_names
from data_forge.api.task_runner import execute_generation_async
from data_forge.api.routers.benchmark import execute_benchmark_async
from data_forge.services.retention_service import (
    preview_cleanup,
    execute_cleanup as retention_execute_cleanup,
    archive_run as retention_archive_run,
    unarchive_run as retention_unarchive_run,
    delete_run as retention_delete_run,
    pin_run as retention_pin_run,
    unpin_run as retention_unpin_run,
    get_storage_usage,
)
from data_forge.services.metrics_service import get_run_metrics_summary, get_run_timeline
from data_forge.services.lineage_service import get_run_lineage, get_run_manifest_from_disk

router = APIRouter(prefix="/api/runs", tags=["runs"])


def _new_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:12]}"


@router.post("/benchmark")
def start_benchmark(config: dict[str, Any], background_tasks: BackgroundTasks) -> dict[str, Any]:
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
def start_generate(config: dict[str, Any], background_tasks: BackgroundTasks) -> dict[str, Any]:
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
    source_scenario_id: str | None = None,
    limit: int = 100,
    include_archived: bool = False,
) -> dict[str, Any]:
    """List runs with optional filters. Default excludes archived runs."""
    runs = list_runs(
        status=status,
        run_type=run_type,
        pack=pack,
        mode=mode,
        layer=layer,
        source_scenario_id=source_scenario_id,
        limit=limit,
        include_archived=include_archived,
    )
    return {"runs": runs}


@router.get("/metrics")
def run_metrics(limit: int = 500) -> dict[str, Any]:
    """Aggregate metrics: total runs, by type/status, avg duration, rows, storage, failures."""
    return get_run_metrics_summary(limit=limit)


@router.get("/storage/summary")
def storage_summary() -> dict[str, Any]:
    """Storage usage: run count, artifact count, total size, by-run breakdown."""
    return get_storage_usage()


@router.get("/cleanup/preview")
def cleanup_preview(
    retention_count: int | None = None,
    retention_days: float | None = None,
) -> dict[str, Any]:
    """Dry-run: list runs that would be removed by cleanup (no changes)."""
    return preview_cleanup(retention_count=retention_count, retention_days=retention_days)


@router.post("/cleanup/execute")
def cleanup_execute(body: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Execute retention cleanup. Body: { delete_artifacts?: bool, retention_count?: int, retention_days?: float }."""
    return retention_execute_cleanup(
        delete_artifacts=bool(body.get("delete_artifacts", False)),
        retention_count=body.get("retention_count"),
        retention_days=body.get("retention_days"),
    )


def _build_run_comparison(left_run: dict[str, Any], right_run: dict[str, Any]) -> dict[str, Any]:
    """Build structured comparison for two runs."""
    left_cfg = left_run.get("config") or left_run.get("config_summary") or {}
    right_cfg = right_run.get("config") or right_run.get("config_summary") or {}
    left_sum = left_run.get("result_summary") or {}
    right_sum = right_run.get("result_summary") or {}

    def _diff(left: Any, right: Any) -> dict[str, Any]:
        return {"left": left, "right": right, "changed": left != right}

    metadata_diff = {
        "id": _diff(left_run.get("id"), right_run.get("id")),
        "status": _diff(left_run.get("status"), right_run.get("status")),
        "run_type": _diff(left_run.get("run_type"), right_run.get("run_type")),
        "duration_seconds": _diff(left_run.get("duration_seconds"), right_run.get("duration_seconds")),
    }
    config_diff = {
        "pack": _diff(left_cfg.get("pack"), right_cfg.get("pack")),
        "mode": _diff(left_cfg.get("mode"), right_cfg.get("mode")),
        "layer": _diff(left_cfg.get("layer"), right_cfg.get("layer")),
        "scale": _diff(left_cfg.get("scale"), right_cfg.get("scale")),
        "privacy_mode": _diff(left_cfg.get("privacy_mode"), right_cfg.get("privacy_mode")),
    }
    ps_l = left_cfg.get("pipeline_simulation") or {}
    ps_r = right_cfg.get("pipeline_simulation") or {}
    bench_l = left_cfg.get("benchmark") or {}
    bench_r = right_cfg.get("benchmark") or {}
    simulation_diff = {
        "enabled": _diff(ps_l.get("enabled") if isinstance(ps_l, dict) else None, ps_r.get("enabled") if isinstance(ps_r, dict) else None),
        "event_pattern": _diff(ps_l.get("event_pattern") if isinstance(ps_l, dict) else None, ps_r.get("event_pattern") if isinstance(ps_r, dict) else None),
    }
    benchmark_diff = {
        "enabled": _diff(bench_l.get("enabled") if isinstance(bench_l, dict) else None, bench_r.get("enabled") if isinstance(bench_r, dict) else None),
        "profile": _diff(bench_l.get("profile") if isinstance(bench_l, dict) else None, bench_r.get("profile") if isinstance(bench_r, dict) else None),
        "scale_preset": _diff(bench_l.get("scale_preset") if isinstance(bench_l, dict) else None, bench_r.get("scale_preset") if isinstance(bench_r, dict) else None),
    }
    total_l = left_sum.get("total_rows") or left_sum.get("total_rows_generated") or left_sum.get("rows_generated")
    total_r = right_sum.get("total_rows") or right_sum.get("total_rows_generated") or right_sum.get("rows_generated")
    summary_diff = {
        "total_rows": _diff(total_l, total_r),
        "throughput": _diff(left_sum.get("throughput"), right_sum.get("throughput")),
        "generation_seconds": _diff(left_sum.get("generation_seconds"), right_sum.get("generation_seconds")),
    }
    art_l = left_run.get("artifacts") or []
    art_r = right_run.get("artifacts") or []
    artifact_diff = {"count": _diff(len(art_l), len(art_r))}

    def _classify(d: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in d.items():
            if isinstance(v, dict) and "left" in v and "right" in v and "changed" in v:
                status = "changed" if v["changed"] else "unchanged"
                if v.get("left") is None and v.get("right") is not None:
                    status = "missing_on_left"
                elif v.get("left") is not None and v.get("right") is None:
                    status = "missing_on_right"
                out[k] = {**v, "status": status}
            else:
                out[k] = v
        return out

    result: dict[str, Any] = {
        "left_run": {
            "id": left_run.get("id"),
            "status": left_run.get("status"),
            "run_type": left_run.get("run_type"),
            "selected_pack": left_run.get("selected_pack"),
        },
        "right_run": {
            "id": right_run.get("id"),
            "status": right_run.get("status"),
            "run_type": right_run.get("run_type"),
            "selected_pack": right_run.get("selected_pack"),
        },
        "metadata_diff": _classify(metadata_diff),
        "config_diff": _classify(config_diff),
        "summary_diff": _classify(summary_diff),
        "simulation_diff": _classify(simulation_diff),
        "benchmark_diff": _classify(benchmark_diff),
        "artifact_diff": _classify(artifact_diff),
    }
    changed_count = sum(
        1 for section in ["metadata_diff", "config_diff", "summary_diff", "simulation_diff", "benchmark_diff", "artifact_diff"]
        for v in result.get(section, {}).values()
        if isinstance(v, dict) and v.get("status") == "changed"
    )
    result["summary"] = {
        "total_changed_fields": changed_count,
    }
    result["raw_diff"] = json.dumps(result, indent=2, default=str)
    return result


@router.get("/compare")
def compare_runs(left: str, right: str) -> dict[str, Any]:
    """Compare two runs. Returns structured diff for UI. Query: ?left=<id>&right=<id>."""
    left_run = get_run(left)
    right_run = get_run(right)
    if not left_run:
        raise HTTPException(status_code=404, detail=f"Run not found: {left}")
    if not right_run:
        raise HTTPException(status_code=404, detail=f"Run not found: {right}")
    return _build_run_comparison(left_run, right_run)


@router.post("/cleanup")
def cleanup_runs(
    retention_count: int | None = None,
    retention_days: float | None = None,
) -> dict[str, Any]:
    """Manually trigger run metadata cleanup (legacy). Uses storage abstraction; does not delete artifact dirs."""
    result = retention_execute_cleanup(
        delete_artifacts=False,
        retention_count=retention_count,
        retention_days=retention_days,
    )
    return {"deleted": result["deleted_run_records"]}


@router.get("/{run_id}")
def get_run_detail(run_id: str) -> dict[str, Any]:
    """Get run detail including status, stages, result summary."""
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@router.get("/{run_id}/status")
def get_run_status(run_id: str) -> dict[str, Any]:
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


@router.get("/{run_id}/timeline")
def get_run_timeline_api(run_id: str) -> dict[str, Any]:
    """Structured timeline: stages with durations, events, slowest stage hint."""
    timeline = get_run_timeline(run_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Run not found")
    return timeline


@router.get("/{run_id}/lineage")
def get_run_lineage_api(run_id: str) -> dict[str, Any]:
    """Lineage: run -> scenario -> version -> pack -> artifacts."""
    lineage = get_run_lineage(run_id)
    if not lineage:
        raise HTTPException(status_code=404, detail="Run not found")
    return lineage


@router.get("/{run_id}/manifest")
def get_run_manifest_api(run_id: str) -> dict[str, Any]:
    """Reproducibility manifest (from manifest.json in output dir if present)."""
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    manifest = get_run_manifest_from_disk(run_id)
    if not manifest:
        from data_forge.models.run_manifest import build_run_manifest
        from data_forge.config import Settings
        from data_forge.api import custom_schema_store
        config = record.get("config") or record.get("config_summary") or {}
        summary = record.get("result_summary") or {}
        settings = Settings()
        custom_schema_id = config.get("custom_schema_id")
        schema_missing = False
        if custom_schema_id:
            try:
                if custom_schema_store.get_custom_schema(custom_schema_id) is None:
                    schema_missing = True
            except Exception:
                schema_missing = True
        manifest = build_run_manifest(
            run_id,
            record.get("run_type", "generate"),
            config,
            scenario_id=record.get("source_scenario_id"),
            output_run_id=summary.get("artifact_run_id") or run_id,
            total_rows=summary.get("total_rows"),
            duration_seconds=record.get("duration_seconds"),
            storage_backend=getattr(settings, "storage_backend", "file"),
            project_root=settings.project_root,
            custom_schema_name=summary.get("custom_schema_name"),
            custom_schema_snapshot_hash=summary.get("custom_schema_snapshot_hash"),
            custom_schema_table_names=summary.get("custom_schema_table_names"),
            schema_missing=schema_missing,
        )
    return manifest


@router.get("/{run_id}/logs")
def get_run_logs(run_id: str) -> dict[str, Any]:
    """Get run events/logs."""
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"events": record.get("events", [])}


def _has_masked_secrets(config: dict[str, Any]) -> bool:
    """Check if config contains masked/redacted values that would break rerun."""
    if not config:
        return False
    for _k, v in config.items():
        if isinstance(v, str) and v == "***":
            return True
        if isinstance(v, dict):
            if _has_masked_secrets(v):
                return True
    return False


@router.post("/{run_id}/rerun")
def rerun_run(run_id: str, background_tasks: BackgroundTasks) -> dict[str, Any]:
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
def clone_config(run_id: str) -> dict[str, Any]:
    """Return config payload for clone (prefill wizard/advanced)."""
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    config = record.get("config") or record.get("config_summary") or {}
    masked = get_masked_field_names(config)
    result: dict[str, Any] = {"config": config}
    result["has_masked_sensitive_fields"] = bool(masked)
    if masked:
        result["masked_fields"] = masked
    return result


@router.post("/{run_id}/archive")
def archive_run_api(run_id: str) -> dict[str, Any]:
    """Archive run (hide from default list, retain data)."""
    record = retention_archive_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@router.post("/{run_id}/unarchive")
def unarchive_run_api(run_id: str) -> dict[str, Any]:
    """Unarchive run."""
    record = retention_unarchive_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@router.post("/{run_id}/delete")
def delete_run_api(run_id: str, body: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    """Permanently delete run record. Body: { delete_artifacts?: bool } to also remove output dir."""
    ok = retention_delete_run(run_id, delete_artifacts=bool(body.get("delete_artifacts", False)))
    if not ok:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"deleted": run_id}


@router.post("/{run_id}/pin")
def pin_run_api(run_id: str) -> dict[str, Any]:
    """Pin run (exclude from retention cleanup)."""
    record = retention_pin_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@router.post("/{run_id}/unpin")
def unpin_run_api(run_id: str) -> dict[str, Any]:
    """Unpin run."""
    record = retention_unpin_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return record
