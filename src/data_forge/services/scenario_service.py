"""Scenario service: thin facade over scenario store for API/CLI use."""

from typing import Any

from data_forge.storage import get_scenario_store


def create_scenario(
    name: str,
    config: dict[str, Any],
    *,
    description: str = "",
    category: str = "custom",
    tags: list[str] | None = None,
    created_from_run_id: str | None = None,
    created_from_scenario_id: str | None = None,
) -> dict[str, Any]:
    """Create a new scenario."""
    return get_scenario_store().create_scenario(
        name=name,
        config=config,
        description=description,
        category=category,
        tags=tags,
        created_from_run_id=created_from_run_id,
        created_from_scenario_id=created_from_scenario_id,
    )


def get_scenario(scenario_id: str) -> dict[str, Any] | None:
    """Get scenario by id."""
    return get_scenario_store().get_scenario(scenario_id)


def update_scenario(scenario_id: str, **kwargs: Any) -> dict[str, Any] | None:
    """Update scenario."""
    return get_scenario_store().update_scenario(scenario_id, **kwargs)


def delete_scenario(scenario_id: str) -> bool:
    """Delete scenario."""
    return get_scenario_store().delete_scenario(scenario_id)


def list_scenarios(
    *,
    category: str | None = None,
    source_pack: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List scenarios with optional filters."""
    return get_scenario_store().list_scenarios(
        category=category,
        source_pack=source_pack,
        tag=tag,
        search=search,
        limit=limit,
    )


def get_masked_field_names(config: dict[str, Any] | None, prefix: str = "") -> list[str]:
    """Return list of config keys that contain masked/redacted values."""
    return get_scenario_store().get_masked_field_names(config, prefix=prefix)


def get_scenario_versions(scenario_id: str) -> list[dict[str, Any]]:
    """Return version history: list of { version, updated_at }."""
    record = get_scenario_store().get_scenario(scenario_id)
    if not record:
        return []
    versions = record.get("versions") or []
    current = record.get("version", 1)
    out = [{"version": current, "updated_at": record.get("updated_at")}]
    seen = {current}
    for v in reversed(versions):
        n = v.get("version")
        if n is not None and n not in seen:
            seen.add(n)
            out.append({"version": n, "updated_at": v.get("updated_at")})
    return out


def get_scenario_version_config(scenario_id: str, version: int) -> dict[str, Any] | None:
    """Get config snapshot for a specific version. Version 0 or current = current config."""
    record = get_scenario_store().get_scenario(scenario_id)
    if not record:
        return None
    current = record.get("version", 1)
    if version == 0 or version == current:
        return record.get("config")
    for v in reversed(record.get("versions") or []):
        if v.get("version") == version:
            return v.get("config")
    return None


def diff_scenario_versions(
    scenario_id: str, left_version: int, right_version: int
) -> dict[str, Any] | None:
    """Compare two scenario versions. Returns { changed: [ { key, left, right } ], ... }."""
    record = get_scenario_store().get_scenario(scenario_id)
    if not record:
        return None
    left_cfg = get_scenario_version_config(scenario_id, left_version) if left_version else record.get("config")
    right_cfg = get_scenario_version_config(scenario_id, right_version) if right_version else record.get("config")
    if not left_cfg or not right_cfg:
        return None

    def _flatten(d: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
        out: list[tuple[str, Any]] = []
        for k, v in d.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict) and not (v and any(isinstance(vv, (dict, list)) for vv in v.values())):
                out.extend(_flatten(v, path))
            else:
                out.append((path, v))
        return out

    left_flat = dict(_flatten(left_cfg))
    right_flat = dict(_flatten(right_cfg))
    all_keys = sorted(set(left_flat) | set(right_flat))
    changed = []
    for key in all_keys:
        lv = left_flat.get(key)
        rv = right_flat.get(key)
        if lv != rv:
            changed.append({"key": key, "left": lv, "right": rv})
    return {"left_version": left_version, "right_version": right_version, "changed": changed}
