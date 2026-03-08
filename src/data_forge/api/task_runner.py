"""Background task runner for async generation."""

import time
from pathlib import Path
from typing import Any

from data_forge.api.run_store import (
    get_run,
    update_run,
    append_event,
)
from data_forge.api.services import run_generate
from data_forge.api.schemas import GenerateRequest

STAGES = [
    "preflight",
    "schema_load",
    "rule_load",
    "generation",
    "anomaly_injection",
    "etl_transforms",
    "export",
    "contract_generation",
    "warehouse_load",
    "validation",
    "manifest",
    "complete",
]


def _stage_record(name: str, status: str = "pending", **kw: Any) -> dict:
    return {
        "name": name,
        "status": status,
        "started_at": None,
        "finished_at": None,
        "duration_seconds": None,
        "message": None,
        "metrics": {},
        **kw,
    }


def _artifact_type_from_path(path: str, rel: str) -> str:
    """Infer artifact type from path/relative path."""
    rel_lower = rel.lower()
    if "great_expectations" in rel_lower or "expectations" in rel_lower:
        return "ge"
    if "dbt" in rel_lower or "seeds" in rel_lower:
        return "dbt"
    if "airflow" in rel_lower or "dags" in rel_lower:
        return "airflow"
    if "contracts" in rel_lower:
        return "contracts"
    if "manifest" in rel_lower:
        return "manifest"
    return "dataset"


def _build_artifacts(output_dir: Path, export_paths: list[str], int_summaries: dict[str, Any]) -> list[dict]:
    """Build artifact registry from export_paths and integration summaries."""
    artifacts: list[dict] = []
    seen: set[str] = set()
    output_dir = Path(output_dir)

    for p_str in export_paths:
        try:
            p = Path(p_str)
            if not p.exists():
                continue
            rel = str(p.relative_to(output_dir)).replace("\\", "/")
            if rel in seen:
                continue
            seen.add(rel)
            stat = p.stat()
            artifacts.append({
                "type": _artifact_type_from_path(p_str, rel),
                "name": p.name,
                "path": rel,
                "size": stat.st_size,
                "created_at": stat.st_ctime,
            })
        except (ValueError, OSError):
            continue

    return artifacts


def _mark_stage(stages: list[dict], name: str, status: str, msg: str | None = None) -> list[dict]:
    stages = stages or []
    found = False
    for s in stages:
        if s["name"] == name:
            s["status"] = status
            if status == "running":
                s["started_at"] = time.time()
            elif status in ("completed", "failed", "skipped"):
                s["finished_at"] = time.time()
                if s.get("started_at") and status != "skipped":
                    s["duration_seconds"] = round(s["finished_at"] - s["started_at"], 2)
            if msg:
                s["message"] = msg
            found = True
            break
    if not found:
        stages.append(_stage_record(name, status=status, message=msg))
    return stages


def execute_generation_async(run_id: str, config: dict[str, Any]) -> None:
    """
    Execute generation in foreground (called from FastAPI BackgroundTasks).
    Updates run record with progress and result.
    """
    append_event(run_id, "info", "Starting generation")
    update_run(run_id, status="running", started_at=time.time())

    # Initialize stages
    stages = [_stage_record(s, "pending") for s in STAGES]
    update_run(run_id, stage_progress=stages)

    record = get_run(run_id)
    if not record:
        return

    try:
        # Schema/rule load
        stages = _mark_stage(record["stage_progress"], "schema_load", "running")
        update_run(run_id, stage_progress=stages)
        append_event(run_id, "info", "Loading schema and rules")

        req = GenerateRequest(**{k: v for k, v in config.items() if k in GenerateRequest.model_fields})
        stages = _mark_stage(stages, "schema_load", "completed")
        stages = _mark_stage(stages, "rule_load", "completed")
        record = update_run(run_id, stage_progress=stages) or {}

        # Generation
        stages = _mark_stage(stages, "generation", "running")
        update_run(run_id, stage_progress=stages)
        append_event(run_id, "info", "Running generation")

        result = run_generate(req)
        record = get_run(run_id)
        if not record:
            return

        stages = record["stage_progress"]
        stages = _mark_stage(stages, "generation", "completed")
        stages = _mark_stage(stages, "anomaly_injection", "completed", "Applied during generation")
        stages = _mark_stage(stages, "etl_transforms", "completed", "Applied during generation")
        stages = _mark_stage(stages, "export", "completed")

        # Mark integration stages from integration_summaries
        int_sum = result.get("integration_summaries") or {}
        if "contract_generation" in int_sum:
            stages = _mark_stage(stages, "contract_generation", "completed" if "error" not in int_sum["contract_generation"] else "failed", int_sum["contract_generation"].get("error"))
        else:
            stages = _mark_stage(stages, "contract_generation", "skipped", "Not requested")
        if config.get("load_target"):
            qr = result.get("quality_report") or {}
            wl = qr.get("warehouse_load") or {}
            stages = _mark_stage(stages, "warehouse_load", "completed" if wl.get("success") else "failed", wl.get("error"))
        else:
            stages = _mark_stage(stages, "warehouse_load", "skipped", "No load target")
        if "manifest" in int_sum:
            stages = _mark_stage(stages, "manifest", "completed" if "error" not in int_sum["manifest"] else "failed", int_sum["manifest"].get("error"))
        else:
            stages = _mark_stage(stages, "manifest", "skipped", "Not requested")
        stages = _mark_stage(stages, "validation", "completed", "Quality report computed")
        stages = _mark_stage(stages, "complete", "completed")
        update_run(run_id, stage_progress=stages)

        # Build result summary; persist output run_id (folder name) for artifact links
        tables = result.get("tables", [])
        total_rows = sum((t.get("row_count") or 0) for t in tables)
        output_run_id = result.get("run_id")
        summary = {
            "selected_pack": config.get("pack"),
            "total_tables": len(tables),
            "total_rows": total_rows,
            "duration_seconds": result.get("duration_seconds"),
            "warnings": result.get("performance_warnings") or [],
            "quality_summary": result.get("quality_report", {}),
            "output_dir": result.get("output_dir"),
            "export_paths": result.get("export_paths", []),
            "integration_summaries": int_sum,
        }
        warnings = record.get("warnings") or []
        warnings.extend(result.get("performance_warnings") or [])

        finished = time.time()
        started = record.get("started_at") or finished
        duration = round(finished - started, 2)

        output_dir_path = Path(result.get("output_dir", "")) if result.get("output_dir") else None
        export_paths_all = result.get("export_paths", [])
        artifacts_list = (
            _build_artifacts(output_dir_path, export_paths_all, int_sum)
            if output_dir_path and output_dir_path.exists()
            else []
        )

        update_run(
            run_id,
            status="succeeded",
            finished_at=finished,
            duration_seconds=duration,
            result_summary={**summary, "artifact_run_id": output_run_id},
            artifact_paths=result.get("export_paths", []),
            artifacts=artifacts_list,
            output_dir=result.get("output_dir"),
            output_run_id=output_run_id,
            warnings=warnings,
            stage_progress=stages,
        )
        append_event(run_id, "info", f"Completed: {len(tables)} tables, {total_rows} rows")

    except Exception as e:
        record = get_run(run_id)
        if record:
            err_msg = str(e)
            stages = _mark_stage(record.get("stage_progress") or [], "generation", "failed", err_msg)
            update_run(
                run_id,
                status="failed",
                finished_at=time.time(),
                error_message=err_msg,
                stage_progress=stages,
            )
        append_event(run_id, "error", err_msg)


