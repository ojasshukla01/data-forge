"""Adapter registry for pluggable database backends."""

from typing import Any

from data_forge.adapters.base import BaseDatabaseAdapter
from data_forge.adapters.sqlite_adapter import SQLiteAdapter
from data_forge.adapters.duckdb_adapter import DuckDBAdapter
from data_forge.adapters.postgres_adapter import PostgresAdapter
from data_forge.adapters.snowflake_adapter import SnowflakeAdapter
from data_forge.adapters.bigquery_adapter import BigQueryAdapter

DATABASE_ADAPTERS: dict[str, type[BaseDatabaseAdapter]] = {
    "sqlite": SQLiteAdapter,
    "duckdb": DuckDBAdapter,
    "postgres": PostgresAdapter,
    "postgresql": PostgresAdapter,
    "snowflake": SnowflakeAdapter,
    "bigquery": BigQueryAdapter,
}


class AdapterNotSupportedError(ValueError):
    """Raised when the requested database adapter is not available."""

    def __init__(self, name: str) -> None:
        supported = ", ".join(sorted(DATABASE_ADAPTERS.keys()))
        super().__init__(f"Database adapter '{name}' is not supported. Supported: {supported}")


def get_adapter(
    name: str,
    uri: str = "",
    batch_size: int = 1000,
    **kwargs: Any,
) -> BaseDatabaseAdapter:
    """Get an adapter instance by name. Cloud adapters (snowflake, bigquery) use kwargs for connection params."""
    key = name.lower().strip()
    if key not in DATABASE_ADAPTERS:
        raise AdapterNotSupportedError(name)
    cls = DATABASE_ADAPTERS[key]
    return cls(uri=uri, batch_size=batch_size, **kwargs)
