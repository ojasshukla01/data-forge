"""Custom schema persistence: JSON files in custom_schemas/ directory.

This provides a simple, local-first registry for user-defined schemas.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

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
    return _schemas_dir() / f"{schema_id}.json"


def _now() -> float:
    return time.time()


def _new_schema_id() -> str:
    return f"schema_{uuid.uuid4().hex[:12]}"


def _load_record(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
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
    return _load_record(_schema_path(schema_id))


MAX_VERSIONS = 50


def update_custom_schema(schema_id: str, *, schema: dict[str, Any] | None = None, **meta: Any) -> dict[str, Any] | None:
    """Update metadata and/or append a new schema version."""
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

    for key, value in meta.items():
        if value is not None:
            record[key] = value

    record["updated_at"] = now
    _save_record(path, record)
    return record


def delete_custom_schema(schema_id: str) -> bool:
    """Delete a custom schema file."""
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


def diff_custom_schema_versions(schema_id: str, left: int, right: int) -> dict[str, Any] | None:
    """Naive structural diff between two schema versions."""
    left_detail = get_custom_schema_version_detail(schema_id, left)
    right_detail = get_custom_schema_version_detail(schema_id, right)
    if not left_detail or not right_detail:
        return None

    left_schema = left_detail.get("schema") or {}
    right_schema = right_detail.get("schema") or {}

    changed: list[dict[str, Any]] = []

    # Simple key-wise diff at the top level; deeper diffs can be added later.
    all_keys = set(left_schema.keys()) | set(right_schema.keys())
    for key in sorted(all_keys):
        l_val = left_schema.get(key)
        r_val = right_schema.get(key)
        if l_val != r_val:
            changed.append({"key": key, "left": l_val, "right": r_val})

    return {
        "schema_id": schema_id,
        "left_version": left,
        "right_version": right,
        "changed": changed,
    }

