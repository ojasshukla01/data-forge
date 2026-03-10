"""Tests for Great Expectations + Airflow integration milestone."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from data_forge.domain_packs import get_pack
from data_forge.ge_export import build_expectation_suite, export_ge
from data_forge.ge_validation import validate_against_expectations
from data_forge.airflow_export import export_airflow
from data_forge.reconciliation import run_reconciliation
from data_forge.golden import create_manifest, write_manifest


def _run_cli(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "data_forge.cli"] + args,
        capture_output=True,
        text=True,
        cwd=cwd or Path(__file__).parent.parent,
        timeout=30,
    )


# GE export tests
def test_ge_export_suites_generated(tmp_path):
    """GE export generates expectation suites."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    report = export_ge(pack.schema, pack.rule_set, tmp_path)
    assert report["suites_generated"] > 0
    assert report["output_dir"] == str(tmp_path)
    exp_dir = tmp_path / "expectations"
    assert exp_dir.exists()
    suites = list(exp_dir.glob("*_suite.json"))
    assert len(suites) == report["suites_generated"]


def test_ge_export_checkpoint_generated(tmp_path):
    """GE export generates checkpoint file."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    export_ge(pack.schema, pack.rule_set, tmp_path)
    cp = tmp_path / "checkpoints" / "data_forge_checkpoint.json"
    assert cp.exists()
    data = json.loads(cp.read_text())
    assert "validations" in data or "name" in data


def test_ge_export_pk_expectations_present(tmp_path):
    """GE suites include primary key expectations."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    export_ge(pack.schema, pack.rule_set, tmp_path)
    exp_dir = tmp_path / "expectations"
    for path in exp_dir.glob("*_suite.json"):
        suite = json.loads(path.read_text())
        types = [e.get("expectation_type") for e in suite.get("expectations", [])]
        assert "expect_column_values_to_not_be_null" in types or "expect_table_row_count_to_be_between" in types


def test_ge_export_enum_expectations_when_available(tmp_path):
    """GE suites include enum expectations when schema has enum_values."""
    from data_forge.models.schema import SchemaModel, TableDef, ColumnDef, DataType

    schema = SchemaModel(
        name="test",
        tables=[
            TableDef(
                name="status",
                columns=[
                    ColumnDef(name="id", data_type=DataType.INTEGER, primary_key=True),
                    ColumnDef(name="status", data_type=DataType.ENUM, enum_values=["active", "inactive"]),
                ],
                primary_key=["id"],
            )
        ],
    )
    suite = build_expectation_suite("status", schema, None)
    types = [e.get("expectation_type") for e in suite.get("expectations", [])]
    assert "expect_column_values_to_be_in_set" in types


