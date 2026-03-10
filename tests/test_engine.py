"""Tests for generation engine."""

import pytest
from data_forge.models.generation import GenerationRequest
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
