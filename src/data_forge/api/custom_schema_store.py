"""Custom schema persistence: JSON files in custom_schemas/ directory.

This provides a simple, local-first registry for user-defined schemas.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, cast

from data_forge.api.security import ensure_custom_schema_path_safe, sanitize_schema_metadata, validate_schema_id
from data_forge.models.schema import SchemaModel

_SCHEMAS_DIR: Path | None = None


def _schemas_dir() -> Path:
    global _SCHEMAS_DIR
    if _SCHEMAS_DIR is None:
        root = Path(__file__).resolve().parent.parent.parent.parent
        _SCHEMAS_DIR = root / "custom_schemas"
        _SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    return _SCHEMAS_DIR


def _schema_path(schema_id: str) -> Path:
    base = _schemas_dir()
    return ensure_custom_schema_path_safe(base, schema_id)


def _now() -> float:
    return time.time()


def _new_schema_id() -> str:
    return f"schema_{uuid.uuid4().hex[:12]}"


def _load_record(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return None


def _save_record(path: Path, record: dict[str, Any]) -> None:
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def create_custom_schema(
    name: str,
    schema: dict[str, Any],
    *,
    description: str = "",
    tags: list[str] | None = None,
    created_from: str | None = None,
) -> dict[str, Any]:
    """Create a new custom schema. Returns full schema record."""
    name, description, tags = sanitize_schema_metadata(name, description, tags)
    schema_id = _new_schema_id()
    now = _now()

    # Validate via SchemaModel for basic structure; store as plain dict.
    model = SchemaModel.model_validate(schema)

    record: dict[str, Any] = {
        "id": schema_id,
        "name": name,
        "description": description or "",
        "tags": tags or [],
        "created_from": created_from,
        "created_at": now,
        "updated_at": now,
        "version": 1,
        "versions": [
            {
                "version": 1,
                "schema": model.model_dump(),
                "updated_at": now,
            }
        ],
    }
    path = _schema_path(schema_id)
    _save_record(path, record)
    return record


def get_custom_schema(schema_id: str) -> dict[str, Any] | None:
    """Load a custom schema by id."""
    validate_schema_id(schema_id)
    return _load_record(_schema_path(schema_id))


MAX_VERSIONS = 50


def update_custom_schema(schema_id: str, *, schema: dict[str, Any] | None = None, **meta: Any) -> dict[str, Any] | None:
    """Update metadata and/or append a new schema version."""
    validate_schema_id(schema_id)
    path = _schema_path(schema_id)
    record = _load_record(path)
    if not record:
        return None

    now = _now()

    if schema is not None:
        model = SchemaModel.model_validate(schema)
        versions = record.get("versions") or []
        current_version = int(record.get("version", 1))
        versions.append(
            {
                "version": current_version + 1,
                "schema": model.model_dump(),
                "updated_at": now,
            }
        )
        versions = versions[-MAX_VERSIONS:]
        record["version"] = current_version + 1
        record["versions"] = versions

    if meta.get("name") is not None or meta.get("description") is not None or meta.get("tags") is not None:
        name, description, tags = sanitize_schema_metadata(
            meta.get("name"),
            meta.get("description"),
            meta.get("tags"),
        )
        if meta.get("name") is not None:
            record["name"] = name
        if meta.get("description") is not None:
            record["description"] = description
        if meta.get("tags") is not None:
            record["tags"] = tags
    for key, value in meta.items():
        if key in ("name", "description", "tags"):
            continue
        if value is not None:
            record[key] = value

    record["updated_at"] = now
    _save_record(path, record)
    return record


def delete_custom_schema(schema_id: str) -> bool:
    """Delete a custom schema file."""
    validate_schema_id(schema_id)
    path = _schema_path(schema_id)
    if not path.exists():
        return False
    try:
        path.unlink()
        return True
    except OSError:
        return False


def list_custom_schemas(limit: int = 100) -> list[dict[str, Any]]:
    """List custom schemas, newest first."""
    dir_path = _schemas_dir()
    if not dir_path.exists():
        return []

    records: list[dict[str, Any]] = []
    for p in sorted(dir_path.glob("schema_*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if len(records) >= limit:
            break
        rec = _load_record(p)
        if not rec:
            continue
        records.append(rec)
    return records


def get_custom_schema_versions(schema_id: str) -> dict[str, Any] | None:
    """Return version numbers and timestamps for a schema."""
    record = get_custom_schema(schema_id)
    if not record:
        return None
    versions = record.get("versions") or []
    return {
        "schema_id": schema_id,
        "versions": [
            {"version": v.get("version"), "updated_at": v.get("updated_at")}
            for v in versions
        ],
        "current_version": record.get("version", 1),
    }


def get_custom_schema_version_detail(schema_id: str, version: int) -> dict[str, Any] | None:
    """Return schema definition for a specific version."""
    record = get_custom_schema(schema_id)
    if not record:
        return None
    for v in record.get("versions") or []:
        if int(v.get("version")) == int(version):
            return {
                "schema_id": schema_id,
                "version": v.get("version"),
                "schema": v.get("schema"),
                "updated_at": v.get("updated_at"),
            }
    return None


def restore_version_as_new(schema_id: str, version: int) -> dict[str, Any] | None:
    """Restore a specific version as a new revision (non-destructive). Returns updated record."""
    validate_schema_id(schema_id)
    detail = get_custom_schema_version_detail(schema_id, version)
    if not detail or not detail.get("schema"):
        return None
    return update_custom_schema(schema_id, schema=detail["schema"])


def diff_custom_schema_versions(schema_id: str, left: int, right: int) -> dict[str, Any] | None:
    """Structural diff between two schema versions with table/column-level details."""
    left_detail = get_custom_schema_version_detail(schema_id, left)
    right_detail = get_custom_schema_version_detail(schema_id, right)
    if not left_detail or not right_detail:
        return None

    left_schema = left_detail.get("schema") or {}
    right_schema = right_detail.get("schema") or {}

    left_tables = {t.get("name", ""): t for t in left_schema.get("tables", []) if t.get("name")}
    right_tables = {t.get("name", ""): t for t in right_schema.get("tables", []) if t.get("name")}

    tables_added: list[str] = []
    tables_removed: list[str] = []
    tables_modified: list[dict[str, Any]] = []

    for name in sorted(right_tables.keys() - left_tables.keys()):
        tables_added.append(name)
    for name in sorted(left_tables.keys() - right_tables.keys()):
        tables_removed.append(name)
    for name in sorted(left_tables.keys() & right_tables.keys()):
        lt, rt = left_tables[name], right_tables[name]
        left_cols = {c.get("name", ""): c for c in lt.get("columns", []) if c.get("name")}
        right_cols = {c.get("name", ""): c for c in rt.get("columns", []) if c.get("name")}
        cols_added = list(right_cols.keys() - left_cols.keys())
        cols_removed = list(left_cols.keys() - right_cols.keys())
        cols_modified = [c for c in left_cols.keys() & right_cols.keys() if left_cols[c] != right_cols[c]]
        if cols_added or cols_removed or cols_modified:
            tables_modified.append({
                "table": name,
                "columns_added": cols_added,
                "columns_removed": cols_removed,
                "columns_modified": cols_modified,
            })

    compatibility_breaking: list[dict[str, Any]] = []
    compatibility_non_breaking: list[dict[str, Any]] = []
    for table in tables_removed:
        compatibility_breaking.append(
            {"type": "table_removed", "table": table, "reason": "Table no longer exists in newer schema"}
        )
    for table in tables_added:
        compatibility_non_breaking.append(
            {"type": "table_added", "table": table, "reason": "New table is additive for producers"}
        )
    for mod in tables_modified:
        table = mod["table"]
        for col in mod.get("columns_removed", []):
            compatibility_breaking.append(
                {
                    "type": "column_removed",
                    "table": table,
                    "column": col,
                    "reason": "Column removed in newer schema",
                }
            )
        for col in mod.get("columns_added", []):
            compatibility_non_breaking.append(
                {
                    "type": "column_added",
                    "table": table,
                    "column": col,
                    "reason": "Column added in newer schema",
                }
            )
        left_cols = {
            c.get("name", ""): c for c in left_tables.get(table, {}).get("columns", []) if c.get("name")
        }
        right_cols = {
            c.get("name", ""): c for c in right_tables.get(table, {}).get("columns", []) if c.get("name")
        }
        for col in mod.get("columns_modified", []):
            left_type = left_cols.get(col, {}).get("data_type")
            right_type = right_cols.get(col, {}).get("data_type")
            if left_type != right_type:
                compatibility_breaking.append(
                    {
                        "type": "column_type_changed",
                        "table": table,
                        "column": col,
                        "from": left_type,
                        "to": right_type,
                        "reason": "Column type changed between versions",
                    }
                )
            else:
                compatibility_non_breaking.append(
                    {
                        "type": "column_modified",
                        "table": table,
                        "column": col,
                        "reason": "Column metadata changed without type change",
                    }
                )

    changed: list[dict[str, Any]] = []
    all_keys = set(left_schema.keys()) | set(right_schema.keys())
    for key in sorted(all_keys):
        if key in ("tables", "relationships"):
            continue
        l_val = left_schema.get(key)
        r_val = right_schema.get(key)
        if l_val != r_val:
            changed.append({"key": key, "left": l_val, "right": r_val})

    return {
        "schema_id": schema_id,
        "left_version": left,
        "right_version": right,
        "changed": changed,
        "tables_added": tables_added,
        "tables_removed": tables_removed,
        "tables_modified": tables_modified,
        "summary": {
            "tables_added": len(tables_added),
            "tables_removed": len(tables_removed),
            "tables_modified": len(tables_modified),
        },
        "compatibility": {
            "status": "breaking" if compatibility_breaking else "compatible",
            "breaking_changes": compatibility_breaking,
            "non_breaking_changes": compatibility_non_breaking,
            "breaking_count": len(compatibility_breaking),
            "non_breaking_count": len(compatibility_non_breaking),
        },
    }

