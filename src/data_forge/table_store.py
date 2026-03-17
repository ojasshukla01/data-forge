"""Table storage abstraction with pluggable backends."""

from __future__ import annotations

import json
import shutil
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

Row = dict[str, Any]
TableData = dict[str, list[Row]]


class TableStore(ABC):
    """Backend-agnostic table storage contract for generation pipeline stages."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Human-readable backend name."""

    @property
    def spill_path(self) -> str | None:
        return None

    @abstractmethod
    def table_names(self) -> list[str]:
        """Return all stored table names."""

    @abstractmethod
    def has_table(self, table_name: str) -> bool:
        """Whether a table exists in this store."""

    @abstractmethod
    def set_table_rows(self, table_name: str, rows: Iterable[Row]) -> None:
        """Replace all rows in a table."""

    @abstractmethod
    def append_rows(self, table_name: str, rows: Iterable[Row]) -> None:
        """Append rows to an existing table (or create table)."""

    @abstractmethod
    def iter_rows(self, table_name: str) -> Iterator[Row]:
        """Yield table rows."""

    @abstractmethod
    def get_row_count(self, table_name: str) -> int:
        """Return row count for a table."""

    def sample_rows(self, table_name: str, limit: int) -> list[Row]:
        if limit <= 0:
            return []
        out: list[Row] = []
        for i, row in enumerate(self.iter_rows(table_name)):
            if i >= limit:
                break
            out.append(dict(row))
        return out

    def materialize_table(self, table_name: str) -> list[Row]:
        return [dict(row) for row in self.iter_rows(table_name)]

    def materialize_all(self) -> TableData:
        return {name: self.materialize_table(name) for name in self.table_names()}

    def replace_all(self, table_data: TableData) -> None:
        for name in list(self.table_names()):
            if name not in table_data:
                self.delete_table(name)
        for name, rows in table_data.items():
            self.set_table_rows(name, rows)

    @abstractmethod
    def delete_table(self, table_name: str) -> None:
        """Delete a table from the store."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release backend resources."""


class InMemoryTableStore(TableStore):
    """TableStore that keeps all rows in process memory."""

    def __init__(self) -> None:
        self._tables: TableData = {}

    @property
    def backend_name(self) -> str:
        return "memory"

    def table_names(self) -> list[str]:
        return list(self._tables.keys())

    def has_table(self, table_name: str) -> bool:
        return table_name in self._tables

    def set_table_rows(self, table_name: str, rows: Iterable[Row]) -> None:
        self._tables[table_name] = [dict(r) for r in rows]

    def append_rows(self, table_name: str, rows: Iterable[Row]) -> None:
        if table_name not in self._tables:
            self._tables[table_name] = []
        self._tables[table_name].extend(dict(r) for r in rows)

    def iter_rows(self, table_name: str) -> Iterator[Row]:
        for row in self._tables.get(table_name, []):
            yield dict(row)

    def get_row_count(self, table_name: str) -> int:
        return len(self._tables.get(table_name, []))

    def delete_table(self, table_name: str) -> None:
        self._tables.pop(table_name, None)

    def cleanup(self) -> None:
        self._tables.clear()


class SpillBackedTableStore(TableStore):
    """
    Spill-backed TableStore using JSONL files in a temp directory.

    This backend keeps only light metadata in memory while rows live on disk.
    """

    def __init__(self, spill_dir: Path | None = None) -> None:
        if spill_dir is None:
            temp_dir = tempfile.TemporaryDirectory(prefix="data-forge-table-store-")
            self._tmp: tempfile.TemporaryDirectory[str] | None = temp_dir
            self._root = Path(temp_dir.name)
        else:
            self._tmp = None
            self._root = Path(spill_dir)
            self._root.mkdir(parents=True, exist_ok=True)
        self._files: dict[str, Path] = {}
        self._row_counts: dict[str, int] = {}

    @property
    def backend_name(self) -> str:
        return "spill"

    @property
    def spill_path(self) -> str | None:
        return str(self._root)

    def table_names(self) -> list[str]:
        return list(self._files.keys())

    def has_table(self, table_name: str) -> bool:
        return table_name in self._files

    def _table_path(self, table_name: str) -> Path:
        if table_name not in self._files:
            safe = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in table_name)
            self._files[table_name] = self._root / f"{safe}.jsonl"
        return self._files[table_name]

    def set_table_rows(self, table_name: str, rows: Iterable[Row]) -> None:
        path = self._table_path(table_name)
        count = 0
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(dict(row), default=str) + "\n")
                count += 1
        self._row_counts[table_name] = count

    def append_rows(self, table_name: str, rows: Iterable[Row]) -> None:
        path = self._table_path(table_name)
        count = self._row_counts.get(table_name, 0)
        with path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(dict(row), default=str) + "\n")
                count += 1
        self._row_counts[table_name] = count

    def iter_rows(self, table_name: str) -> Iterator[Row]:
        path = self._files.get(table_name)
        if not path or not path.exists():
            return
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                item = json.loads(text)
                if isinstance(item, dict):
                    yield item

    def get_row_count(self, table_name: str) -> int:
        return self._row_counts.get(table_name, 0)

    def delete_table(self, table_name: str) -> None:
        path = self._files.pop(table_name, None)
        self._row_counts.pop(table_name, None)
        if path and path.exists():
            path.unlink(missing_ok=True)

    def cleanup(self) -> None:
        self._files.clear()
        self._row_counts.clear()
        if self._tmp is not None:
            self._tmp.cleanup()
            return
        shutil.rmtree(self._root, ignore_errors=True)


def build_table_store(
    backend: str,
    spill_dir: Path | None = None,
) -> TableStore:
    normalized = (backend or "memory").strip().lower()
    if normalized == "spill":
        return SpillBackedTableStore(spill_dir=spill_dir)
    return InMemoryTableStore()
