"""Adapter registry for pluggable database backends. Cloud adapters (snowflake, bigquery) are lazy-loaded when [warehouse] extra is installed."""

from typing import Any

from data_forge.adapters.base import BaseDatabaseAdapter
from data_forge.adapters.sqlite_adapter import SQLiteAdapter
from data_forge.adapters.duckdb_adapter import DuckDBAdapter
from data_forge.adapters.postgres_adapter import PostgresAdapter

# Core adapters always available
_CORE_ADAPTERS: dict[str, type[BaseDatabaseAdapter]] = {
    "sqlite": SQLiteAdapter,
    "duckdb": DuckDBAdapter,
    "postgres": PostgresAdapter,
    "postgresql": PostgresAdapter,
}

# Core adapters only; cloud (snowflake, bigquery) are lazy-loaded via get_adapter()
DATABASE_ADAPTERS: dict[str, type[BaseDatabaseAdapter]] = dict(_CORE_ADAPTERS)
SUPPORTED_ADAPTER_NAMES: tuple[str, ...] = tuple(_CORE_ADAPTERS.keys()) + ("snowflake", "bigquery")


class AdapterNotSupportedError(ValueError):
    """Raised when the requested database adapter is not available or its extra is not installed."""

    def __init__(self, name: str, message: str | None = None) -> None:
        supported = ", ".join(sorted(SUPPORTED_ADAPTER_NAMES))
        super().__init__(message or f"Database adapter '{name}' is not supported. Supported: {supported}")


def _get_cloud_adapter(name: str) -> type[BaseDatabaseAdapter]:
    """Lazy-load cloud adapter. Raises AdapterNotSupportedError if extra not installed."""
    if name == "snowflake":
        try:
            from data_forge.adapters.snowflake_adapter import SnowflakeAdapter
            return SnowflakeAdapter
        except ImportError as e:
            raise AdapterNotSupportedError(
                name,
                "Snowflake adapter requires the warehouse extra. Install with: pip install data-forge[warehouse]",
            ) from e
    if name == "bigquery":
        try:
            from data_forge.adapters.bigquery_adapter import BigQueryAdapter
            return BigQueryAdapter
        except ImportError as e:
            raise AdapterNotSupportedError(
                name,
                "BigQuery adapter requires the warehouse extra. Install with: pip install data-forge[warehouse]",
            ) from e
    raise AdapterNotSupportedError(name)


def get_adapter(
    name: str,
    uri: str = "",
    batch_size: int = 1000,
    **kwargs: Any,
) -> BaseDatabaseAdapter:
    """Get an adapter instance by name. Cloud adapters (snowflake, bigquery) use kwargs and require [warehouse] extra."""
    key = name.lower().strip()
    if key in _CORE_ADAPTERS:
        cls = _CORE_ADAPTERS[key]
    elif key in ("snowflake", "bigquery"):
        cls = _get_cloud_adapter(key)
    else:
        raise AdapterNotSupportedError(name)
    return cls(uri=uri, batch_size=batch_size, **kwargs)
