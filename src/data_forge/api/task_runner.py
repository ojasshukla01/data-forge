"""Background task runner for async generation."""

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from data_forge.storage import get_run_store
from data_forge.api import custom_schema_store
from data_forge.api.services import run_generate
from data_forge.api.schemas import GenerateRequest
from data_forge.models.config_schema import RunConfig
from data_forge.models.run_manifest import build_run_manifest, write_manifest_json, write_manifest_markdown
from data_forge.config import Settings
from data_forge.simulation.event_stream import generate_event_stream, write_event_stream_jsonl
from data_forge.simulation.time_patterns import EventPattern

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


def _stage_record(name: str, status: str = "pending", **kw: Any) -> dict[str, Any]:
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
    if "event_stream" in rel_lower or ("events" in rel_lower and ".jsonl" in rel_lower):
        return "event_stream"
    if "pipeline_snapshot" in rel_lower or "snapshot" in rel_lower:
        return "pipeline_snapshot"
    if "benchmark_profile" in rel_lower:
        return "benchmark_profile"
    return "dataset"


def _run_pipeline_simulation(
    output_dir: Path,
    config: dict[str, Any],
    pack: str | None,
) -> tuple[list[Path], dict[str, Any]]:
    """Generate event streams and pipeline snapshots when pipeline_simulation enabled."""
    sim = config.get("pipeline_simulation")
    if not sim or not sim.get("enabled"):
        return [], {}

    pack_id = pack or "saas_billing"
    seed = int(config.get("seed", 42))
    density = (sim.get("event_density") or "medium").lower()
    event_counts = {"low": 500, "medium": 2000, "high": 10000}
    event_count = event_counts.get(density, 2000)

    start_date = sim.get("start_date") or "2024-01-01"
    end_date = sim.get("end_date") or "2024-01-31"
    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        start_ts = start_dt.timestamp()
        end_ts = end_dt.timestamp()
    except (ValueError, TypeError):
        start_ts = 1704067200.0  # 2024-01-01
        end_ts = 1706745600.0   # 2024-01-31

    pattern_str = (sim.get("event_pattern") or "steady").lower()
    try:
        pattern = EventPattern(pattern_str)
    except ValueError:
        pattern = EventPattern.STEADY
    replay_mode = (sim.get("replay_mode") or "ordered").lower()
    late_ratio = float(sim.get("late_arrival_ratio") or 0)

    events = generate_event_stream(
        pack_id=pack_id,
        event_count=event_count,
        start_ts=start_ts,
        end_ts=end_ts,
        pattern=pattern,
        replay_mode=replay_mode,
        late_arrival_ratio=late_ratio,
        seed=seed,
    )

    paths: list[Path] = []
    events_dir = output_dir / "event_stream"
    events_dir.mkdir(parents=True, exist_ok=True)
    events_path = events_dir / "events.jsonl"
    write_event_stream_jsonl(events, events_path)
    paths.append(events_path)

    # Pipeline snapshot metadata
    snapshot = {
        "stages": ["source", "transform", "validate", "export", "load"],
        "event_count": len(events),
        "time_window": {"start": start_date, "end": end_date},
        "event_pattern": pattern_str,
        "replay_mode": replay_mode,
    }
    snapshot_path = output_dir / "pipeline_snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    paths.append(snapshot_path)

    summary = {
        "event_stream_count": len(events),
        "time_window": {"start": start_date, "end": end_date},
        "event_pattern": pattern_str,
        "replay_mode": replay_mode,
        "late_arrival_ratio": late_ratio,
    }
    return paths, {"pipeline_simulation": summary}


def _build_artifacts(output_dir: Path, export_paths: list[str], int_summaries: dict[str, Any]) -> list[dict[str, Any]]:
    """Build artifact registry from export_paths and integration summaries."""
    artifacts: list[dict[str, Any]] = []
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


