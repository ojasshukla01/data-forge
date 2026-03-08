"""Tests for schema ingestion."""

import pytest
from pathlib import Path

from data_forge.schema_ingest import load_schema, parse_sql_ddl
from data_forge.models.schema import SchemaModel, DataType


def test_parse_sql_ddl_simple():
    ddl = """
    CREATE TABLE users (
        id BIGINT PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        created_at TIMESTAMP
    );
    """
    schema = parse_sql_ddl(ddl)
    assert len(schema.tables) == 1
    assert schema.tables[0].name == "users"
    assert len(schema.tables[0].columns) == 3
    assert schema.tables[0].primary_key == ["id"]
    id_col = next(c for c in schema.tables[0].columns if c.name == "id")
    assert id_col.data_type == DataType.BIGINT
    assert id_col.primary_key is True


def test_parse_sql_ddl_with_fk():
    ddl = """
    CREATE TABLE orgs (id BIGINT PRIMARY KEY, name VARCHAR(100));
    CREATE TABLE users (
        id BIGINT PRIMARY KEY,
        organization_id BIGINT NOT NULL REFERENCES orgs(id)
    );
    """
    schema = parse_sql_ddl(ddl)
    assert len(schema.tables) == 2
    assert len(schema.relationships) == 1
    rel = schema.relationships[0]
    assert rel.from_table == "users"
    assert rel.to_table == "orgs"
    assert rel.from_columns == ["organization_id"]
    assert rel.to_columns == ["id"]


def test_load_schema_saas_billing():
    root = Path(__file__).resolve().parent.parent
    schema_path = root / "schemas" / "saas_billing.sql"
    if not schema_path.exists():
        pytest.skip("schemas/saas_billing.sql not found")
    schema = load_schema(schema_path)
    assert isinstance(schema, SchemaModel)
    assert len(schema.tables) >= 5
    assert any(t.name == "organizations" for t in schema.tables)
    assert any(t.name == "invoices" for t in schema.tables)
    order = schema.dependency_order()
    # organizations should come before users (no incoming FK)
    org_idx = next(i for i, t in enumerate(order) if t.name == "organizations")
    users_idx = next(i for i, t in enumerate(order) if t.name == "users")
    assert org_idx < users_idx
