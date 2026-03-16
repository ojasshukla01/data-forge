"""Tests for generation engine."""

import pytest
from data_forge.models.generation import DataLayer, GenerationRequest
from data_forge.models.rules import RuleSet
from data_forge.models.schema import ColumnDef, DataType, SchemaModel, TableDef
from data_forge.engine import run_generation, export_result
from data_forge.domain_packs import get_pack
from data_forge.config import OutputFormat


def test_run_generation_saas_pack():
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(schema_name="saas_billing", seed=42, scale=50)
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    assert len(result.tables) > 0
    assert result.quality_report
    total = sum(t.row_count for t in result.tables)
    assert total >= 50
    # Same seed -> same row counts
    result2 = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert [t.row_count for t in result.tables] == [t.row_count for t in result2.tables]


def test_export_result(tmp_path):
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(schema_name="saas_billing", seed=1, scale=20)
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    paths = export_result(result, tmp_path, fmt=OutputFormat.CSV)
    assert len(paths) == len(result.tables)
    for p in paths:
        assert p.exists()
        assert p.stat().st_size >= 0


def test_privacy_policy_enforced_blocks_generation():
    schema = SchemaModel(
        tables=[
            TableDef(
                name="auth",
                columns=[
                    ColumnDef(name="id", data_type=DataType.INTEGER, primary_key=True),
                    ColumnDef(name="api_token", data_type=DataType.STRING),
                ],
                primary_key=["id"],
            )
        ]
    )
    req = GenerationRequest(
        schema_name="custom",
        seed=5,
        scale=10,
        privacy_mode="strict",
        privacy_policy_mode="enforce",
        privacy_policy_fail_on_high_risk=True,
    )
    result = run_generation(req, schema=schema, rule_set=RuleSet(name="default"))
    assert result.success is False
    assert any("privacy policy blocked run" in e.lower() for e in result.errors)
    policy = result.quality_report.get("privacy_policy", {})
    assert policy.get("policy_decision") == "block"


def test_layer_all_lazy_materialization_exports_all_layers(tmp_path):
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(
        schema_name="saas_billing",
        seed=7,
        scale=30,
        layer=DataLayer.ALL,
        layer_materialization="lazy",
    )
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    assert result.layers_data is not None
    assert "bronze" in result.layers_data
    assert "silver" not in result.layers_data
    assert "gold" not in result.layers_data
    assert (
        result.quality_report.get("materialization", {}).get("layer_materialization")
        == "lazy"
    )
    paths = export_result(result, tmp_path, fmt=OutputFormat.CSV)
    path_strs = {str(p).replace("\\", "/") for p in paths}
    assert any("/bronze/" in p for p in path_strs)
    assert any("/silver/" in p for p in path_strs)
    assert any("/gold/" in p for p in path_strs)