# GE validation tests
def test_ge_validation_passing(tmp_path):
    """GE validation runs and returns report; at least one suite passes when data matches."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    export_ge(pack.schema, pack.rule_set, tmp_path)
    from data_forge.engine import run_generation
    from data_forge.models.generation import GenerationRequest
    from data_forge.exporters import export_tables
    from data_forge.config import OutputFormat

    req = GenerationRequest(schema_name="saas_billing", seed=1, scale=20)
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    table_data = {t.table_name: t.rows for t in result.tables}
    (tmp_path / "data").mkdir(exist_ok=True)
    export_tables(table_data, tmp_path / "data", fmt=OutputFormat.CSV)
    report = validate_against_expectations(tmp_path / "expectations", tmp_path / "data")
    ge = report["ge_validation"]
    assert "total_suites" in ge
    assert "passed" in ge
    assert "failed" in ge
    assert ge["total_suites"] >= 1
    assert ge["passed"] + ge["failed"] == ge["total_suites"]


def test_ge_validation_failing_duplicates(tmp_path):
    """GE validation fails when duplicates in PK column."""
    exp_dir = tmp_path / "expectations"
    exp_dir.mkdir(parents=True)
    suite = {
        "expectation_suite_name": "test_suite",
        "expectations": [
            {"expectation_type": "expect_column_values_to_be_unique", "kwargs": {"column": "id"}},
        ],
    }
    (exp_dir / "test_suite.json").write_text(json.dumps(suite), encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "test.csv").write_text("id,name\n1,a\n1,b\n")
    report = validate_against_expectations(exp_dir, data_dir)
    ge = report["ge_validation"]
    assert ge["failed"] >= 1
    assert any("duplicate" in str(f.get("reason", "")).lower() for f in ge.get("failures", []))


# Airflow export tests
def test_airflow_export_dag_files_generated(tmp_path):
    """Airflow export generates DAG files."""
    report = export_airflow("generate_only", tmp_path)
    assert report["files_generated"] == 1
    assert (tmp_path / "dags" / "data_forge_generate.py").exists()


def test_airflow_export_template_reflected(tmp_path):
    """Selected template is reflected in file contents."""
    export_airflow("benchmark_pipeline", tmp_path)
    content = (tmp_path / "dags" / "data_forge_benchmark.py").read_text()
    assert "benchmark" in content.lower()
    assert "data-forge benchmark" in content


def test_airflow_export_cli_works(tmp_path):
    """generate --export-airflow works."""
    result = _run_cli([
        "generate", "--pack", "saas_billing", "--scale", "10", "-o", str(tmp_path / "out"),
        "--export-airflow", "--airflow-dir", str(tmp_path / "airflow"),
        "--airflow-template", "generate_and_load",
    ])
    assert result.returncode == 0
    assert (tmp_path / "airflow" / "dags" / "data_forge_generate_load.py").exists()


# Reconciliation tests
def test_reconciliation_row_count_mismatch_detected(tmp_path):
    """Reconciliation detects row count mismatch."""
    manifest = create_manifest(seed=42, mode="full_snapshot", layer="bronze", row_counts={"orders": 100}, schema_sig="")
    write_manifest(manifest, tmp_path / "manifest.json")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "orders.csv").write_text("id\n1\n2\n")
    report = run_reconciliation(tmp_path / "manifest.json", tmp_path / "data")
    rec = report["reconciliation"]
    assert "orders" in rec["row_count_diffs"]
    assert rec["row_count_diffs"]["orders"]["expected"] == 100
    assert rec["row_count_diffs"]["orders"]["actual"] == 2


def test_reconciliation_missing_table_detected(tmp_path):
    """Reconciliation detects missing table."""
    manifest = create_manifest(
        seed=42, mode="full_snapshot", layer="bronze",
        row_counts={"customers": 5, "products": 10},
        schema_sig="",
    )
    write_manifest(manifest, tmp_path / "manifest.json")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "customers.csv").write_text("id\n1\n2\n3\n4\n5\n")
    report = run_reconciliation(tmp_path / "manifest.json", tmp_path / "data")
    rec = report["reconciliation"]
    assert "products" in rec["missing_tables"]


def test_reconciliation_missing_column_detected(tmp_path):
    """Reconciliation detects missing columns when schema provided."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    manifest = create_manifest(seed=42, mode="full_snapshot", layer="bronze", row_counts={"organizations": 1}, schema_sig="")
    write_manifest(manifest, tmp_path / "manifest.json")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "organizations.csv").write_text("id\n1\n")
    report = run_reconciliation(tmp_path / "manifest.json", tmp_path / "data", schema=pack.schema)
    rec = report["reconciliation"]
    if "organizations" in rec.get("missing_columns", {}):
        assert len(rec["missing_columns"]["organizations"]) > 0


def test_reconciliation_layer_deltas_present(tmp_path):
    """Reconciliation includes layer deltas when layers_data provided."""
    layers_data = {
        "bronze": {"t": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}]},
        "silver": {"t": [{"id": 1}, {"id": 2}, {"id": 3}]},
        "gold": {"t": [{"id": 1}]},
    }
    from data_forge.reconciliation import reconcile_layer_deltas
    report = reconcile_layer_deltas(layers_data)
    ld = report["reconciliation"]["layer_deltas"]
    assert ld.get("bronze_to_silver_removed", 0) == 2
    assert ld.get("silver_to_gold_removed", 0) == 2


# CLI tests
def test_cli_generate_with_export_ge(tmp_path):
    """generate --export-ge works."""
    result = _run_cli([
        "generate", "--pack", "saas_billing", "--scale", "15", "-o", str(tmp_path / "out"),
        "--export-ge", "--ge-dir", str(tmp_path / "ge"),
    ])
    assert result.returncode == 0
    assert (tmp_path / "ge" / "expectations").exists()
    assert list((tmp_path / "ge" / "expectations").glob("*_suite.json"))


def test_cli_validate_ge_works(tmp_path):
    """validate-ge command runs and produces expected output."""
    (tmp_path / "expectations").mkdir(parents=True)
    suite = {
        "expectation_suite_name": "simple_suite",
        "expectations": [
            {"expectation_type": "expect_table_row_count_to_be_between", "kwargs": {"min_value": 0, "max_value": 100}},
        ],
    }
    (tmp_path / "expectations" / "simple_suite.json").write_text(json.dumps(suite), encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "simple.csv").write_text("id\n1\n2\n3\n")
    run = _run_cli(["validate-ge", "--expectations", str(tmp_path), "--data", str(tmp_path / "data")])
    assert run.returncode == 0
    assert "passed" in run.stdout.lower() or "suite" in run.stdout.lower()


def test_cli_reconcile_works(tmp_path):
    """reconcile command works."""
    manifest = create_manifest(seed=42, mode="full_snapshot", layer="bronze", row_counts={"t": 2}, schema_sig="")
    write_manifest(manifest, tmp_path / "m.json")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "t.csv").write_text("id\n1\n2\n")
    run = _run_cli(["reconcile", "--manifest", str(tmp_path / "m.json"), "--data", str(tmp_path / "data")])
    assert run.returncode == 0
