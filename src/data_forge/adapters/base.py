"""Base interface for database adapters."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from itertools import islice
from typing import Any

from data_forge.models.schema import SchemaModel
from data_forge.models.generation import TableSnapshot


class BaseDatabaseAdapter(ABC):
    """Abstract base class for database adapters. All adapters must implement these methods."""

    DEFAULT_BATCH_SIZE = 1000

    def __init__(self, uri: str, batch_size: int = DEFAULT_BATCH_SIZE) -> None:
        self.uri = uri
        self.batch_size = batch_size
        self._connection: Any = None
        self._load_counts: dict[str, int] = {}

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database."""
        ...

    @abstractmethod
    def create_schema(self, schema_model: SchemaModel) -> None:
        """Create schema/namespace if applicable (e.g. PostgreSQL schema). No-op for SQLite/DuckDB."""
        ...

    @abstractmethod
    def create_tables(self, schema_model: SchemaModel) -> None:
        """Create tables from schema definition."""
        ...

    @abstractmethod
    def load_table(self, table_name: str, rows: list[dict[str, Any]]) -> int:
        """Load rows into a table. Returns number of rows loaded."""
        ...

    def load_tables(self, table_snapshots: list[TableSnapshot]) -> dict[str, int]:
        """Load multiple tables. Returns row counts per table."""
        counts: dict[str, int] = {}
        for snap in table_snapshots:
            n = self.load_table(snap.table_name, snap.rows)
            counts[snap.table_name] = n
            self._load_counts[snap.table_name] = n
        return counts

    def load_table_from_iter(
        self,
        table_name: str,
        rows_iter: Iterator[dict[str, Any]],
        batch_size: int | None = None,
    ) -> int:
        """Load table from row iterator in batches. Reduces memory when source is spill-backed."""
        size = batch_size or self.batch_size
        total = 0
        while True:
            batch = list(islice(rows_iter, size))
            if not batch:
                break
            total += self.load_table(table_name, batch)
        self._load_counts[table_name] = total
        return total

    @abstractmethod
    def validate_load(self) -> dict[str, Any]:
        """Validate that loaded row counts match expectations. Returns validation result."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the connection."""
        ...

    def __enter__(self) -> "BaseDatabaseAdapter":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
