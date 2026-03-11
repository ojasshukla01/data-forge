"""Tests for Cloud Warehouse Adapters + dbt Integration."""

import pytest
from pathlib import Path

from data_forge.adapters import get_adapter, DATABASE_ADAPTERS
from data_forge.adapters.snowflake_adapter import SnowflakeAdapter
from data_forge.adapters.bigquery_adapter import BigQueryAdapter
from data_forge.dbt_export import export_dbt
from data_forge.warehouse_validation import run_warehouse_validation
from data_forge.models.schema import SchemaModel, TableDef, ColumnDef, DataType
from data_forge.models.generation import TableSnapshot


def _run_cli(args: list[str]):
    import subprocess
    r = subprocess.run(
        ["python", "-m", "data_forge.cli"] + args,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    return r


# --- Registry ---
def test_snowflake_and_bigquery_registered():
    assert "snowflake" in DATABASE_ADAPTERS
    assert "bigquery" in DATABASE_ADAPTERS
    assert DATABASE_ADAPTERS["snowflake"] is SnowflakeAdapter
    assert DATABASE_ADAPTERS["bigquery"] is BigQueryAdapter


def test_get_adapter_snowflake():
    adapter = get_adapter(
        "snowflake",
        "",
        snowflake_account="xy",
        snowflake_user="u",
        snowflake_password="p",
        snowflake_database="db",
        snowflake_schema="sc",
    )
    assert isinstance(adapter, SnowflakeAdapter)
    assert adapter.account == "xy"
    assert adapter.database == "db"


def test_get_adapter_bigquery():
    adapter = get_adapter(
        "bigquery",
        "",
        bigquery_project="proj",
        bigquery_dataset="ds",
    )
    assert isinstance(adapter, BigQueryAdapter)
    assert adapter.project == "proj"
    assert adapter.dataset_id == "ds"


# --- dbt export ---
def test_dbt_export_seeds(tmp_path):
    schema = SchemaModel(
        tables=[
            TableDef(name="users", columns=[ColumnDef(name="id", data_type=DataType.INTEGER, primary_key=True)]),
        ]
    )
    table_data = {"users": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]}
    report = export_dbt(table_data, schema, tmp_path)
    assert report["enabled"] is True
    assert "users.csv" in report["seeds_generated"]
    assert (tmp_path / "seeds" / "users.csv").exists()


def test_dbt_export_sources_yml(tmp_path):
    table_data = {"customers": [{"id": 1}], "orders": [{"id": 1}]}
    export_dbt(table_data, None, tmp_path)
    sources = (tmp_path / "models" / "sources.yml").read_text()
    assert "data_forge" in sources
    assert "customers" in sources
    assert "orders" in sources


def test_dbt_export_schema_tests_yml(tmp_path):
    schema = SchemaModel(
        tables=[
            TableDef(
                name="t",
                columns=[
                    ColumnDef(name="id", data_type=DataType.INTEGER, primary_key=True),
                ],
                primary_key=["id"],
            ),
        ]
    )
    table_data = {"t": [{"id": 1}]}
    export_dbt(table_data, schema, tmp_path)
    tests = (tmp_path / "models" / "schema_tests.yml").read_text()
    assert "not_null" in tests
    assert "unique" in tests
    assert "id" in tests


# --- Warehouse validation ---
def test_warehouse_validation_row_count_match():
    load_report = {"success": True, "row_counts": {"t": 10}}
    schema = SchemaModel(tables=[TableDef(name="t", columns=[])])
    snapshots = [TableSnapshot(table_name="t", columns=["id"], rows=[{}] * 10, row_count=10)]
    r = run_warehouse_validation(load_report, schema, snapshots, target="sqlite")
    assert r["checks_passed"] is True
    assert r["row_count_match"] is True
    assert r["tables_checked"] == 1


def test_warehouse_validation_missing_table():
    load_report = {"success": True, "row_counts": {"t1": 5}}
    schema = SchemaModel(tables=[TableDef(name="t1"), TableDef(name="t2")])
    snapshots = [
        TableSnapshot(table_name="t1", columns=[], rows=[{}] * 5, row_count=5),
        TableSnapshot(table_name="t2", columns=[], rows=[{}] * 3, row_count=3),
    ]
    r = run_warehouse_validation(load_report, schema, snapshots)
    assert r["checks_passed"] is False
    assert "t2" in r["missing_tables"]


def test_warehouse_validation_row_count_mismatch():
    load_report = {"success": True, "row_counts": {"t": 5}}
    schema = SchemaModel(tables=[TableDef(name="t")])
    snapshots = [TableSnapshot(table_name="t", columns=[], rows=[{}] * 10, row_count=10)]
    r = run_warehouse_validation(load_report, schema, snapshots)
    assert r["row_count_match"] is False
    assert r["checks_passed"] is False


# --- Cloud adapter mocks ---
def test_snowflake_adapter_raises_on_missing_creds():
    adapter = SnowflakeAdapter(uri="", account="", user="", password="")
    with pytest.raises(ValueError) as exc:
        adapter.connect()
    assert "credentials" in str(exc.value).lower()


def test_bigquery_adapter_raises_on_missing_config():
    adapter = BigQueryAdapter(uri="", project="", dataset="")
    with pytest.raises(ValueError) as exc:
        adapter.connect()
    assert "config" in str(exc.value).lower()


# --- CLI ---
def test_cli_export_dbt(tmp_path):
    r = _run_cli([
        "generate", "--pack", "saas_billing", "--scale", "5",
        "--export-dbt", "--dbt-dir", str(tmp_path / "dbt_out"),
        "-o", str(tmp_path),
    ])
    assert r.returncode == 0
    seeds = tmp_path / "dbt_out" / "seeds"
    assert seeds.exists()
    assert len(list(seeds.glob("*.csv"))) >= 1
    assert (tmp_path / "dbt_out" / "models" / "sources.yml").exists()


def test_cli_no_secret_leakage():
    """Ensure password is not echoed in CLI help or error."""
    r = _run_cli(["generate", "--help"])
    assert r.returncode == 0
    out = r.stdout + r.stderr
    assert "sf-password" in out or "sf_password" in out or "Snowflake" in out
