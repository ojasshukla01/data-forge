"""Tests for run manifest and lineage with custom schema provenance."""

from data_forge.models.run_manifest import build_run_manifest
from data_forge.services.lineage_service import get_run_lineage


def test_build_run_manifest_includes_custom_schema_fields() -> None:
    """Manifest includes custom_schema_id, custom_schema_version, schema_source_type when schema-driven."""
    config = {
        "pack": None,
        "custom_schema_id": "schema_abc123",
        "custom_schema_version": 2,
        "seed": 42,
        "scale": 100,
    }
    m = build_run_manifest("run_1", "generate", config)
    assert m["custom_schema_id"] == "schema_abc123"
    assert m["custom_schema_version"] == 2
    assert m["schema_source_type"] == "custom_schema"
    assert m["pack"] is None


def test_build_run_manifest_includes_custom_schema_name_for_provenance_durability() -> None:
    """Manifest includes custom_schema_name when provided for provenance durability."""
    config = {
        "pack": None,
        "custom_schema_id": "schema_prov",
        "seed": 42,
    }
    m = build_run_manifest("run_prov", "generate", config, custom_schema_name="My Schema")
    assert m["custom_schema_id"] == "schema_prov"
    assert m["custom_schema_name"] == "My Schema"


def test_build_run_manifest_pack_source() -> None:
    """Manifest uses schema_source_type=pack when no custom_schema_id."""
    config = {"pack": "saas_billing", "seed": 42}
    m = build_run_manifest("run_2", "generate", config)
    assert m["schema_source_type"] == "pack"
    assert m["pack"] == "saas_billing"
    assert m.get("custom_schema_id") is None
    assert m.get("custom_schema_version") is None


def test_build_run_manifest_backward_compatible() -> None:
    """Legacy config without custom schema fields still works."""
    config = {"pack": "ecommerce", "seed": 1, "scale": 10}
    m = build_run_manifest("run_3", "generate", config)
    assert m["run_id"] == "run_3"
    assert m["schema_source_type"] == "pack"


def test_lineage_includes_custom_schema_when_in_config() -> None:
    """Lineage returns custom_schema_id when run config has it."""
    from unittest.mock import patch
    mock_record = {
        "id": "run_test",
        "run_type": "generate",
        "config": {"custom_schema_id": "schema_xyz", "pack": None},
        "config_summary": {"custom_schema_id": "schema_xyz"},
        "selected_pack": None,
        "result_summary": {"custom_schema_version": 2, "artifact_run_id": "run_test", "output_dir": "/out"},
        "source_scenario_id": None,
    }
    with patch("data_forge.services.lineage_service.get_run", return_value=mock_record):
        with patch("data_forge.services.lineage_service.get_scenario", return_value=None):
            lineage = get_run_lineage("run_test")
    assert lineage is not None
    assert lineage["custom_schema_id"] == "schema_xyz"
    assert lineage["custom_schema_version"] == 2
    assert lineage["schema_source_type"] == "custom_schema"


def test_lineage_includes_custom_schema_name_when_in_result_summary() -> None:
    """Lineage returns custom_schema_name when result_summary has it (provenance durability)."""
    from unittest.mock import patch
    mock_record = {
        "id": "run_named",
        "run_type": "generate",
        "config": {"custom_schema_id": "schema_named", "pack": None},
        "result_summary": {"custom_schema_version": 1, "custom_schema_name": "Deleted Schema", "artifact_run_id": "run_named"},
        "source_scenario_id": None,
    }
    with patch("data_forge.services.lineage_service.get_run", return_value=mock_record):
        with patch("data_forge.services.lineage_service.get_scenario", return_value=None):
            lineage = get_run_lineage("run_named")
    assert lineage is not None
    assert lineage["custom_schema_id"] == "schema_named"
    assert lineage["custom_schema_name"] == "Deleted Schema"
