"""Run service: thin facade over run store for API/CLI use."""

from typing import Any

from data_forge.storage import get_run_store


def create_run(
    run_id: str,
    run_type: str,
    config: dict[str, Any],
    *,
    selected_pack: str | None = None,
    source_scenario_id: str | None = None,
) -> dict[str, Any]:
    """Create a new run record."""
    return get_run_store().create_run(
        run_id, run_type, config,
        selected_pack=selected_pack,
        source_scenario_id=source_scenario_id,
    )


def get_run(run_id: str) -> dict[str, Any] | None:
    """Get run by id."""
    return get_run_store().get_run(run_id)


def update_run(run_id: str, **kwargs: Any) -> dict[str, Any] | None:
    """Update run record."""
    return get_run_store().update_run(run_id, **kwargs)


def list_runs(
    *,
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
    """List runs with optional filters. Supports offset/limit and cursor pagination."""
    return get_run_store().list_runs(
        status=status,
        run_type=run_type,
        pack=pack,
        mode=mode,
        layer=layer,
        source_scenario_id=source_scenario_id,
        limit=limit,
        offset=offset,
        cursor=cursor,
        include_archived=include_archived,
    )


def append_event(run_id: str, level: str, message: str) -> None:
    """Append a log event to the run record."""
    get_run_store().append_event(run_id, level, message)


def run_cleanup(
    retention_count: int | None = None,
    retention_days: float | None = None,
) -> int:
    """Run retention cleanup (metadata only). Returns count of run records removed."""
    return get_run_store().run_cleanup(
        retention_count=retention_count,
        retention_days=retention_days,
    )
