"""Reconciliation and diff helpers for manifest, layers, and loaded data."""

import csv
import json
from pathlib import Path
from typing import Any

from data_forge.golden import load_manifest
from data_forge.validators.quality import load_dataset_from_dir


def _load_row_counts_from_dir(data_dir: Path) -> dict[str, int]:
    """Load row counts from data directory (top-level or bronze/silver/gold)."""
    counts: dict[str, int] = {}

    def add_from(path: Path) -> None:
        if not path.is_dir():
            return
        for f in sorted(path.iterdir()):
            if not f.is_file():
                continue
            name = f.stem
            suffix = f.suffix.lower()
            try:
                if suffix == ".csv":
                    with f.open(encoding="utf-8", newline="") as fp:
                        counts[name] = sum(1 for _ in csv.DictReader(fp))
                elif suffix == ".json":
                    data = json.loads(f.read_text())
                    counts[name] = len(data) if isinstance(data, list) else 0
                elif suffix in (".jsonl", ".ndjson"):
                    counts[name] = sum(1 for line in f.read_text().strip().split("\n") if line)
                elif suffix == ".parquet":
                    import pyarrow.parquet as pq
                    counts[name] = pq.read_table(f).num_rows
            except Exception:
                pass

    add_from(data_dir)
    for sub in ("bronze", "silver", "gold"):
        add_from(data_dir / sub)
    return counts


def _find_data_file(data_dir: Path, table_name: str) -> Path | None:
    """Find data file for table in data_dir or bronze/silver/gold."""
    for base in [data_dir, data_dir / "bronze", data_dir / "silver", data_dir / "gold"]:
        for ext in (".csv", ".json", ".parquet", ".jsonl"):
            p = base / f"{table_name}{ext}"
            if p.exists():
                return p
    return None


def reconcile_manifest_vs_data(
    manifest_path: Path | str,
    data_dir: Path | str,
    schema: Any = None,
) -> dict[str, Any]:
    """
    Reconcile manifest expected row counts vs actual data.
    Optionally include missing tables, missing columns, duplicate PKs if schema provided.
    """
    manifest = load_manifest(Path(manifest_path))
    data_dir = Path(data_dir)
    expected = manifest.get("row_counts", {})

    actual_counts = _load_row_counts_from_dir(data_dir)

    row_count_diffs: dict[str, dict[str, int]] = {}
    missing_tables: list[str] = []
    missing_columns: dict[str, list[str]] = {}
    duplicate_primary_keys: dict[str, int] = {}

    for table_name, exp_count in expected.items():
        act = actual_counts.get(table_name)
        if act is None:
            missing_tables.append(table_name)
            row_count_diffs[table_name] = {"expected": exp_count, "actual": 0}
        elif act != exp_count:
            row_count_diffs[table_name] = {"expected": exp_count, "actual": act}

    for table_name in set(expected) - set(actual_counts):
        if table_name not in missing_tables:
            missing_tables.append(table_name)

    if schema:
        table_data = load_dataset_from_dir(data_dir)
        for sub in ("bronze", "silver", "gold"):
            sub_path = data_dir / sub
            if sub_path.is_dir():
                sub_data = load_dataset_from_dir(sub_path)
                for k, v in sub_data.items():
                    if k not in table_data or not table_data[k]:
                        table_data[k] = v
        for table_name, rows in table_data.items():
            table_def = schema.get_table(table_name) if hasattr(schema, "get_table") else None
            if table_def:
                pk_cols = list(getattr(table_def, "primary_key", None) or [])
                if not pk_cols:
                    pk_cols = [c.name for c in getattr(table_def, "columns", []) if getattr(c, "primary_key", False)]
                expected_cols = {c.name for c in getattr(table_def, "columns", [])}
                for row in rows[:1]:
                    missing = expected_cols - set(row.keys())
                    if missing:
                        missing_columns[table_name] = list(missing)
                if pk_cols and rows:
                    seen: dict[tuple[Any, ...], int] = {}
                    for row in rows:
                        key = tuple(row.get(pk) for pk in pk_cols)
                        seen[key] = seen.get(key, 0) + 1
                    dups = sum(1 for c in seen.values() if c > 1)
                    if dups > 0:
                        duplicate_primary_keys[table_name] = dups

    return {
        "reconciliation": {
            "row_count_diffs": row_count_diffs,
            "missing_tables": missing_tables,
            "missing_columns": missing_columns,
            "duplicate_primary_keys": duplicate_primary_keys,
        }
    }


def reconcile_layer_deltas(
    layers_data: dict[str, dict[str, list[dict[str, Any]]]],
) -> dict[str, Any]:
    """
    Compute bronze->silver and silver->gold row count deltas.
    """
    layer_deltas: dict[str, int] = {}
    if "bronze" in layers_data and "silver" in layers_data:
        bronze_total = sum(len(rows) for rows in layers_data["bronze"].values())
        silver_total = sum(len(rows) for rows in layers_data["silver"].values())
        layer_deltas["bronze_to_silver_removed"] = max(0, bronze_total - silver_total)
    if "silver" in layers_data and "gold" in layers_data:
        silver_total = sum(len(rows) for rows in layers_data["silver"].values())
        gold_total = sum(len(rows) for rows in layers_data["gold"].values())
        layer_deltas["silver_to_gold_removed"] = max(0, silver_total - gold_total)
    return {"reconciliation": {"layer_deltas": layer_deltas}}


def run_reconciliation(
    manifest_path: Path | str,
    data_dir: Path | str,
    schema: Any = None,
    layers_data: dict[str, dict[str, list[dict[str, Any]]]] | None = None,
) -> dict[str, Any]:
    """
    Full reconciliation report: manifest vs data, plus layer deltas if provided.
    """
    out = reconcile_manifest_vs_data(manifest_path, data_dir, schema)
    if layers_data:
        ld = reconcile_layer_deltas(layers_data)
        out["reconciliation"]["layer_deltas"] = ld["reconciliation"].get("layer_deltas", {})
    elif "layer_deltas" not in out["reconciliation"]:
        out["reconciliation"]["layer_deltas"] = {}
    return out
