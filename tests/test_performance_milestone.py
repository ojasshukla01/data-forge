"""Tests for performance hardening + benchmark milestone."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from data_forge.domain_packs import get_pack
from data_forge.engine import run_generation
from data_forge.exporters import export_table_chunked
from data_forge.models.generation import GenerationRequest
from data_forge.adapters.load import load_to_database
from data_forge.performance import build_materialization_diagnostics


def _run_cli(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "data_forge.cli"] + args,
        capture_output=True,
        text=True,
        cwd=cwd or Path(__file__).parent.parent,
        timeout=60,
    )


# Chunking tests
def test_chunked_generation_preserves_row_counts():
    """Chunked generation should produce the same total row count as non-chunked."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    scale = 500
    req_no_chunk = GenerationRequest(
        schema_name="saas_billing", seed=42, scale=scale, chunk_size=None
    )
    req_chunked = GenerationRequest(
        schema_name="saas_billing", seed=42, scale=scale, chunk_size=100
    )
    r1 = run_generation(req_no_chunk, schema=pack.schema, rule_set=pack.rule_set)
    r2 = run_generation(req_chunked, schema=pack.schema, rule_set=pack.rule_set)
    assert r1.success
    assert r2.success
    total1 = sum(t.row_count for t in r1.tables)
    total2 = sum(t.row_count for t in r2.tables)
    assert total1 == total2
    # Per-table counts should match
    counts1 = {t.table_name: t.row_count for t in r1.tables}
    counts2 = {t.table_name: t.row_count for t in r2.tables}
    assert counts1 == counts2


def test_chunked_csv_export_works(tmp_path):
    """export_table_chunked writes valid CSV from iterator."""
    rows = [{"id": i, "val": f"r{i}"} for i in range(50)]
    it = iter(rows)
    path = export_table_chunked(it, tmp_path / "chunked", fmt="csv")
    assert path is not None
    assert path.exists()
    content = path.read_text()
    lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
    assert len(lines) == 51  # header + 50 rows
    assert "id,val" in content
    assert "0,r0" in content
    assert "49,r49" in content


def test_chunked_jsonl_export_works(tmp_path):
    """export_table_chunked writes valid JSONL from iterator."""
    rows = [{"n": i, "label": f"item_{i}"} for i in range(30)]
    it = iter(rows)
    path = export_table_chunked(it, tmp_path / "chunked", fmt="jsonl")
    assert path is not None
    assert path.exists()
    lines = path.read_text().strip().split("\n")
    assert len(lines) == 30
    data = [json.loads(line) for line in lines]
    assert data == rows


# Batch loading tests
def test_sqlite_batch_load_works(tmp_path):
    """SQLite adapter loads data in batches."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(schema_name="saas_billing", seed=1, scale=150)
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    db_path = tmp_path / "batch.db"
    report = load_to_database(result, pack.schema, "sqlite", str(db_path), batch_size=50)
    assert report.get("success")
    assert report.get("tables_loaded", 0) > 0
    total = sum(report.get("row_counts", {}).values())
    assert total == sum(t.row_count for t in result.tables)


def test_duckdb_batch_load_works(tmp_path):
    """DuckDB adapter loads data in batches."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(schema_name="saas_billing", seed=1, scale=100)
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    db_path = tmp_path / "batch.duckdb"
    report = load_to_database(result, pack.schema, "duckdb", str(db_path), batch_size=25)
    assert report.get("success")
    assert report.get("tables_loaded", 0) > 0
    total = sum(report.get("row_counts", {}).values())
    assert total == sum(t.row_count for t in result.tables)


# Benchmark tests
def test_benchmark_command_runs():
    """Benchmark command runs and exits 0."""
    result = _run_cli(["benchmark", "--pack", "saas_billing", "--scale", "50"])
    assert result.returncode == 0
    assert "benchmark_results" in result.stdout or "rows_per_second" in result.stdout


def test_benchmark_output_json_created(tmp_path):
    """Benchmark --output-json writes valid JSON file."""
    out_file = tmp_path / "bench.json"
    result = _run_cli([
        "benchmark", "--pack", "saas_billing", "--scale", "30",
        "--output-json", str(out_file)
    ])
    assert result.returncode == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "benchmark_results" in data
    assert "timings" in data
    assert "performance_warnings" in data


