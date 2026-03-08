"""Tests for CLI commands."""

import subprocess
import sys
from pathlib import Path

import pytest


def _run_cli(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "data_forge.cli"] + args,
        capture_output=True,
        text=True,
        cwd=cwd or Path(__file__).parent.parent,
        timeout=30,
    )


def test_cli_generate_pack():
    result = _run_cli(["generate", "--pack", "saas_billing", "--scale", "20", "-o", "output_test", "-f", "csv"])
    assert result.returncode == 0
    out_dir = Path(__file__).parent.parent / "output_test"
    assert out_dir.exists()
    files = list(out_dir.glob("*.csv"))
    assert len(files) >= 1
    for f in files:
        f.unlink()
    out_dir.rmdir()


def test_cli_packs():
    result = _run_cli(["packs"])
    assert result.returncode == 0
    assert "saas_billing" in result.stdout
    assert "ecommerce" in result.stdout


def test_cli_validate_schema():
    root = Path(__file__).parent.parent
    schema = root / "schemas" / "saas_billing.sql"
    if not schema.exists():
        pytest.skip("schemas/saas_billing.sql not found")
    result = _run_cli(["validate", str(schema)])
    assert result.returncode == 0
    assert "Schema loaded" in result.stdout


def test_cli_validate_with_data(tmp_path):
    root = Path(__file__).parent.parent
    schema = root / "schemas" / "saas_billing.sql"
    if not schema.exists():
        pytest.skip("schemas/saas_billing.sql not found")
    (tmp_path / "organizations.csv").write_text("id,name\n1,Acme\n2,Globex\n")
    result = _run_cli(["validate", str(schema), "--data", str(tmp_path)])
    assert result.returncode == 0
    assert "Dataset validation" in result.stdout or "1 tables" in result.stdout
