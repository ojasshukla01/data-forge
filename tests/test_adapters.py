"""Tests for database adapters."""

import pytest
from pathlib import Path

from data_forge.models.schema import SchemaModel, TableDef, ColumnDef, DataType
from data_forge.adapters import get_adapter, AdapterNotSupportedError
from data_forge.adapters.sqlite_adapter import SQLiteAdapter
from data_forge.adapters.duckdb_adapter import DuckDBAdapter


@pytest.fixture
def simple_schema():
    return SchemaModel(
        name="test",
        tables=[
            TableDef(
                name="users",
                columns=[
                    ColumnDef(name="id", data_type=DataType.INTEGER, primary_key=True),
                    ColumnDef(name="name", data_type=DataType.STRING),
                ],
                primary_key=["id"],
            ),
            TableDef(
                name="orders",
                columns=[
                    ColumnDef(name="id", data_type=DataType.INTEGER, primary_key=True),
                    ColumnDef(name="user_id", data_type=DataType.INTEGER),
                    ColumnDef(name="total", data_type=DataType.FLOAT),
                ],
                primary_key=["id"],
            ),
        ],
    )


@pytest.fixture
def sample_rows():
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]


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
def test_get_adapter_returns_sqlite():
    adapter = get_adapter("sqlite", ":memory:")
    assert isinstance(adapter, SQLiteAdapter)


def test_get_adapter_raises_for_unknown():
    with pytest.raises(AdapterNotSupportedError) as exc:
        get_adapter("mongodb", "fake://uri")
    assert "mongodb" in str(exc.value)
    assert "sqlite" in str(exc.value).lower()


# --- SQLite ---
def test_sqlite_create_tables(tmp_path, simple_schema):
    uri = str(tmp_path / "test.db")
    with SQLiteAdapter(uri) as adapter:
        adapter.create_schema(simple_schema)
        adapter.create_tables(simple_schema)
    import sqlite3
    conn = sqlite3.connect(uri)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()
    assert "users" in tables
    assert "orders" in tables


def test_sqlite_load_data(tmp_path, simple_schema, sample_rows):
    uri = str(tmp_path / "test.db")
    with SQLiteAdapter(uri) as adapter:
        adapter.create_schema(simple_schema)
        adapter.create_tables(simple_schema)
        n = adapter.load_table("users", sample_rows)
    assert n == 2
    import sqlite3
    conn = sqlite3.connect(uri)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    assert cur.fetchone()[0] == 2
    conn.close()


def test_sqlite_validate_load(tmp_path, simple_schema, sample_rows):
    uri = str(tmp_path / "test.db")
    with SQLiteAdapter(uri) as adapter:
        adapter.create_schema(simple_schema)
        adapter.create_tables(simple_schema)
        adapter.load_table("users", sample_rows)
        result = adapter.validate_load()
    assert result["success"] is True
    assert result["actual"]["users"] == 2


# --- DuckDB ---
def test_duckdb_create_tables(tmp_path, simple_schema):
    uri = str(tmp_path / "test.duckdb")
    with DuckDBAdapter(uri) as adapter:
        adapter.create_schema(simple_schema)
        adapter.create_tables(simple_schema)
    import duckdb
    conn = duckdb.connect(uri)
    tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
    conn.close()
    names = [t[0] for t in tables]
    assert "users" in names
    assert "orders" in names


def test_duckdb_load_data(tmp_path, simple_schema, sample_rows):
    uri = str(tmp_path / "test.duckdb")
    with DuckDBAdapter(uri) as adapter:
        adapter.create_schema(simple_schema)
        adapter.create_tables(simple_schema)
        n = adapter.load_table("users", sample_rows)
    assert n == 2
    import duckdb
    conn = duckdb.connect(uri)
    r = conn.execute("SELECT COUNT(*) FROM users").fetchone()
    conn.close()
    assert r[0] == 2


def test_duckdb_validate_load(tmp_path, simple_schema, sample_rows):
    uri = str(tmp_path / "test.duckdb")
    with DuckDBAdapter(uri) as adapter:
        adapter.create_schema(simple_schema)
        adapter.create_tables(simple_schema)
        adapter.load_table("users", sample_rows)
        result = adapter.validate_load()
    assert result["success"] is True
    assert result["actual"]["users"] == 2


# --- Postgres (skip if no local DB) ---
@pytest.mark.skipif(
    True,  # Skip by default; set env to run: DATA_FORGE_TEST_POSTGRES=1
    reason="Requires local PostgreSQL",
)
def test_postgres_create_tables(simple_schema):
    import os
    uri = os.environ.get("DATA_FORGE_TEST_POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/postgres")
    from data_forge.adapters.postgres_adapter import PostgresAdapter
    with PostgresAdapter(uri) as adapter:
        adapter.create_schema(simple_schema)
        adapter.create_tables(simple_schema)


# --- CLI ---
def test_warehouse_load_report(tmp_path, simple_schema, sample_rows):
    """Verify warehouse_load appears in quality report when loading."""
    from data_forge.models.generation import GenerationRequest, GenerationResult, TableSnapshot

    uri = str(tmp_path / "test.db")
    req = GenerationRequest(
        schema_name="test",
        seed=1,
        scale=1,
        load_target="sqlite",
        db_uri=uri,
    )
    snapshots = [
        TableSnapshot(table_name="users", columns=["id", "name"], rows=sample_rows, row_count=2),
    ]
    from data_forge.adapters.load import load_to_database

    result = GenerationResult(request=req, tables=snapshots, success=True)
    report = load_to_database(result, simple_schema, "sqlite", uri)
    assert report["target"] == "sqlite"
    assert report["success"] is True
    assert report["tables_loaded"] == 1
    assert report["row_counts"]["users"] == 2


def test_cli_generate_load_sqlite(tmp_path):
    r = _run_cli([
        "generate", "--pack", "saas_billing", "--scale", "10",
        "--load", "sqlite", "--db-uri", str(tmp_path / "out.db"),
        "-o", str(tmp_path),
    ])
    assert r.returncode == 0
    assert (tmp_path / "out.db").exists()
    import sqlite3
    conn = sqlite3.connect(str(tmp_path / "out.db"))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cur.fetchall()]
    conn.close()
    assert len(tables) >= 1
