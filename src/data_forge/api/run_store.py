"""Run persistence: JSON files in runs/ directory."""

import json
import time
from pathlib import Path
from typing import Any, cast

from data_forge.config import Settings

_RUNS_DIR: Path | None = None


def _runs_dir() -> Path:
    global _RUNS_DIR
    if _RUNS_DIR is None:
        root = Settings().project_root.resolve()
        _RUNS_DIR = root / "runs"
        _RUNS_DIR.mkdir(parents=True, exist_ok=True)
    return _RUNS_DIR


def _run_path(run_id: str) -> Path:
    path = _runs_dir() / f"{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _redact_config(config: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive keys from config."""
    out = dict(config)
    for k in list(out.keys()):
        if any(s in k.lower() for s in ("password", "secret", "token", "credential", "uri")):
            if isinstance(out.get(k), str) and out[k]:
                out[k] = "***"
    return out


def create_run(
    run_id: str,
    run_type: str,
    config: dict[str, Any],
    selected_pack: str | None = None,
    source_scenario_id: str | None = None,
) -> dict[str, Any]:
    """Create a new run record with status=queued."""
    now = time.time()
    record: dict[str, Any] = {
        "id": run_id,
        "status": "queued",
        "created_at": now,
        "started_at": None,
        "finished_at": None,
        "duration_seconds": None,
        "run_type": run_type,
        "config": config,
        "config_summary": _redact_config(config),
        "selected_pack": selected_pack or config.get("pack"),
        "stage_progress": [],
        "warnings": [],
        "error_message": None,
        "result_summary": None,
        "artifact_paths": [],
        "artifacts": [],
        "output_dir": None,
        "events": [],
        "pinned": False,
        "archived_at": None,
    }
    if source_scenario_id:
        record["source_scenario_id"] = source_scenario_id
    path = _run_path(run_id)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    # Prune old runs to respect retention
    try:
        run_cleanup()
    except Exception:
        pass

    return record


def get_run(run_id: str) -> dict[str, Any] | None:
    """Load run record by id."""
    path = _run_path(run_id)
    if not path.exists():
        return None
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return None


def update_run(run_id: str, **kwargs: Any) -> dict[str, Any] | None:
    """Update run record. Merges kwargs into existing record."""
    record = get_run(run_id)
    if not record:
        return None
    for k, v in kwargs.items():
        if v is not None:
            record[k] = v
    path = _run_path(run_id)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def append_event(run_id: str, level: str, message: str) -> None:
    """Append a log event."""
    record = get_run(run_id)
    if not record:
        return
    events = record.get("events") or []
    events.append({"level": level, "message": message, "ts": time.time()})
    record["events"] = events[-200:]  # Keep last 200
    path = _run_path(run_id)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def list_runs(
    status: str | None = None,
    run_type: str | None = None,
    pack: str | None = None,
    mode: str | None = None,
    layer: str | None = None,
    source_scenario_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
    cursor: str | None = None,
    include_archived: bool = True,
) -> list[dict[str, Any]]:
    """List run records with optional filters. Supports offset/limit and cursor pagination."""
    runs_dir = _runs_dir()
    if not runs_dir.exists():
        return []
    records: list[dict[str, Any]] = []
    skipped = 0
    past_cursor = cursor is None

    for p in sorted(runs_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if len(records) >= limit:
            break
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not include_archived and r.get("archived_at"):
            continue
        if status and r.get("status") != status:
            continue
        if run_type and r.get("run_type") != run_type:
            continue
        if pack and r.get("selected_pack") != pack:
            continue
        if source_scenario_id and r.get("source_scenario_id") != source_scenario_id:
            continue
        cfg = r.get("config") or r.get("config_summary") or {}
        if mode and cfg.get("mode") != mode:
            continue
        if layer and cfg.get("layer") != layer:
            continue
        if cursor and not past_cursor:
            if r.get("id") == cursor:
                past_cursor = True
            continue
        if not cursor and skipped < offset:
            skipped += 1
            continue
        records.append(r)
    return records


def delete_run(run_id: str) -> bool:
    """Permanently delete a run record (remove JSON file). Does not remove output/ artifacts."""
    path = _run_path(run_id)
    if not path.exists():
        return False
    try:
        path.unlink()
        return True
    except OSError:
        return False


def run_cleanup(
    retention_count: int | None = None,
    retention_days: float | None = None,
) -> int:
    """
    Prune old run metadata files. Only deletes run records in runs/; does NOT delete output/ artifacts.
    Returns number of files deleted.
    """
    settings = Settings()
    count = retention_count if retention_count is not None else settings.runs_retention_count
    days = retention_days if retention_days is not None else settings.runs_retention_days

    runs_dir = _runs_dir()
    if not runs_dir.exists():
        return 0

    files = sorted(runs_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    to_delete: list[Path] = []
    now = time.time()

    for i, p in enumerate(files):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            r = {}
        if r.get("pinned"):
            continue
        if i >= count:
            to_delete.append(p)
            continue
        if days is not None and days > 0:
            try:
                mtime = p.stat().st_mtime
                if (now - mtime) / 86400 > days:
                    to_delete.append(p)
            except OSError:
                pass

    deleted = 0
    for p in to_delete:
        try:
            p.unlink()
            deleted += 1
        except OSError:
            pass
    return deleted
