"""Lightweight validation against GE expectation artifacts without full GE runtime."""

import json
from pathlib import Path
from typing import Any, cast

from data_forge.validators.quality import load_dataset_from_dir


def _load_suite(path: Path) -> dict[str, Any] | None:
    """Load expectation suite from JSON."""
    if not path.exists():
        return None
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return None


def _evaluate_expectation(
    exp: dict[str, Any],
    table_name: str,
    rows: list[dict[str, Any]],
) -> tuple[bool, str | None]:
    """Evaluate a single expectation against rows. Returns (passed, reason if failed)."""
    exp_type = exp.get("expectation_type", "")
    kwargs = exp.get("kwargs", {})

    if exp_type == "expect_table_row_count_to_be_between":
        count = len(rows)
        min_v = kwargs.get("min_value")
        max_v = kwargs.get("max_value")
        if min_v is not None and count < min_v:
            return False, f"row count {count} < min {min_v}"
        if max_v is not None and count > max_v:
            return False, f"row count {count} > max {max_v}"
        return True, None

    col = kwargs.get("column")
    if not col:
        return True, None

    if exp_type == "expect_column_values_to_not_be_null":
        nulls = [i for i, r in enumerate(rows) if r.get(col) is None]
        if nulls:
            return False, f"column '{col}' has nulls at row(s): {nulls[:5]}{'...' if len(nulls) > 5 else ''}"
        return True, None

    if exp_type == "expect_column_values_to_be_unique":
        seen: dict[Any, list[int]] = {}
        for i, r in enumerate(rows):
            v = r.get(col)
            if v not in seen:
                seen[v] = []
            seen[v].append(i)
        dups = {v: idxs for v, idxs in seen.items() if len(idxs) > 1}
        if dups:
            sample = next(iter(dups.items()))
            return False, f"duplicate values in '{col}': value {sample[0]} at rows {sample[1][:5]}"
        return True, None

    if exp_type == "expect_column_values_to_be_in_set":
        value_set = set(kwargs.get("value_set", []))
        for i, r in enumerate(rows):
            v = r.get(col)
            if v is not None and v not in value_set:
                return False, f"column '{col}' row {i}: value {v} not in allowed set"
        return True, None

    if exp_type == "expect_column_values_to_be_between":
        min_v = kwargs.get("min_value")
        max_v = kwargs.get("max_value")
        for i, r in enumerate(rows):
            v = r.get(col)
            if v is None:
                continue
            try:
                vv = float(v) if isinstance(v, (int, float, str)) and str(v).replace(".", "").replace("-", "").isdigit() else v
                if isinstance(vv, (int, float)):
                    if min_v is not None and vv < min_v:
                        return False, f"column '{col}' row {i}: {v} < min {min_v}"
                    if max_v is not None and vv > max_v:
                        return False, f"column '{col}' row {i}: {v} > max {max_v}"
            except (TypeError, ValueError):
                pass
        return True, None

    return True, None


def validate_against_expectations(
    expectations_dir: Path | str,
    data_dir: Path | str,
) -> dict[str, Any]:
    """
    Validate data against expectation suites. No GE runtime required.
    Returns report: {total_suites, passed, failed, failures: [{suite, expectation, reason}]}
    """
    expectations_dir = Path(expectations_dir)
    data_dir = Path(data_dir)

    # Load data from top-level or bronze/silver/gold
    table_data = load_dataset_from_dir(data_dir)
    for sub in ("bronze", "silver", "gold"):
        sub_path = data_dir / sub
        if sub_path.is_dir():
            sub_data = load_dataset_from_dir(sub_path)
            for k, v in sub_data.items():
                if k not in table_data or not table_data[k]:
                    table_data[k] = v

    suite_files = list(expectations_dir.glob("*_suite.json"))
    total_suites = len(suite_files)
    passed = 0
    failed = 0
    failures: list[dict[str, Any]] = []

    for path in suite_files:
        suite = _load_suite(path)
        if not suite:
            failed += 1
            failures.append({"suite": path.stem, "expectation": "load", "reason": "failed to load suite"})
            continue
        suite_name = suite.get("expectation_suite_name", path.stem)
        table_name = suite_name.replace("_suite", "")
        rows = table_data.get(table_name, [])
        suite_ok = True
        for exp in suite.get("expectations", []):
            ok, reason = _evaluate_expectation(exp, table_name, rows)
            if not ok:
                suite_ok = False
                failures.append({
                    "suite": suite_name,
                    "expectation": exp.get("expectation_type", "unknown"),
                    "reason": reason or "validation failed",
                })
        if suite_ok:
            passed += 1
        else:
            failed += 1

    return {
        "ge_validation": {
            "total_suites": total_suites,
            "passed": passed,
            "failed": failed,
            "failures": failures,
        }
    }
