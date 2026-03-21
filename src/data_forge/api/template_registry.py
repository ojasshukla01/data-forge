"""Template registry: user preferences for templates (hide built-in, user-added templates).

Stores which built-in packs to hide and which custom schemas are promoted as templates.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from data_forge.config import Settings

_REGISTRY_PATH: Path | None = None


def _registry_path() -> Path:
    global _REGISTRY_PATH
    if _REGISTRY_PATH is None:
        root = Settings().project_root.resolve()
        _REGISTRY_PATH = root / "template_registry.json"
    return _REGISTRY_PATH


def _load() -> dict[str, Any]:
    path = _registry_path()
    if not path.exists():
        return {"hidden_builtin": [], "user_template_ids": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "hidden_builtin": data.get("hidden_builtin", []),
            "user_template_ids": data.get("user_template_ids", []),
        }
    except (json.JSONDecodeError, OSError):
        return {"hidden_builtin": [], "user_template_ids": []}


def _save(data: dict[str, Any]) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_hidden_builtin() -> list[str]:
    """Return pack IDs that the user has hidden."""
    return list(_load()["hidden_builtin"])


def get_user_template_ids() -> list[str]:
    """Return custom schema IDs that are user templates."""
    return list(_load()["user_template_ids"])


def hide_builtin(pack_id: str) -> bool:
    """Hide a built-in pack from the user's template list."""
    data = _load()
    if pack_id not in data["hidden_builtin"]:
        data["hidden_builtin"].append(pack_id)
        _save(data)
        return True
    return False


def unhide_builtin(pack_id: str) -> bool:
    """Unhide a built-in pack."""
    data = _load()
    if pack_id in data["hidden_builtin"]:
        data["hidden_builtin"].remove(pack_id)
        _save(data)
        return True
    return False


def add_user_template(schema_id: str) -> bool:
    """Add a custom schema as a user template."""
    data = _load()
    if schema_id not in data["user_template_ids"]:
        data["user_template_ids"].append(schema_id)
        _save(data)
        return True
    return False


def remove_user_template(schema_id: str) -> bool:
    """Remove a custom schema from user templates (schema itself is not deleted)."""
    data = _load()
    if schema_id in data["user_template_ids"]:
        data["user_template_ids"].remove(schema_id)
        _save(data)
        return True
    return False


def is_builtin_hidden(pack_id: str) -> bool:
    """Check if a built-in pack is hidden."""
    return pack_id in get_hidden_builtin()


def is_user_template(schema_id: str) -> bool:
    """Check if a custom schema is a user template."""
    return schema_id in get_user_template_ids()
