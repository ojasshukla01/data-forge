"""Export generated data to CSV, JSON, Parquet, SQL."""

from collections.abc import Iterable, Iterator
from itertools import islice
from pathlib import Path
from typing import Any

from data_forge.config import OutputFormat
from data_forge.models.generation import TableSnapshot

__all__ = [
    "export_tables",
    "export_table",
    "export_table_chunked",
    "export_table_iter",
    "export_snapshots",
]


def export_tables(
    table_data: dict[str, list[dict[str, Any]]],
    output_dir: Path | str,
    fmt: OutputFormat | str = "parquet",
    sql_dialect: str = "postgresql",
) -> list[Path]:
    """Export each table to a file in output_dir. Returns list of written paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for name, rows in table_data.items():
        path = export_table(rows, output_dir / name, fmt, table_name=name, sql_dialect=sql_dialect)
        if path:
            paths.append(path)
    return paths


def export_table(
    rows: list[dict[str, Any]],
    path_base: Path | str,
    fmt: OutputFormat | str = "parquet",
    table_name: str = "table",
    sql_dialect: str = "postgresql",
) -> Path | None:
    """
    Export rows to a single file. path_base is path without extension; extension added by format.
    """
    path_base = Path(path_base)
    if isinstance(fmt, str):
        fmt = OutputFormat(fmt) if fmt in [e.value for e in OutputFormat] else OutputFormat.PARQUET
    path = path_base.with_suffix("." + fmt.value)

    if fmt == OutputFormat.CSV:
        return _export_csv(rows, path)
    if fmt == OutputFormat.JSON:
        return _export_json(rows, path)
    if fmt == OutputFormat.JSONL or fmt == OutputFormat.NDJSON:
        return _export_jsonl(rows, path)
    if fmt == OutputFormat.PARQUET:
        return _export_parquet(rows, path)
    if fmt == OutputFormat.SQL:
        return _export_sql(rows, path, table_name, sql_dialect)
    return None


def export_table_iter(
    rows_iter: Iterable[dict[str, Any]],
    path_base: Path | str,
    fmt: OutputFormat | str = "parquet",
    table_name: str = "table",
    sql_dialect: str = "postgresql",
    batch_size: int = 5000,
) -> Path | None:
    """
    Export rows from an iterator without requiring full-table materialization for
    streaming-friendly formats.
    """
    path_base = Path(path_base)
    if isinstance(fmt, str):
        fmt = OutputFormat(fmt) if fmt in [e.value for e in OutputFormat] else OutputFormat.PARQUET
    path = path_base.with_suffix("." + fmt.value)

    if fmt == OutputFormat.CSV:
        return _export_csv_iter(rows_iter, path)
    if fmt == OutputFormat.JSONL or fmt == OutputFormat.NDJSON:
        return _export_jsonl_iter(rows_iter, path)
    if fmt == OutputFormat.PARQUET:
        return _export_parquet_iter(rows_iter, path, batch_size=batch_size)
    if fmt == OutputFormat.SQL:
        return _export_sql_iter(rows_iter, path, table_name, sql_dialect, batch_size=batch_size)
    if fmt == OutputFormat.JSON:
        # JSON array requires full materialization by format definition.
        return _export_json(list(rows_iter), path)
    return None


def export_snapshots(
    snapshots: list[TableSnapshot],
    output_dir: Path | str,
    fmt: OutputFormat | str = "parquet",
    sql_dialect: str = "postgresql",
    batch_size: int = 5000,
) -> list[Path]:
    """
    Export table snapshots directly. Uses iterator path to avoid rebuilding an
    intermediate table_data dict from GenerationResult snapshots.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for snapshot in snapshots:
        path = export_table_iter(
            iter(snapshot.rows),
            output_dir / snapshot.table_name,
            fmt=fmt,
            table_name=snapshot.table_name,
            sql_dialect=sql_dialect,
            batch_size=batch_size,
        )
        if path:
            paths.append(path)
    return paths


def export_table_chunked(
    rows_iter: Iterator[dict[str, Any]],
    path_base: Path | str,
    fmt: str,
    table_name: str = "table",
    fieldnames: list[str] | None = None,
) -> Path | None:
    """Export rows incrementally from iterator. CSV/JSONL only. For CSV, fieldnames from first row if not provided."""
    path_base = Path(path_base)
    fmt_enum = OutputFormat(fmt) if fmt in [e.value for e in OutputFormat] else OutputFormat.PARQUET
    if fmt_enum not in (OutputFormat.CSV, OutputFormat.JSONL, OutputFormat.NDJSON):
        return None
    path = path_base.with_suffix("." + fmt_enum.value)
    try:
        first = next(rows_iter)
    except StopIteration:
        path.write_text("", encoding="utf-8")
        return path
    if fmt_enum == OutputFormat.CSV:
        import csv
        fn = fieldnames or list(first.keys())
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fn, extrasaction="ignore")
            w.writeheader()
            w.writerow(first)
            for row in rows_iter:
                w.writerow(row)
    else:
        import json
        with path.open("w", encoding="utf-8") as f:
            f.write(json.dumps(first, default=str) + "\n")
            for row in rows_iter:
                f.write(json.dumps(row, default=str) + "\n")
    return path


