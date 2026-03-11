"""Golden dataset manifest for regression testing."""

import hashlib
import json
from pathlib import Path
from typing import Any, cast


def schema_signature(schema: "Any") -> str:
    """Compute a stable hash of schema structure."""
    from data_forge.models.schema import SchemaModel

    if not isinstance(schema, SchemaModel):
        return ""
    parts = []
    for t in schema.tables:
        parts.append(t.name)
        for c in t.columns:
            parts.append(f"{c.name}:{c.data_type.value}")
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:16]


def create_manifest(
    seed: int,
    mode: str,
    layer: str,
    row_counts: dict[str, int],
    schema_sig: str,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Create a golden manifest dict."""
    manifest: dict[str, Any] = {
        "seed": seed,
        "mode": mode,
        "layer": layer,
        "row_counts": row_counts,
        "schema_signature": schema_sig,
    }
    return manifest


def write_manifest(manifest: dict[str, Any], path: Path) -> Path:
    """Write manifest to JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def load_manifest(path: Path) -> dict[str, Any]:
    """Load manifest from JSON file."""
    return cast(dict[str, Any], json.loads(Path(path).read_text(encoding="utf-8")))


def compute_checksums(data_dir: Path) -> dict[str, str]:
    """Compute per-file checksums for a directory (optional, for stricter validation)."""
    checksums: dict[str, str] = {}
    for f in sorted(Path(data_dir).rglob("*")):
        if f.is_file():
            rel = str(f.relative_to(data_dir)).replace("\\", "/")
            checksums[rel] = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
    return checksums


def validate_against_manifest(
    data_dir: Path,
    manifest: dict[str, Any],
    schema_sig: str | None = None,
) -> tuple[bool, list[str]]:
    """
    Validate that output matches manifest. Returns (ok, list of mismatch messages).
    """
    errors: list[str] = []
    data_dir = Path(data_dir)

    expected_counts = manifest.get("row_counts", {})
    if not expected_counts:
        return True, []

    for table_name, expected_count in expected_counts.items():
        for ext in (".csv", ".json", ".parquet", ".jsonl"):
            f = data_dir / f"{table_name}{ext}"
            if not f.exists():
                f = data_dir / "bronze" / f"{table_name}{ext}"
            if not f.exists():
                f = data_dir / "silver" / f"{table_name}{ext}"
            if not f.exists():
                f = data_dir / "gold" / f"{table_name}{ext}"
            if f.exists():
                actual = _count_rows(f, ext)
                if actual != expected_count:
                    errors.append(f"{table_name}: expected {expected_count} rows, got {actual}")
                break
        else:
            errors.append(f"{table_name}: no data file found")

    if schema_sig and manifest.get("schema_signature") != schema_sig:
        errors.append("schema_signature mismatch")

    return len(errors) == 0, errors


def _count_rows(path: Path, ext: str) -> int:
    """Count rows in a data file."""
    import csv
    import json

    ext = ext.lstrip(".")
    if ext == "csv":
        with path.open(encoding="utf-8") as f:
            return sum(1 for _ in csv.DictReader(f))
    if ext == "json":
        data = json.loads(path.read_text())
        return len(data) if isinstance(data, list) else 0
    if ext == "jsonl":
        return sum(1 for line in path.read_text().strip().split("\n") if line)
    if ext == "parquet":
        import pyarrow.parquet as pq
        return int(pq.read_table(path).num_rows)
    return 0
