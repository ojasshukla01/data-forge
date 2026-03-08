"""Tests for exporters."""

import json
import tempfile
from pathlib import Path

import pytest

from data_forge.config import OutputFormat
from data_forge.exporters import export_table, export_tables


def test_export_csv(tmp_path):
    rows = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    path = export_table(rows, tmp_path / "out", fmt=OutputFormat.CSV)
    assert path is not None
    assert path.exists()
    content = path.read_text()
    assert "a,b" in content or "a,b" in content.replace("\r", "")
    assert "1,x" in content or "1,x" in content.replace("\r", "")


def test_export_json(tmp_path):
    rows = [{"id": 1, "name": "Alice"}]
    path = export_table(rows, tmp_path / "out", fmt=OutputFormat.JSON)
    assert path is not None
    data = json.loads(path.read_text())
    assert data == rows


def test_export_jsonl(tmp_path):
    rows = [{"n": 1}, {"n": 2}]
    path = export_table(rows, tmp_path / "out", fmt=OutputFormat.JSONL)
    assert path is not None
    lines = [json.loads(l) for l in path.read_text().strip().split("\n") if l]
    assert lines == rows


def test_export_sql(tmp_path):
    rows = [{"id": 1, "val": "test"}]
    path = export_table(
        rows,
        tmp_path / "out",
        fmt=OutputFormat.SQL,
        table_name="mytable",
    )
    assert path is not None
    content = path.read_text()
    assert "INSERT INTO mytable" in content
    assert "1" in content
    assert "test" in content


def test_export_parquet(tmp_path):
    rows = [{"x": 1}, {"x": 2}]
    path = export_table(rows, tmp_path / "out", fmt=OutputFormat.PARQUET)
    assert path is not None
    assert path.suffix == ".parquet"
