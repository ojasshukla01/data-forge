"""Metrics and run timeline for observability."""

from typing import Any

from data_forge.services import list_runs
from data_forge.services.retention_service import get_storage_usage, preview_cleanup


def get_run_metrics_summary(limit: int = 500) -> dict[str, Any]:
    """
    Aggregate metrics from run store and storage.
    Lightweight, local-friendly; no distributed tracing.
    """
    runs = list_runs(limit=limit, include_archived=True)
    storage = get_storage_usage()
    preview = preview_cleanup()

    total_runs = len(runs)
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    durations: list[float] = []
    total_rows = 0
    failure_categories: dict[str, int] = {}

    for r in runs:
        rt = r.get("run_type") or "generate"
        by_type[rt] = by_type.get(rt, 0) + 1
        st = r.get("status") or "unknown"
        by_status[st] = by_status.get(st, 0) + 1
        dur = r.get("duration_seconds")
        if dur is not None and isinstance(dur, (int, float)):
            durations.append(float(dur))
        summary = r.get("result_summary") or {}
        if isinstance(summary, dict):
            rows = summary.get("total_rows") or summary.get("total_rows_generated") or summary.get("rows_generated")
            if isinstance(rows, (int, float)):
                total_rows += int(rows)
        if st == "failed":
            err = r.get("error_message") or "unknown"
            category = err.split("\n")[0][:80] if err else "unknown"
            failure_categories[category] = failure_categories.get(category, 0) + 1

    avg_duration = round(sum(durations) / len(durations), 2) if durations else None

    return {
        "total_runs": total_runs,
        "runs_by_type": by_type,
        "runs_by_status": by_status,
        "average_duration_seconds": avg_duration,
        "total_rows_generated": total_rows,
        "artifact_count": storage.get("artifact_count", 0),
        "storage_mb": storage.get("total_size_mb", 0),
        "cleanup_candidates_count": len(preview.get("candidates", [])),
        "failure_categories": failure_categories,
    }


def get_run_timeline(run_id: str) -> dict[str, Any] | None:
    """
    Structured timeline for a run: stages with durations and events.
    Returns None if run not found.
    """
    from data_forge.services import get_run

    record = get_run(run_id)
    if not record:
        return None

    stages = record.get("stage_progress") or []
    events = record.get("events") or []
    total_duration = record.get("duration_seconds")
    started_at = record.get("started_at")
    finished_at = record.get("finished_at")

    # Build timeline entries: each stage with duration_seconds
    stage_durations: list[dict[str, Any]] = []
    slowest_stage: str | None = None
    slowest_duration: float = 0.0

    for s in stages:
        name = s.get("name", "")
        dur = s.get("duration_seconds")
        if dur is not None and name and s.get("status") in ("completed", "failed"):
            stage_durations.append({"name": name, "duration_seconds": dur, "status": s.get("status"), "message": s.get("message")})
            if dur > slowest_duration:
                slowest_duration = dur
                slowest_stage = name

    # Why slow hint
    why_slow: str | None = None
    if total_duration and total_duration > 0 and slowest_stage and slowest_duration > 0:
        pct = round(100 * slowest_duration / total_duration, 0)
        if pct >= 50:
            why_slow = f"{slowest_stage} took {pct:.0f}% of total time ({slowest_duration}s)"

    return {
        "run_id": run_id,
        "status": record.get("status"),
        "run_type": record.get("run_type"),
        "total_duration_seconds": total_duration,
        "started_at": started_at,
        "finished_at": finished_at,
        "stages": stage_durations,
        "stage_progress_full": stages,
        "events": events,
        "slowest_stage": slowest_stage,
        "slowest_stage_duration_seconds": slowest_duration if slowest_duration else None,
        "why_slow_hint": why_slow,
        "error_message": record.get("error_message"),
    }
