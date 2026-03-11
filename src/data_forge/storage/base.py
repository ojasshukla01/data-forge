"""Storage abstractions for runs, scenarios, and artifacts."""

from abc import ABC, abstractmethod
from typing import Any


class RunStoreInterface(ABC):
    """Abstract run metadata store."""

    @abstractmethod
    def create_run(
        self,
        run_id: str,
        run_type: str,
        config: dict[str, Any],
        *,
        selected_pack: str | None = None,
        source_scenario_id: str | None = None,
    ) -> dict[str, Any]:
        ...

    @abstractmethod
    def get_run(self, run_id: str) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def update_run(self, run_id: str, **kwargs: Any) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def append_event(self, run_id: str, level: str, message: str) -> None:
        ...

    @abstractmethod
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
        include_archived: bool = True,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def run_cleanup(
        self,
        retention_count: int | None = None,
        retention_days: float | None = None,
    ) -> int:
        ...

    @abstractmethod
    def delete_run(self, run_id: str) -> bool:
        """Permanently remove run record. Artifact files (output dir) are handled by caller if needed."""
        ...


class ScenarioStoreInterface(ABC):
    """Abstract scenario metadata store."""

    @abstractmethod
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
        ...

    @abstractmethod
    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def update_scenario(self, scenario_id: str, **kwargs: Any) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def delete_scenario(self, scenario_id: str) -> bool:
        ...

    @abstractmethod
    def list_scenarios(
        self,
        *,
        category: str | None = None,
        source_pack: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def get_masked_field_names(self, config: dict[str, Any] | None, prefix: str = "") -> list[str]:
        ...
