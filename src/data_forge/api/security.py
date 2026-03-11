"""Security helpers: schema ID validation, path safety, input sanitization."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# schema_id must start with schema_, no path traversal chars
VALID_SCHEMA_ID = re.compile(r"^schema_[a-zA-Z0-9_-]{1,52}$")
MAX_NAME_LEN = 500
MAX_DESC_LEN = 2000
MAX_TAG_LEN = 50
MAX_TAGS = 50
MAX_SCHEMA_BODY_BYTES = 512 * 1024  # 512KB for custom schema JSON


def validate_schema_id(schema_id: str) -> None:
    """Ensure schema_id is safe (no path traversal)."""
    if not schema_id:
        raise ValueError("schema_id is required")
    if not isinstance(schema_id, str):
        raise ValueError("schema_id must be a string")
    if "/" in schema_id or "\\" in schema_id or ".." in schema_id:
        raise ValueError("Invalid schema_id: path traversal not allowed")
    if len(schema_id) > 64:
        raise ValueError("schema_id too long")
    if not VALID_SCHEMA_ID.match(schema_id):
        raise ValueError("Invalid schema_id format (expected schema_<alphanumeric>)")


def sanitize_schema_metadata(
    name: str | None,
    description: str | None,
    tags: list[str] | None,
) -> tuple[str, str, list[str]]:
    """Sanitize name, description, tags for storage."""
    name = (name or "").strip()[:MAX_NAME_LEN]
    description = (description or "").strip()[:MAX_DESC_LEN]
    if tags is None:
        tags = []
    tags = [str(t).strip()[:MAX_TAG_LEN] for t in tags if t][:MAX_TAGS]
    return name, description, tags


def sanitize_json_schema(obj: Any) -> dict[str, Any]:
    """
    Ensure schema object is a dict with expected keys only.
    Deep nesting is limited to prevent DoS.
    """
    if not isinstance(obj, dict):
        raise ValueError("Schema must be a JSON object")
    # Only allow known top-level keys
    allowed = {"name", "tables", "relationships", "source", "source_type"}
    return {k: v for k, v in obj.items() if k in allowed}


def validate_schema_body_size(schema: dict[str, Any]) -> None:
    """Reject schema bodies exceeding MAX_SCHEMA_BODY_BYTES."""
    try:
        size = len(json.dumps(schema).encode("utf-8"))
    except (TypeError, ValueError) as e:
        raise ValueError("Schema must be JSON-serializable") from e
    if size > MAX_SCHEMA_BODY_BYTES:
        raise ValueError(
            f"Schema body too large ({size} bytes, max {MAX_SCHEMA_BODY_BYTES})"
        )


def ensure_custom_schema_path_safe(base_dir: Path, schema_id: str) -> Path:
    """Resolve schema file path and ensure it stays inside base_dir."""
    validate_schema_id(schema_id)
    path = (base_dir / f"{schema_id}.json").resolve()
    try:
        path.relative_to(base_dir.resolve())
    except ValueError as err:
        raise ValueError("Path would escape custom_schemas directory") from err
    return path
