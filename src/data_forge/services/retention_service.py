"""Retention and cleanup service: preview, execute, archive, delete, pin, storage usage."""

import shutil
import time
from pathlib import Path
from typing import Any

from data_forge.config import Settings
from data_forge.models.artifact_metadata import RetentionPolicy
from data_forge.storage import get_run_store


def _output_base() -> Path:
    s = Settings()
    return s.project_root / s.output_dir


def _run_dir_size(run_id: str) -> int:
    """Total size in bytes of output/<run_id> directory."""
    base = _output_base() / run_id
    if not base.is_dir():
        return 0
    total = 0
    try:
        for f in base.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    except OSError:
        pass
    return total


def preview_cleanup(
    policy: RetentionPolicy | None = None,
    *,
    retention_count: int | None = None,
    retention_days: float | None = None,
) -> dict[str, Any]:
    """
    Dry-run: return list of runs that would be removed by cleanup.
    Does not modify anything.
    """
    store = get_run_store()
    settings = Settings()
    count = (retention_count if retention_count is not None else getattr(policy, "max_run_count", None))
    if count is None:
        count = settings.runs_retention_count
    days = retention_days if retention_days is not None else (getattr(policy, "max_age_days", None) if policy else None)
    if days is None:
        days = settings.runs_retention_days

    # List all runs (include archived for preview), then apply same logic as cleanup
    all_runs = store.list_runs(limit=5000, include_archived=True)
    # Sort by created_at desc (newest first)
    all_runs = sorted(all_runs, key=lambda r: r.get("created_at") or 0, reverse=True)

    candidates: list[dict[str, Any]] = []
    now = time.time()
    for i, r in enumerate(all_runs):
        if r.get("pinned"):
            continue
        if policy and policy.exclude_archived and r.get("archived_at"):
            continue
        status = r.get("status") or ""
        if policy and status in (policy.exclude_statuses or []):
            continue
        run_type = r.get("run_type") or ""
        if policy and policy.exclude_run_types and run_type in policy.exclude_run_types:
            continue
        if i >= count:
            candidates.append({
                "run_id": r.get("id"),
                "run_type": run_type,
                "status": status,
                "created_at": r.get("created_at"),
                "age_days": (now - (r.get("created_at") or now)) / 86400,
            })
            continue
        if days is not None and days > 0:
            age_days = (now - (r.get("created_at") or now)) / 86400
            if age_days > days:
                candidates.append({
                    "run_id": r.get("id"),
                    "run_type": run_type,
                    "status": status,
                    "created_at": r.get("created_at"),
                    "age_days": age_days,
                })

    return {
        "candidates": candidates,
        "policy": {
            "retention_count": count,
            "retention_days": days,
        },
        "dry_run": True,
    }


def execute_cleanup(
    delete_artifacts: bool = False,
    *,
    retention_count: int | None = None,
    retention_days: float | None = None,
) -> dict[str, Any]:
    """Run retention cleanup. Returns count of run records removed (and optionally artifact dirs)."""
    store = get_run_store()
    settings = Settings()
    count = retention_count if retention_count is not None else settings.runs_retention_count
    days = retention_days if retention_days is not None else settings.runs_retention_days

    # Get candidates the same way as preview
    preview = preview_cleanup(retention_count=count, retention_days=days)
    run_ids = [c["run_id"] for c in preview["candidates"] if c.get("run_id")]

    deleted_records = store.run_cleanup(retention_count=count, retention_days=days)

    deleted_dirs = 0
    if delete_artifacts and run_ids:
        base = _output_base()
        for run_id in run_ids:
            path = base / run_id
            if path.is_dir():
                try:
                    shutil.rmtree(path)
                    deleted_dirs += 1
                except OSError:
                    pass

    return {
        "deleted_run_records": deleted_records,
        "deleted_artifact_dirs": deleted_dirs,
        "run_ids_affected": run_ids[:100],
    }


def archive_run(run_id: str) -> dict[str, Any] | None:
    """Mark run as archived (hidden from default list, retained)."""
    store = get_run_store()
    record = store.get_run(run_id)
    if not record:
        return None
    store.update_run(run_id, archived_at=time.time())
    return store.get_run(run_id)


