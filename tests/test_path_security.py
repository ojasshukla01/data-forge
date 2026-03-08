"""Tests for path security."""

import pytest
from pathlib import Path

from data_forge.config import ensure_path_allowed, SecurityError, Settings


def test_ensure_path_allowed_under_schemas(tmp_path):
    settings = Settings()
    root = tmp_path
    (root / "schemas").mkdir()
    schema_file = root / "schemas" / "foo.sql"
    schema_file.touch()
    result = ensure_path_allowed(schema_file, root)
    assert result == schema_file.resolve()


def test_ensure_path_allowed_raises_outside():
    with pytest.raises(SecurityError, match="outside allowed"):
        ensure_path_allowed(Path("/etc/passwd"), Path("/home/proj"))
