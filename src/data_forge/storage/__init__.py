"""Storage abstraction: file-backed (default) or SQLite."""

from typing import TYPE_CHECKING

from data_forge.config import Settings

if TYPE_CHECKING:
    from data_forge.storage.base import RunStoreInterface, ScenarioStoreInterface

_run_store: "RunStoreInterface | None" = None
_scenario_store: "ScenarioStoreInterface | None" = None


def get_run_store() -> "RunStoreInterface":
    """Return the configured run store (file or SQLite)."""
    global _run_store
    if _run_store is None:
        settings = Settings()
        if getattr(settings, "storage_backend", "file") == "sqlite":
            from data_forge.storage.sqlite_backend import SQLiteRunStore
            _run_store = SQLiteRunStore(settings.sqlite_uri)
        else:
            from data_forge.storage.file_backend import FileRunStore
            _run_store = FileRunStore()
    return _run_store


def get_scenario_store() -> "ScenarioStoreInterface":
    """Return the configured scenario store (file or SQLite)."""
    global _scenario_store
    if _scenario_store is None:
        settings = Settings()
        if getattr(settings, "storage_backend", "file") == "sqlite":
            from data_forge.storage.sqlite_backend import SQLiteScenarioStore
            _scenario_store = SQLiteScenarioStore(settings.sqlite_uri)
        else:
            from data_forge.storage.file_backend import FileScenarioStore
            _scenario_store = FileScenarioStore()
    return _scenario_store


__all__ = ["get_run_store", "get_scenario_store"]