def unarchive_run(run_id: str) -> dict[str, Any] | None:
    """Clear archived_at so run appears in default list again."""
    store = get_run_store()
    record = store.get_run(run_id)
    if not record:
        return None
    store.update_run(run_id, archived_at=None)
    return store.get_run(run_id)


def delete_run(run_id: str, delete_artifacts: bool = False) -> bool:
    """Permanently remove run record; optionally delete output/<run_id> directory."""
    store = get_run_store()
    if not store.get_run(run_id):
        return False
    ok = store.delete_run(run_id)
    if ok and delete_artifacts:
        path = _output_base() / run_id
        if path.is_dir():
            try:
                shutil.rmtree(path)
            except OSError:
                pass
    return ok


def pin_run(run_id: str) -> dict[str, Any] | None:
    """Pin run so it is excluded from retention cleanup."""
    store = get_run_store()
    if not store.get_run(run_id):
        return None
    store.update_run(run_id, pinned=True)
    return store.get_run(run_id)


def unpin_run(run_id: str) -> dict[str, Any] | None:
    """Unpin run."""
    store = get_run_store()
    if not store.get_run(run_id):
        return None
    store.update_run(run_id, pinned=False)
    return store.get_run(run_id)


def get_storage_usage() -> dict[str, Any]:
    """Aggregate storage usage: run count, artifact count, total size, by run."""
    store = get_run_store()
    base = _output_base()
    runs = store.list_runs(limit=2000, include_archived=True)

    total_bytes = 0
    artifact_count = 0
    by_run: list[dict[str, Any]] = []

    for r in runs:
        run_id = r.get("id")
        if not run_id:
            continue
        run_dir = base / run_id
        size = _run_dir_size(run_id) if run_dir.is_dir() else 0
        if run_dir.is_dir():
            try:
                artifact_count += sum(1 for _ in run_dir.rglob("*") if _.is_file())
            except OSError:
                pass
        total_bytes += size
        by_run.append({
            "run_id": run_id,
            "run_type": r.get("run_type"),
            "status": r.get("status"),
            "created_at": r.get("created_at"),
            "size_bytes": size,
            "pinned": r.get("pinned", False),
            "archived_at": r.get("archived_at"),
        })

    by_run.sort(key=lambda x: x.get("created_at") or 0, reverse=True)

    return {
        "runs_count": len(runs),
        "artifact_count": artifact_count,
        "total_size_bytes": total_bytes,
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
        "by_run": by_run[:200],
    }


class RetentionService:
    """Facade for retention operations (for dependency injection if needed)."""

    @staticmethod
    def preview_cleanup(
        policy: RetentionPolicy | None = None,
        *,
        retention_count: int | None = None,
        retention_days: float | None = None,
    ) -> dict[str, Any]:
        return preview_cleanup(policy, retention_count=retention_count, retention_days=retention_days)

    @staticmethod
    def execute_cleanup(
        delete_artifacts: bool = False,
        *,
        retention_count: int | None = None,
        retention_days: float | None = None,
    ) -> dict[str, Any]:
        return execute_cleanup(delete_artifacts, retention_count=retention_count, retention_days=retention_days)

    @staticmethod
    def archive_run(run_id: str) -> dict[str, Any] | None:
        return archive_run(run_id)

    @staticmethod
    def unarchive_run(run_id: str) -> dict[str, Any] | None:
        return unarchive_run(run_id)

    @staticmethod
    def delete_run(run_id: str, delete_artifacts: bool = False) -> bool:
        return delete_run(run_id, delete_artifacts=delete_artifacts)

    @staticmethod
    def pin_run(run_id: str) -> dict[str, Any] | None:
        return pin_run(run_id)

    @staticmethod
    def unpin_run(run_id: str) -> dict[str, Any] | None:
        return unpin_run(run_id)

    @staticmethod
    def get_storage_usage() -> dict[str, Any]:
        return get_storage_usage()
