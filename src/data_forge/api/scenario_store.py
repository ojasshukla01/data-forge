"""Scenario persistence: JSON files in scenarios/ directory."""

import json
import time
import uuid
from pathlib import Path
from typing import Any, cast

from data_forge.config import Settings

_SCENARIOS_DIR: Path | None = None


def _scenarios_dir() -> Path:
    global _SCENARIOS_DIR
    if _SCENARIOS_DIR is None:
        root = Settings().project_root.resolve()
        _SCENARIOS_DIR = root / "scenarios"
        _SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
    return _SCENARIOS_DIR


def _scenario_path(scenario_id: str) -> Path:
    path = _scenarios_dir() / f"{scenario_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


MASKED_PLACEHOLDER = "***"


def _redact_config(config: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive keys from config."""
    out = dict(config)
    for k in list(out.keys()):
        if any(s in k.lower() for s in ("password", "secret", "token", "credential", "uri")):
            if isinstance(out.get(k), str) and out[k] and out[k] != MASKED_PLACEHOLDER:
                out[k] = MASKED_PLACEHOLDER
        elif isinstance(out.get(k), dict):
            out[k] = _redact_config(out[k])
    return out


def get_masked_field_names(config: dict[str, Any] | None, prefix: str = "") -> list[str]:
    """Return list of field names (or paths) that have masked/redacted values."""
    if not config or not isinstance(config, dict):
        return []
    names: list[str] = []
    for k, v in config.items():
        if isinstance(v, str) and v == MASKED_PLACEHOLDER:
            names.append(prefix + k if prefix else k)
        elif isinstance(v, dict):
            names.extend(get_masked_field_names(v, prefix=f"{prefix}{k}."))
    return names


def _extract_summary(config: dict[str, Any]) -> dict[str, Any]:
    """Extract a compact config summary for list views."""
    cfg = config or {}
    ps = cfg.get("pipeline_simulation") or {}
    bench = cfg.get("benchmark") or {}
    return {
        "pack": cfg.get("pack"),
        "mode": cfg.get("mode"),
        "layer": cfg.get("layer"),
        "scale": cfg.get("scale"),
        "uses_pipeline_simulation": ps.get("enabled") if isinstance(ps, dict) else False,
        "uses_benchmark": bench.get("enabled") if isinstance(bench, dict) else False,
        "privacy_mode": cfg.get("privacy_mode"),
        "export_format": cfg.get("export_format"),
    }


def _derive_badges(config: dict[str, Any]) -> list[str]:
    """Derive scenario type badges from config."""
    badges = []
    cfg = config or {}
    if cfg.get("pack"):
        badges.append("domain_pack")
    if (cfg.get("pipeline_simulation") or {}).get("enabled"):
        badges.append("pipeline_simulation")
    if (cfg.get("benchmark") or {}).get("enabled"):
        badges.append("benchmark")
    if cfg.get("privacy_mode") and cfg.get("privacy_mode") != "off":
        badges.append("privacy")
    if cfg.get("contracts"):
        badges.append("contracts")
    if cfg.get("export_dbt") or cfg.get("export_ge") or cfg.get("export_airflow"):
        badges.append("integrations")
    return badges


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
    """Create a new scenario. Returns full scenario record."""
    scenario_id = f"scenario_{uuid.uuid4().hex[:12]}"
    now = time.time()
    config_summary = _redact_config(config)
    summary = _extract_summary(config)
    badges = _derive_badges(config)
    record = {
        "id": scenario_id,
        "name": name,
        "description": description or "",
        "category": category,
        "tags": tags or [],
        "source_pack": config.get("pack"),
        "config": config,
        "config_summary": config_summary,
        "created_at": now,
        "updated_at": now,
        "created_from_run_id": created_from_run_id,
        "created_from_scenario_id": created_from_scenario_id,
        "key_features": badges,
        "uses_pipeline_simulation": summary.get("uses_pipeline_simulation", False),
        "uses_benchmark": summary.get("uses_benchmark", False),
        "uses_privacy_mode": bool(summary.get("privacy_mode") and summary.get("privacy_mode") != "off"),
        "uses_integrations": bool(
            config.get("export_dbt") or config.get("export_ge") or config.get("export_airflow")
        ),
        "version": 1,
        "versions": [{"version": 1, "config": dict(config), "updated_at": now}],
    }
    path = _scenario_path(scenario_id)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def get_scenario(scenario_id: str) -> dict[str, Any] | None:
    """Load scenario by id."""
    path = _scenario_path(scenario_id)
    if not path.exists():
        return None
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return None


MAX_VERSION_HISTORY = 20


def update_scenario(scenario_id: str, **kwargs: Any) -> dict[str, Any] | None:
    """Update scenario. Merges kwargs. Recomputes summary/badges if config changes. Appends version history."""
    record = get_scenario(scenario_id)
    if not record:
        return None
    now = time.time()
    if "config" in kwargs:
        versions = record.get("versions") or []
        current_version = record.get("version", 1)
        if versions and record.get("config") is not None:
            versions.append({
                "version": current_version,
                "config": dict(record["config"]),
                "updated_at": record.get("updated_at") or now,
            })
            versions = versions[-MAX_VERSION_HISTORY:]
        new_version = current_version + 1
        record["version"] = new_version
        record["versions"] = versions
        record["config_summary"] = _redact_config(kwargs["config"])
        summary = _extract_summary(kwargs["config"])
        record["key_features"] = _derive_badges(kwargs["config"])
        record["uses_pipeline_simulation"] = summary.get("uses_pipeline_simulation", False)
        record["uses_benchmark"] = summary.get("uses_benchmark", False)
        record["uses_privacy_mode"] = bool(
            summary.get("privacy_mode") and summary.get("privacy_mode") != "off"
        )
        record["uses_integrations"] = bool(
            kwargs["config"].get("export_dbt")
            or kwargs["config"].get("export_ge")
            or kwargs["config"].get("export_airflow")
        )
        record["source_pack"] = kwargs["config"].get("pack")
    record["updated_at"] = now
    for k, v in kwargs.items():
        if v is not None:
            record[k] = v
    path = _scenario_path(scenario_id)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def delete_scenario(scenario_id: str) -> bool:
    """Delete scenario. Returns True if deleted."""
    path = _scenario_path(scenario_id)
    if not path.exists():
        return False
    try:
        path.unlink()
        return True
    except OSError:
        return False


def list_scenarios(
    category: str | None = None,
    source_pack: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List scenarios with optional filters."""
    scenarios_dir = _scenarios_dir()
    if not scenarios_dir.exists():
        return []
    records: list[dict[str, Any]] = []
    for p in sorted(scenarios_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        if len(records) >= limit:
            break
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if category and r.get("category") != category:
            continue
        if source_pack and r.get("source_pack") != source_pack:
            continue
        if tag and tag not in (r.get("tags") or []):
            continue
        if search:
            q = search.lower()
            if q not in (r.get("name") or "").lower() and q not in (r.get("description") or "").lower():
                continue
        records.append(r)
    return records
