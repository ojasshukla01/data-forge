"""Validate example scenario JSON files in examples/scenarios/."""

import json
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples" / "scenarios"


def _scenario_files():
    if not EXAMPLES_DIR.exists():
        return []
    return list(EXAMPLES_DIR.glob("*.json"))


@pytest.mark.parametrize("path", _scenario_files(), ids=lambda p: p.name)
def test_example_scenario_valid_structure(path: Path) -> None:
    """Each example scenario JSON has required fields and valid structure."""
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert isinstance(data, dict), "Scenario must be a JSON object"
    assert "name" in data and data["name"], "Scenario must have a non-empty name"
    assert "config" in data and isinstance(data["config"], dict), "Scenario must have a config object"
    config = data["config"]
    assert "pack" in config and config["pack"], "config.pack is required"
    # Categories are optional but if present should be valid
    if "category" in data:
        valid = {"quick_start", "testing", "pipeline_simulation", "warehouse_benchmark", "privacy_uat", "contracts", "custom"}
        assert data["category"] in valid, f"category must be one of {valid}"