def _mark_stage(stages: list[dict[str, Any]], name: str, status: str, msg: str | None = None) -> list[dict[str, Any]]:
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
    Config is normalized via RunConfig (versioned schema) for backward compatibility.
    """
    store = get_run_store()
    store.append_event(run_id, "info", "Starting generation")
    store.update_run(run_id, status="running", started_at=time.time())

    # Initialize stages
    stages = [_stage_record(s, "pending") for s in STAGES]
    store.update_run(run_id, stage_progress=stages)

    record = store.get_run(run_id)
    if not record:
        return

    try:
        # Normalize config (legacy flat or nested) to versioned RunConfig, then to flat for engine
        run_config = RunConfig.from_flat_dict(config)
        flat = run_config.to_flat_dict()
        req = GenerateRequest(**{k: v for k, v in flat.items() if k in GenerateRequest.model_fields})

        # Schema/rule load
        stages = _mark_stage(record["stage_progress"], "schema_load", "running")
        store.update_run(run_id, stage_progress=stages)
        store.append_event(run_id, "info", "Loading schema and rules")
        stages = _mark_stage(stages, "schema_load", "completed")
        stages = _mark_stage(stages, "rule_load", "completed")
        record = store.update_run(run_id, stage_progress=stages) or {}

        # Generation
        stages = _mark_stage(stages, "generation", "running")
        store.update_run(run_id, stage_progress=stages)
        store.append_event(run_id, "info", "Running generation")

        result = run_generate(req)
        record = store.get_run(run_id)
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
        store.update_run(run_id, stage_progress=stages)

        # Pipeline simulation (event streams, snapshots)
        output_dir_path = Path(result.get("output_dir", "")) if result.get("output_dir") else None
        export_paths_all = list(result.get("export_paths", []))
        if config.get("pipeline_simulation", {}).get("enabled") and output_dir_path and output_dir_path.exists():
            try:
                sim_paths, sim_summary = _run_pipeline_simulation(
                    output_dir_path, config, config.get("pack")
                )
                export_paths_all.extend(str(p) for p in sim_paths)
                int_sum = {**int_sum, **sim_summary}
            except Exception as sim_err:
                int_sum["pipeline_simulation"] = {"enabled": True, "error": str(sim_err)}

        # Build result summary; persist output run_id (folder name) for artifact links
        tables = result.get("tables", [])
        total_rows = sum((t.get("row_count") or 0) for t in tables)
        output_run_id = result.get("run_id")
        custom_schema_version = None
        custom_schema_name = None
        custom_schema_snapshot_hash = None
        custom_schema_table_names: list[str] | None = None
        if config.get("custom_schema_id"):
            try:
                rec = custom_schema_store.get_custom_schema(config["custom_schema_id"])
                if rec:
                    if rec.get("versions"):
                        custom_schema_version = rec.get("version") or len(rec["versions"])
                    custom_schema_name = rec.get("name") or config.get("custom_schema_id")
                    # Lightweight snapshot for provenance when schema is later deleted
                    schema_body = rec["versions"][-1].get("schema", {}) if rec.get("versions") else {}
                    try:
                        canonical = json.dumps(schema_body, sort_keys=True)
                        custom_schema_snapshot_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]
                    except Exception:
                        pass
                    tables = schema_body.get("tables") or []
                    custom_schema_table_names = [t.get("name") for t in tables if t.get("name")]
            except Exception:
                pass
        summary = {
            "selected_pack": config.get("pack"),
            "custom_schema_id": config.get("custom_schema_id"),
            "custom_schema_version": custom_schema_version,
            "custom_schema_name": custom_schema_name,
            "custom_schema_snapshot_hash": custom_schema_snapshot_hash,
            "custom_schema_table_names": custom_schema_table_names,
            "total_tables": len(tables),
            "total_rows": total_rows,
            "duration_seconds": result.get("duration_seconds"),
            "warnings": result.get("performance_warnings") or [],
            "quality_summary": result.get("quality_report", {}),
            "output_dir": result.get("output_dir"),
            "export_paths": export_paths_all,
            "integration_summaries": int_sum,
        }
        if int_sum.get("pipeline_simulation"):
            summary["pipeline_simulation_summary"] = int_sum["pipeline_simulation"]
        warnings = record.get("warnings") or []
        warnings.extend(result.get("performance_warnings") or [])

        finished = time.time()
        started = record.get("started_at") or finished
        duration = round(finished - started, 2)
        artifacts_list = (
            _build_artifacts(output_dir_path, export_paths_all, int_sum)
            if output_dir_path and output_dir_path.exists()
            else []
        )

        store.update_run(
            run_id,
            status="succeeded",
            finished_at=finished,
            duration_seconds=duration,
            result_summary={**summary, "artifact_run_id": output_run_id},
            artifact_paths=export_paths_all,
            artifacts=artifacts_list,
            output_dir=result.get("output_dir"),
            output_run_id=output_run_id,
            warnings=warnings,
            stage_progress=stages,
        )
        try:
            settings = Settings()
            manifest_config = dict(config)
            if custom_schema_version is not None:
                manifest_config["custom_schema_version"] = custom_schema_version
            manifest = build_run_manifest(
                run_id,
                record.get("run_type", "generate"),
                manifest_config,
                scenario_id=record.get("source_scenario_id"),
                scenario_version=record.get("scenario_version"),
                output_run_id=output_run_id,
                total_rows=total_rows,
                duration_seconds=duration,
                storage_backend=getattr(settings, "storage_backend", "file"),
                project_root=settings.project_root,
                custom_schema_name=custom_schema_name,
                custom_schema_snapshot_hash=custom_schema_snapshot_hash,
                custom_schema_table_names=custom_schema_table_names,
            )
            if output_dir_path and output_dir_path.exists():
                write_manifest_json(manifest, output_dir_path)
                write_manifest_markdown(manifest, output_dir_path)
        except Exception:
            pass
        store.append_event(run_id, "info", f"Completed: {len(tables)} tables, {total_rows} rows")

    except Exception as e:
        record = store.get_run(run_id)
        if record:
            err_msg = str(e)
            stages = _mark_stage(record.get("stage_progress") or [], "generation", "failed", err_msg)
            store.update_run(
                run_id,
                status="failed",
                finished_at=time.time(),
                error_message=err_msg,
                stage_progress=stages,
            )
        store.append_event(run_id, "error", str(e))


