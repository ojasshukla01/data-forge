"""File-based storage backend (current JSON files in runs/ and scenarios/)."""

from typing import Any

from data_forge.storage.base import RunStoreInterface, ScenarioStoreInterface
from data_forge.api import run_store as rs
from data_forge.api import scenario_store as ss


class FileRunStore(RunStoreInterface):
    """Delegates to existing run_store module."""

    def create_run(
        self,
        run_id: str,
        run_type: str,
        config: dict[str, Any],
        *,
        selected_pack: str | None = None,
        source_scenario_id: str | None = None,
    ) -> dict[str, Any]:
        return rs.create_run(
            run_id, run_type, config,
            selected_pack=selected_pack,
            source_scenario_id=source_scenario_id,
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return rs.get_run(run_id)

    def update_run(self, run_id: str, **kwargs: Any) -> dict[str, Any] | None:
        return rs.update_run(run_id, **kwargs)

    def append_event(self, run_id: str, level: str, message: str) -> None:
        rs.append_event(run_id, level, message)

    def list_runs(
        self,
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
        return rs.list_runs(
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

    def run_cleanup(
        self,
        retention_count: int | None = None,
        retention_days: float | None = None,
    ) -> int:
        return rs.run_cleanup(
            retention_count=retention_count,
            retention_days=retention_days,
        )

    def delete_run(self, run_id: str) -> bool:
        return rs.delete_run(run_id)


class FileScenarioStore(ScenarioStoreInterface):
    """Delegates to existing scenario_store module."""

    def create_scenario(
        self,
        name: str,
        config: dict[str, Any],
        *,
        description: str = "",
        category: str = "custom",
        tags: list[str] | None = None,
        created_from_run_id: str | None = None,
        created_from_scenario_id: str | None = None,
    ) -> dict[str, Any]:
        return ss.create_scenario(
            name, config,
            description=description,
            category=category,
            tags=tags,
            created_from_run_id=created_from_run_id,
            created_from_scenario_id=created_from_scenario_id,
        )

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        return ss.get_scenario(scenario_id)

    def update_scenario(self, scenario_id: str, **kwargs: Any) -> dict[str, Any] | None:
        return ss.update_scenario(scenario_id, **kwargs)

    def delete_scenario(self, scenario_id: str) -> bool:
        return ss.delete_scenario(scenario_id)

    def list_scenarios(
        self,
        *,
        category: str | None = None,
        source_pack: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        cursor: str | None = None,
    ) -> list[dict[str, Any]]:
        return ss.list_scenarios(
            category=category,
            source_pack=source_pack,
            tag=tag,
            search=search,
            limit=limit,
            offset=offset,
            cursor=cursor,
        )

    def get_masked_field_names(self, config: dict[str, Any] | None, prefix: str = "") -> list[str]:
        return ss.get_masked_field_names(config, prefix=prefix)
