"""Tests for exporters."""

import json

from data_forge.config import OutputFormat
from data_forge.exporters import export_table, export_table_iter, export_snapshots
from data_forge.models.generation import TableSnapshot


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
    lines = [json.loads(line) for line in path.read_text().strip().split("\n") if line]
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


def test_export_table_iter_jsonl(tmp_path):
    rows = ({"id": i, "name": f"u{i}"} for i in range(5))
    path = export_table_iter(rows, tmp_path / "iter_out", fmt=OutputFormat.JSONL)
    assert path is not None
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").strip().split("\n")]
    assert len(lines) == 5
    assert lines[0]["id"] == 0
    assert lines[-1]["name"] == "u4"


def test_export_table_iter_parquet(tmp_path):
    rows = ({"id": i, "value": f"v{i}"} for i in range(120))
    path = export_table_iter(rows, tmp_path / "iter_parquet", fmt=OutputFormat.PARQUET, batch_size=25)
    assert path is not None
    assert path.exists()
    assert path.suffix == ".parquet"


def test_export_snapshots_without_table_dict_copy(tmp_path):
    snapshots = [
        TableSnapshot(table_name="users", columns=["id"], rows=[{"id": 1}, {"id": 2}], row_count=2),
        TableSnapshot(table_name="orders", columns=["id"], rows=[{"id": 10}], row_count=1),
    ]
    paths = export_snapshots(snapshots, tmp_path, fmt=OutputFormat.CSV)
    assert len(paths) == 2
    names = {p.stem for p in paths}
    assert names == {"users", "orders"}
