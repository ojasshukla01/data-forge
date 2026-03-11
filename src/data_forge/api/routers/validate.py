"""Validation API router."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from data_forge.schema_ingest import load_schema
from data_forge.rule_engine import load_rule_set
from data_forge.validators.quality import (
    load_dataset_from_dir,
    compute_quality_report,
    _ref_integrity,
)
from data_forge.ge_validation import validate_against_expectations
from data_forge.reconciliation import run_reconciliation
from data_forge.config import SecurityError

router = APIRouter(prefix="/api", tags=["validate"])


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


@router.post("/validate")
def api_validate(params: dict[str, Any]) -> dict[str, Any]:
    """
    Validate schema and data. Params: schema_path, data_path, rules_path?, privacy_mode?
    """
    root = _project_root()
    schema_path = root / (params.get("schema_path") or "").lstrip("/")
    data_path = root / (params.get("data_path") or "").lstrip("/")
    rules_path = params.get("rules_path")
    if rules_path:
        rules_path = root / rules_path.lstrip("/")

    if not schema_path.exists():
        raise HTTPException(status_code=400, detail=f"Schema not found: {schema_path}")

    try:
        schema = load_schema(schema_path, project_root=root)
    except SecurityError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Schema parse failed: {e}") from e

    if not data_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Data path not a directory: {data_path}")

    table_data = load_dataset_from_dir(data_path)
    for sub in ("bronze", "silver", "gold"):
        subp = data_path / sub
        if subp.is_dir():
            extra = load_dataset_from_dir(subp)
            for k, v in extra.items():
                if k not in table_data or not table_data[k]:
                    table_data[k] = v

    rule_set = None
    if rules_path and rules_path.exists():
        try:
            rule_set = load_rule_set(rules_path, project_root=root)
        except Exception:
            pass

    privacy_mode = params.get("privacy_mode", "off")
    report = compute_quality_report(
        schema,
        table_data,
        rule_set=rule_set,
        privacy_mode=privacy_mode,
    )

    ref_ok, ref_errors = _ref_integrity(schema, table_data)
    report["referential_integrity"] = ref_ok
    report["referential_errors"] = ref_errors[:20]

    return {
        "success": ref_ok and (report.get("rule_violations", {}).get("total", 0) == 0),
        "report": report,
        "tables_validated": list(table_data.keys()),
    }


@router.post("/validate/ge")
def api_validate_ge(params: dict[str, Any]) -> dict[str, Any]:
    """Validate data against GE expectations. Params: expectations_path, data_path"""
    root = _project_root()
    exp_path = root / (params.get("expectations_path") or "").lstrip("/")
    data_path = root / (params.get("data_path") or "").lstrip("/")
    if not exp_path.exists():
        raise HTTPException(status_code=400, detail="Expectations path not found")
    if not data_path.is_dir():
        raise HTTPException(status_code=400, detail="Data path not a directory")
    exp_dir = exp_path / "expectations" if (exp_path / "expectations").exists() else exp_path
    return validate_against_expectations(exp_dir, data_path)


@router.post("/reconcile")
def api_reconcile(params: dict[str, Any]) -> dict[str, Any]:
    """Reconcile manifest vs data. Params: manifest_path, data_path, schema_path?"""
    root = _project_root()
    manifest_path = root / (params.get("manifest_path") or "").lstrip("/")
    data_path = root / (params.get("data_path") or "").lstrip("/")
    schema_path = params.get("schema_path")
    schema_obj = None
    if schema_path:
        sp = root / schema_path.lstrip("/")
        if sp.exists():
            try:
                schema_obj = load_schema(sp, project_root=root)
            except Exception:
                pass
    if not manifest_path.exists():
        raise HTTPException(status_code=400, detail="Manifest not found")
    if not data_path.is_dir():
        raise HTTPException(status_code=400, detail="Data path not a directory")
    return run_reconciliation(manifest_path, data_path, schema=schema_obj)
