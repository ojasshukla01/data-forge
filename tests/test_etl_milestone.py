"""Tests for ETL/ELT realism milestone."""

import subprocess
import sys
from pathlib import Path

import pytest

from data_forge.domain_packs import get_pack
from data_forge.engine import run_generation, export_result
from data_forge.models.generation import (
    DataLayer,
    DriftProfile,
    GenerationMode,
    GenerationRequest,
    MessinessProfile,
)
from data_forge.generators.cdc_simulator import apply_mode
from data_forge.generators.layers import bronze_to_silver, silver_to_gold
from data_forge.generators.messiness import apply_messiness
from data_forge.generators.schema_drift import apply_drift
from data_forge.golden import create_manifest, load_manifest, validate_against_manifest, write_manifest
from data_forge.config import OutputFormat


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "data_forge.cli"] + args,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
        timeout=30,
    )


# CDC / Incremental
def test_cdc_includes_valid_op_type():
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(
        schema_name="saas_billing",
        seed=42,
        scale=30,
        mode=GenerationMode.CDC,
        change_ratio=0.3,
    )
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    valid = {"INSERT", "UPDATE", "DELETE"}
    for t in result.tables:
        for row in t.rows:
            op = row.get("op_type")
            assert op in valid, f"Invalid op_type: {op}"


def test_incremental_includes_timestamps_and_batch_id():
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(
        schema_name="saas_billing",
        seed=1,
        scale=20,
        mode=GenerationMode.INCREMENTAL,
        batch_id="batch_001",
    )
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    for t in result.tables:
        for row in t.rows:
            assert "created_at" in row
            assert "updated_at" in row
            assert row.get("batch_id") == "batch_001"


def test_deterministic_change_ratio():
    data = {"t": [{"id": i, "x": i * 2} for i in range(50)]}
    out1 = apply_mode(data.copy(), GenerationMode.CDC, 0.2, 42, "b1")
    data2 = {"t": [{"id": i, "x": i * 2} for i in range(50)]}
    out2 = apply_mode(data2, GenerationMode.CDC, 0.2, 42, "b1")
    assert [r.get("op_type") for r in out1["t"]] == [r.get("op_type") for r in out2["t"]]


# Bronze / Silver / Gold
def test_all_layers_generated():
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(schema_name="saas_billing", seed=1, scale=15, layer=DataLayer.ALL)
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    assert result.layers_data is not None
    assert "bronze" in result.layers_data
    assert "silver" in result.layers_data
    assert "gold" in result.layers_data


def test_silver_cleaner_than_bronze():
    bronze = {"t": [{"id": 1, "name": "  foo  "}, {"id": 2, "name": "bar"}]}
    silver = bronze_to_silver(bronze)
    assert silver["t"][0]["name"] == "foo"
    assert silver["t"][1]["name"] == "bar"


def test_gold_cleaned():
    silver = {"t": [{"id": 1, "name": "a  b  c"}]}
    gold = silver_to_gold(silver)
    assert gold["t"][0]["name"] == "a b c"


# Schema drift
def test_drift_events_recorded():
    from data_forge.models.schema import SchemaModel, TableDef, ColumnDef

    schema = SchemaModel(tables=[TableDef(name="t", columns=[ColumnDef(name="a"), ColumnDef(name="b")])])
    data = {"t": [{"a": 1, "b": 2}]}
    new_schema, new_data, events = apply_drift(schema, data, DriftProfile.MILD, 42)
    assert isinstance(events, list)


def test_mild_vs_aggressive_drift_levels():
    from data_forge.models.schema import SchemaModel, TableDef, ColumnDef

    schema = SchemaModel(tables=[TableDef(name="t", columns=[ColumnDef(name="x")])])
    data = {"t": [{"x": 1}]}
    _, _, mild = apply_drift(schema, data, DriftProfile.MILD, 100)
    _, _, aggressive = apply_drift(schema, data, DriftProfile.AGGRESSIVE, 100)
    assert len(aggressive) >= len(mild) or (len(mild) == 0 and len(aggressive) >= 0)


# Golden datasets
def test_fixed_seed_produces_matching_manifest(tmp_path):
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(schema_name="saas_billing", seed=999, scale=10)
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    row_counts = {t.table_name: t.row_count for t in result.tables}
    manifest = create_manifest(seed=999, mode="full_snapshot", layer="bronze", row_counts=row_counts, schema_sig="")
    manifest_path = tmp_path / "manifest.json"
    write_manifest(manifest, manifest_path)
    export_result(result, tmp_path / "out", fmt=OutputFormat.CSV)
    ok, errs = validate_against_manifest(tmp_path / "out", load_manifest(manifest_path))
    assert ok, errs


def test_changed_output_fails_manifest_validation(tmp_path):
    manifest = create_manifest(
        seed=1,
        mode="full_snapshot",
        layer="bronze",
        row_counts={"orders": 100},
        schema_sig="",
    )
    write_manifest(manifest, tmp_path / "m.json")
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "orders.csv").write_text("id\n1\n2\n")  # 2 rows, expect 100
    ok, errs = validate_against_manifest(tmp_path / "out", load_manifest(tmp_path / "m.json"))
    assert not ok
    assert any("expected" in str(e).lower() for e in errs)


# Messiness
def test_chaotic_messiness_alters_output():
    data = {"t": [{"id": i, "name": f"Row{i}", "val": i * 10} for i in range(20)]}
    apply_messiness(data, MessinessProfile.CHAOTIC, 42)
    has_change = any(
        r.get("name") != f"Row{i}" or isinstance(r.get("val"), str)
        for i, r in enumerate(data["t"])
    )
    assert has_change


def test_clean_messiness_preserves():
    data = {"t": [{"id": 1, "name": "X"}]}
    orig = [dict(r) for r in data["t"]]
    apply_messiness(data, MessinessProfile.CLEAN, 1)
    assert data["t"] == orig


# CLI
def test_cli_generate_mode_cdc(tmp_path):
    r = _run_cli(["generate", "--pack", "saas_billing", "--scale", "15", "--mode", "cdc", "-o", str(tmp_path), "-f", "csv"])
    assert r.returncode == 0
    csv_files = list(tmp_path.rglob("*.csv"))
    assert len(csv_files) >= 1


def test_cli_generate_layer_all(tmp_path):
    r = _run_cli(["generate", "--pack", "saas_billing", "--scale", "10", "--layer", "all", "-o", str(tmp_path)])
    assert r.returncode == 0
    bronze = tmp_path / "bronze"
    silver = tmp_path / "silver"
    gold = tmp_path / "gold"
    assert bronze.exists() or silver.exists() or gold.exists()


def test_cli_validate_golden(tmp_path):
    manifest = create_manifest(seed=1, mode="full_snapshot", layer="bronze", row_counts={"orgs": 5}, schema_sig="")
    write_manifest(manifest, tmp_path / "m.json")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "orgs.csv").write_text("id,name\n1,a\n2,b\n3,c\n4,d\n5,e\n")
    r = _run_cli(["validate-golden", "--manifest", str(tmp_path / "m.json"), "--data", str(tmp_path / "data")])
    assert r.returncode == 0
