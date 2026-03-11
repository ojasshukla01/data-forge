"""Security-focused tests: schema ID validation, path safety, payload limits."""

from fastapi.testclient import TestClient

from data_forge.api.main import app
from data_forge.api.security import validate_schema_body_size, validate_schema_id


def test_validate_schema_id_rejects_path_traversal() -> None:
    """validate_schema_id rejects slashes, backslashes, .."""
    for bad in ["schema_../evil", "schema_foo/bar", "schema_foo\\bar", "../schema_x"]:
        try:
            validate_schema_id(bad)
            raise AssertionError(f"Expected ValueError for {bad!r}")
        except ValueError as e:
            assert "path" in str(e).lower() or "invalid" in str(e).lower()


def test_validate_schema_id_rejects_wrong_format() -> None:
    """validate_schema_id rejects non-schema_ prefix and invalid chars."""
    for bad in ["", "foo", "schema", "schema_", "schema_a!", "schema_a b"]:
        try:
            validate_schema_id(bad)
            raise AssertionError(f"Expected ValueError for {bad!r}")
        except ValueError:
            pass


def test_validate_schema_id_accepts_valid() -> None:
    """validate_schema_id accepts valid schema_<alphanumeric>."""
    validate_schema_id("schema_abc123")
    validate_schema_id("schema_test")
    validate_schema_id("schema_a1_b2")


def test_validate_schema_body_size_rejects_large() -> None:
    """validate_schema_body_size rejects schema exceeding limit."""
    # Build schema > 512KB (100 tables * 200 columns with long padding)
    long_pad = "x" * 500
    huge = {
        "tables": [
            {
                "name": f"t{i}",
                "columns": [{"name": f"c{j}{long_pad}", "data_type": "string"} for j in range(200)],
            }
            for i in range(100)
        ],
        "relationships": [],
    }
    try:
        validate_schema_body_size(huge)
        raise AssertionError("Expected ValueError for oversized schema")
    except ValueError as e:
        assert "too large" in str(e).lower()


def test_validate_schema_body_size_accepts_reasonable() -> None:
    """validate_schema_body_size accepts schema under limit."""
    small = {"name": "test", "tables": [{"name": "t1", "columns": []}], "relationships": []}
    validate_schema_body_size(small)


def test_custom_schema_api_rejects_invalid_schema_id() -> None:
    """Custom schema API returns 400 for invalid schema_id (path traversal chars)."""
    client = TestClient(app)
    # schema_id="schema_.." hits our handler; validate_schema_id rejects ".."
    resp = client.get("/api/custom-schemas/schema_..")
    assert resp.status_code == 400
    detail = resp.json().get("detail", "")
    assert "path" in detail.lower() or "invalid" in detail.lower()


def test_custom_schema_api_rejects_schema_id_with_special_chars() -> None:
    """Custom schema API rejects schema_id with invalid characters."""
    client = TestClient(app)
    # schema_a! has invalid char ! ; single path segment so route matches
    resp = client.get("/api/custom-schemas/schema_a%21")
    assert resp.status_code == 400


def test_custom_schema_validate_malformed_schema() -> None:
    """POST /validate returns errors for malformed schema."""
    client = TestClient(app)
    resp = client.post(
        "/api/custom-schemas/validate",
        json={"schema": "not an object"},
    )
    assert resp.status_code == 422  # Pydantic validation error


def test_custom_schema_create_rejects_oversized_schema() -> None:
    """POST /create returns 400 when schema body exceeds 512KB limit (under 2MB req limit)."""
    client = TestClient(app)
    # Schema >512KB but <2MB: 30 tables * 80 cols * 300 chars ≈ 720KB
    long_pad = "x" * 280
    huge_tables = [
        {
            "name": f"t{i}",
            "columns": [{"name": f"c{j}{long_pad}", "data_type": "string"} for j in range(80)],
        }
        for i in range(30)
    ]
    payload = {
        "name": "big",
        "schema": {"name": "big", "tables": huge_tables, "relationships": []},
    }
    resp = client.post("/api/custom-schemas", json=payload)
    # 400 from validate_schema_body_size, or 413 if total request >2MB
    assert resp.status_code in (400, 413)
    if resp.status_code == 400:
        data = resp.json()
        detail = str(data.get("detail", ""))
        assert "too large" in detail.lower()