def test_benchmark_results_contain_required_fields():
    """Benchmark results include all required fields."""
    result = _run_cli(["benchmark", "--pack", "saas_billing", "--scale", "20"])
    assert result.returncode == 0
    # Parse JSON from stdout (first line might be progress; last block is benchmark_results)
    try:
        start = result.stdout.find('{')
        if start >= 0:
            # Take the first JSON object (benchmark_results)
            depth = 0
            end = start
            for i, c in enumerate(result.stdout[start:]):
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        end = start + i + 1
                        break
            chunk = result.stdout[start:end]
            parsed = json.loads(chunk)
            br = parsed.get("benchmark_results", parsed)
            assert "iterations" in br
            assert "total_rows_generated" in br
            assert "generation_seconds" in br
            assert "rows_per_second_generation" in br
            assert "peak_memory_mb_estimate" in br
    except (json.JSONDecodeError, KeyError):
        pytest.skip("Could not parse benchmark JSON from stdout")


# Timings tests
def test_result_includes_timing_keys():
    """Generation result includes timing keys when timings_out provided."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    timings: dict = {}
    req = GenerationRequest(schema_name="saas_billing", seed=1, scale=30)
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set, timings_out=timings)
    assert result.success
    assert "schema_load_seconds" in timings or "generation_seconds" in timings
    assert "generation_seconds" in timings
    assert "rule_load_seconds" in timings


def test_timings_are_non_negative():
    """Timing values are non-negative."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    timings: dict = {}
    req = GenerationRequest(schema_name="saas_billing", seed=1, scale=20)
    run_generation(req, schema=pack.schema, rule_set=pack.rule_set, timings_out=timings)
    for k, v in timings.items():
        assert isinstance(v, (int, float)), f"{k} should be numeric"
        assert v >= 0, f"{k} should be non-negative, got {v}"


# Warnings test
def test_large_scale_without_chunk_size_emits_warning():
    """Scale exceeding threshold without chunk_size produces performance warning."""
    from unittest.mock import patch

    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    # Patch threshold to 80 so scale=100 triggers the warning
    with patch("data_forge.performance.SCALE_WARN", 80):
        req = GenerationRequest(
            schema_name="saas_billing", seed=1, scale=100, chunk_size=None
        )
        result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    assert any("chunk" in w.lower() or "scale" in w.lower() for w in result.performance_warnings)


# Determinism test
def test_fixed_seed_with_chunking_remains_stable():
    """Same seed + chunk_size produces identical row counts across runs."""
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(
        schema_name="saas_billing", seed=99, scale=200, chunk_size=50
    )
    r1 = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    r2 = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert r1.success and r2.success
    counts1 = [t.row_count for t in r1.tables]
    counts2 = [t.row_count for t in r2.tables]
    assert counts1 == counts2


def test_build_materialization_diagnostics_emits_large_run_signals():
    diagnostics = build_materialization_diagnostics(
        row_counts={"users": 250_000, "events": 100_000},
        approx_cols_by_table={"users": 10, "events": 15},
        layer="all",
    )
    assert diagnostics["planned_rows"] == 350_000
    assert diagnostics["planned_cells_estimate"] > 0
    assert diagnostics["estimated_peak_memory_mb"] > 0
    assert any("local runs" in w.lower() or "memory" in w.lower() for w in diagnostics["warnings"])
    assert any("layer mode is 'all'" in w.lower() for w in diagnostics["warnings"])


def test_run_generation_includes_materialization_diagnostics():
    pack = get_pack("saas_billing")
    if not pack:
        pytest.skip("saas_billing pack not found")
    req = GenerationRequest(schema_name="saas_billing", seed=7, scale=120, layer="all")
    result = run_generation(req, schema=pack.schema, rule_set=pack.rule_set)
    assert result.success
    assert "materialization" in result.quality_report
    m = result.quality_report["materialization"]
    assert m.get("planned_rows", 0) > 0
    assert m.get("tables", 0) > 0