def _export_csv(rows: list[dict[str, Any]], path: Path) -> Path:
    import csv

    if not rows:
        path.write_text("", encoding="utf-8")
        return path
    all_keys: set[str] = set()
    for row in rows:
        all_keys.update(row.keys())
    fieldnames = list(rows[0].keys()) + [k for k in sorted(all_keys) if k not in rows[0]]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)
    return path


def _export_csv_iter(rows_iter: Iterable[dict[str, Any]], path: Path) -> Path:
    import csv

    iterator = iter(rows_iter)
    try:
        first = next(iterator)
    except StopIteration:
        path.write_text("", encoding="utf-8")
        return path
    fieldnames = list(first.keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerow(first)
        for row in iterator:
            w.writerow(row)
    return path


def _export_json(rows: list[dict[str, Any]], path: Path) -> Path:
    import json

    path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    return path


def _export_jsonl(rows: list[dict[str, Any]], path: Path) -> Path:
    import json

    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, default=str) + "\n")
    return path


def _export_jsonl_iter(rows_iter: Iterable[dict[str, Any]], path: Path) -> Path:
    import json

    with path.open("w", encoding="utf-8") as f:
        for row in rows_iter:
            f.write(json.dumps(row, default=str) + "\n")
    return path


_PARQUET_ROW_GROUP_SIZE = 5000


def _rows_to_arrow_table(rows: list[dict[str, Any]], cols: list[str]) -> Any:
    import pyarrow as pa

    arrays = []
    for c in cols:
        vals = [r.get(c) for r in rows]
        try:
            arr = pa.array(vals)
        except (pa.ArrowInvalid, TypeError):
            arr = pa.array([str(v) if v is not None else None for v in vals])
        arrays.append(arr)
    return pa.table(dict(zip(cols, arrays, strict=True)))


def _export_parquet(rows: list[dict[str, Any]], path: Path) -> Path:
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not rows:
        pq.write_table(pa.table({}), path)
        return path
    cols = list(rows[0].keys())
    if len(rows) <= _PARQUET_ROW_GROUP_SIZE:
        table = _rows_to_arrow_table(rows, cols)
        pq.write_table(table, path)
        return path
    # Write in row groups to avoid building one giant table in memory
    first_batch = rows[: min(_PARQUET_ROW_GROUP_SIZE, len(rows))]
    schema = _rows_to_arrow_table(first_batch, cols).schema
    with pq.ParquetWriter(path, schema) as writer:
        for i in range(0, len(rows), _PARQUET_ROW_GROUP_SIZE):
            chunk = rows[i : i + _PARQUET_ROW_GROUP_SIZE]
            writer.write_table(_rows_to_arrow_table(chunk, cols))
    return path


def _iter_row_batches(rows_iter: Iterable[dict[str, Any]], batch_size: int) -> Iterator[list[dict[str, Any]]]:
    iterator = iter(rows_iter)
    while True:
        batch = list(islice(iterator, batch_size))
        if not batch:
            return
        yield batch


def _export_parquet_iter(rows_iter: Iterable[dict[str, Any]], path: Path, batch_size: int) -> Path:
    import pyarrow as pa
    import pyarrow.parquet as pq

    batches = _iter_row_batches(rows_iter, max(1, batch_size))
    first_batch = next(batches, None)
    if not first_batch:
        pq.write_table(pa.table({}), path)
        return path
    cols = list(first_batch[0].keys())
    first_table = _rows_to_arrow_table(first_batch, cols)
    with pq.ParquetWriter(path, first_table.schema) as writer:
        writer.write_table(first_table)
        for batch in batches:
            writer.write_table(_rows_to_arrow_table(batch, cols))
    return path


_SQL_BATCH_SIZE = 2000


def _export_sql(
    rows: list[dict[str, Any]],
    path: Path,
    table_name: str,
    dialect: str,
) -> Path:
    def escape(v: Any) -> str:
        if v is None:
            return "NULL"
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, (int, float)):
            return str(v)
        s = str(v).replace("\\", "\\\\").replace("'", "''")
        return f"'{s}'"

    with path.open("w", encoding="utf-8") as f:
        for i in range(0, len(rows), _SQL_BATCH_SIZE):
            batch = rows[i : i + _SQL_BATCH_SIZE]
            lines = []
            for row in batch:
                cols = ", ".join(row.keys())
                vals = ", ".join(escape(row[k]) for k in row.keys())
                lines.append(f"INSERT INTO {table_name} ({cols}) VALUES ({vals});")
            f.write("\n".join(lines))
            if i + _SQL_BATCH_SIZE < len(rows):
                f.write("\n")
    return path


def _export_sql_iter(
    rows_iter: Iterable[dict[str, Any]],
    path: Path,
    table_name: str,
    dialect: str,
    batch_size: int,
) -> Path:
    def escape(v: Any) -> str:
        if v is None:
            return "NULL"
        if isinstance(v, bool):
            return "TRUE" if v else "FALSE"
        if isinstance(v, (int, float)):
            return str(v)
        s = str(v).replace("\\", "\\\\").replace("'", "''")
        return f"'{s}'"

    with path.open("w", encoding="utf-8") as f:
        first_batch = True
        for batch in _iter_row_batches(rows_iter, max(1, batch_size)):
            if not first_batch:
                f.write("\n")
            first_batch = False
            lines = []
            for row in batch:
                cols = ", ".join(row.keys())
                vals = ", ".join(escape(row[k]) for k in row.keys())
                lines.append(f"INSERT INTO {table_name} ({cols}) VALUES ({vals});")
            f.write("\n".join(lines))
    return path
