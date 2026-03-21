"""Provenance durability: lineage and manifest when custom schema is deleted or missing."""

from unittest.mock import patch

from data_forge.services.lineage_service import get_run_lineage


def test_lineage_schema_missing_when_custom_schema_deleted() -> None:
    """When run used a custom schema that no longer exists, lineage has schema_missing True and preserved metadata."""
    run_record = {
        "run_id": "run_test1",
        "run_type": "generate",
        "config": {"custom_schema_id": "schema_deleted123", "pack": None},
        "config_summary": {},
        "result_summary": {
            "custom_schema_id": "schema_deleted123",
            "custom_schema_version": 2,
            "custom_schema_name": "My Deleted Schema",
            "custom_schema_snapshot_hash": "a1b2c3d4e5f6",
            "custom_schema_table_names": ["users", "orders"],
            "artifact_run_id": "run_test1",
        },
        "selected_pack": None,
    }

    with patch("data_forge.services.lineage_service.get_run", return_value=run_record):
        with patch("data_forge.services.lineage_service.get_scenario", return_value=None):
            with patch("data_forge.services.lineage_service.custom_schema_store") as mock_store:
                mock_store.get_custom_schema.return_value = None
                lineage = get_run_lineage("run_test1")
    assert lineage is not None
    assert lineage.get("schema_missing") is True
    assert "schema_missing_message" in lineage
    assert "no longer available" in lineage["schema_missing_message"]
    assert lineage.get("custom_schema_id") == "schema_deleted123"
    assert lineage.get("custom_schema_name") == "My Deleted Schema"
    assert lineage.get("custom_schema_version") == 2
    assert lineage.get("custom_schema_snapshot_hash") == "a1b2c3d4e5f6"
    assert lineage.get("custom_schema_table_names") == ["users", "orders"]


def test_lineage_schema_present_when_custom_schema_exists() -> None:
    """When custom schema still exists, lineage has schema_missing False."""
    run_record = {
        "run_id": "run_test2",
        "run_type": "generate",
        "config": {"custom_schema_id": "schema_still_here", "pack": None},
        "config_summary": {},
        "result_summary": {
            "custom_schema_id": "schema_still_here",
            "custom_schema_name": "Existing Schema",
            "artifact_run_id": "run_test2",
        },
        "selected_pack": None,
    }

    with patch("data_forge.services.lineage_service.get_run", return_value=run_record):
        with patch("data_forge.services.lineage_service.get_scenario", return_value=None):
            with patch("data_forge.services.lineage_service.custom_schema_store") as mock_store:
                mock_store.get_custom_schema.return_value = {"id": "schema_still_here", "name": "Existing Schema"}
                lineage = get_run_lineage("run_test2")
    assert lineage is not None
    assert lineage.get("schema_missing") is False
    assert lineage.get("custom_schema_id") == "schema_still_here"
    assert lineage.get("custom_schema_name") == "Existing Schema"
