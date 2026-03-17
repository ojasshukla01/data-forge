"""Data quality report: schema validity, referential integrity, rule violations, basic stats."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

from data_forge.models.schema import SchemaModel
from data_forge.models.rules import RuleSet
from data_forge.pii.redaction import RedactionConfig, redact_samples


def _iter_rows_for_table(
    table_name: str,
    table_data: dict[str, list[dict[str, Any]]] | None = None,
    table_store: Any | None = None,
) -> Iterable[dict[str, Any]]:
    if table_data is not None:
        return table_data.get(table_name, [])
    if table_store is None:
        return []
    return cast(Iterable[dict[str, Any]], table_store.iter_rows(table_name))


def _table_names(
    table_data: dict[str, list[dict[str, Any]]] | None = None,
    table_store: Any | None = None,
) -> list[str]:
    if table_data is not None:
        return list(table_data.keys())
    if table_store is not None:
        return cast(list[str], table_store.table_names())
    return []


def _evaluate_rule_impl(
    rule: "Any",
    table_name: str,
    row: dict[str, Any],
    context: dict[str, Any],
) -> tuple[bool, str | None]:
    """Delegate to rule_engine.evaluate_rule."""
    from data_forge.rule_engine import evaluate_rule
    return evaluate_rule(rule, table_name, row, context)


def compute_quality_report(
    schema: SchemaModel,
    table_data: dict[str, list[dict[str, Any]]] | None = None,
    rule_set: RuleSet | None = None,
    mode: "Any" = None,
    layer: "Any" = None,
    drift_events: list[dict[str, Any]] | None = None,
    pii_detection: dict[str, dict[str, str]] | None = None,
    privacy_mode: str = "off",
    redaction_config: RedactionConfig | None = None,
    privacy_warnings: list[str] | None = None,
    privacy_policy_mode: str = "advisory",
    privacy_policy_max_risk_score: int | None = None,
    privacy_policy_max_sensitive_columns: int | None = None,
    privacy_policy_fail_on_high_risk: bool = False,
    privacy_policy_block_categories: list[str] | None = None,
    table_store: Any | None = None,
) -> dict[str, Any]:
    """
    Produce a quality report: row counts, null counts, ref integrity, schema compliance.
    """
    report: dict[str, Any] = {
        "tables": {},
        "referential_integrity": True,
        "referential_errors": [],
        "schema_validity_score": 1.0,
        "summary": {},
    }
    total_rows = 0
    total_nulls = 0
    total_cells = 0
    duplicate_pk_errors: list[dict[str, Any]] = []
    cdc_valid = True
    by_rule: dict[str, int] = {}
    rule_samples: list[dict[str, Any]] = []
    max_samples_per_rule = 10
    samples_by_rule_count: dict[str, int] = {}
    total_rule_violations = 0

    available_tables = _table_names(table_data=table_data, table_store=table_store)

    for table_name in available_tables:
        rows = _iter_rows_for_table(table_name, table_data=table_data, table_store=table_store)
        table = schema.get_table(table_name)
        cols: list[str] = []
        if table:
            cols = [c.name for c in table.columns]
        pk_cols = table.primary_key if table else []
        pk_col = pk_cols[0] if pk_cols else None
        seen_pk_values: set[Any] = set()

        n_rows = 0
        null_count = 0
        context: dict[str, Any] = {}
        applicable_rules = (
            [r for r in rule_set.business_rules if r.table == table_name]
            if rule_set and rule_set.business_rules
            else []
        )
        for row_idx, row in enumerate(rows):
            n_rows += 1
            if not cols:
                cols = list(row.keys())
            null_count += sum(1 for v in row.values() if v is None)

            if pk_col:
                pk = row.get(pk_col)
                if pk is not None:
                    if pk in seen_pk_values:
                        duplicate_pk_errors.append(
                            {"table": table_name, "row_index": row_idx, "pk_value": pk}
                        )
                    seen_pk_values.add(pk)

            if mode and str(getattr(mode, "value", mode)) == "cdc":
                op = row.get("op_type")
                if op is not None and op not in {"INSERT", "UPDATE", "DELETE"}:
                    cdc_valid = False

            for rule in applicable_rules:
                passed, err_msg = _evaluate_rule_impl(rule, table_name, row, context)
                if passed or not err_msg:
                    continue
                total_rule_violations += 1
                by_rule[rule.name] = by_rule.get(rule.name, 0) + 1
                existing_samples = samples_by_rule_count.get(rule.name, 0)
                if existing_samples >= max_samples_per_rule or len(rule_samples) >= 50:
                    continue
                row_sample = dict(row)
                if pii_detection and redaction_config and redaction_config.enabled:
                    row_sample = redact_samples([row_sample], table_name, pii_detection, redaction_config)[0]
                rule_samples.append({
                    "table": table_name,
                    "rule": rule.name,
                    "row_index": row_idx,
                    "row": row_sample,
                })
                samples_by_rule_count[rule.name] = existing_samples + 1

        cell_count = n_rows * len(cols) if cols else 0
        total_rows += n_rows
        total_nulls += null_count
        total_cells += cell_count
        report["tables"][table_name] = {
            "row_count": n_rows,
            "column_count": len(cols),
            "null_count": null_count,
            "null_ratio": round(null_count / cell_count, 4) if cell_count else 0,
        }

    ok, ref_errors = _ref_integrity(schema, table_data=table_data, table_store=table_store)
    report["referential_integrity"] = ok
    report["referential_errors"] = ref_errors
    report["summary"] = {
        "total_rows": total_rows,
        "total_tables": len(available_tables),
        "total_nulls": total_nulls,
        "total_cells": total_cells,
        "overall_null_ratio": round(total_nulls / total_cells, 4) if total_cells else 0,
    }
    if ref_errors:
        report["schema_validity_score"] = max(0, 1.0 - len(ref_errors) / max(total_rows, 1) * 0.1)

    if total_rule_violations:
        report["rule_violations"] = {
            "total": total_rule_violations,
            "by_rule": by_rule,
            "samples": rule_samples,
        }
    elif not rule_set or not rule_set.business_rules:
        report["rule_violations"] = {"total": 0}
    else:
        report["rule_violations"] = {"total": 0}

    # PII detection in report
    if pii_detection:
        report["pii_detection"] = pii_detection

    # Privacy audit
    redact_apply = bool(redaction_config and redaction_config.enabled and privacy_mode != "off")
    redactions_count = 0
    if report.get("rule_violations", {}).get("samples") and pii_detection and redact_apply:
        for s in report["rule_violations"]["samples"]:
            tname = s.get("table", "")
            sens = sum(1 for c, cat in (pii_detection.get(tname) or {}).items() if cat != "unclassified")
            if sens and s.get("row"):
                redactions_count += sens
    sensitive_cols = 0
    by_category: dict[str, int] = {}
    high_risk = {"credentials", "government_id", "financial"}
    high_risk_detected: list[str] = []
    if pii_detection:
        for tcols in pii_detection.values():
            for cat in tcols.values():
                if cat != "unclassified":
                    sensitive_cols += 1
                    by_category[cat] = by_category.get(cat, 0) + 1
                    if cat in high_risk and cat not in high_risk_detected:
                        high_risk_detected.append(cat)
    report["privacy_audit"] = {
        "mode": privacy_mode,
        "sensitive_columns_detected": sensitive_cols,
        "redactions_applied": redactions_count,
        "warnings": privacy_warnings or [],
        "blocked": False,
    }
    report["privacy_summary"] = {
        "total_sensitive_columns": sensitive_cols,
        "by_category": by_category,
        "high_risk_categories_detected": high_risk_detected,
    }
    # Privacy scorecard: lightweight and explicit. This is a heuristic risk indicator, not a formal guarantee.
    category_weights = {
        "credentials": 5,
        "government_id": 5,
        "financial": 4,
        "health": 4,
        "date_of_birth": 3,
        "email": 2,
        "phone": 2,
        "address": 2,
        "free_text_sensitive": 2,
        "name": 1,
        "unknown_sensitive": 1,
    }
    weighted_points = 0
    for category, count in by_category.items():
        weighted_points += category_weights.get(category, 1) * count
    risk_score = min(100, weighted_points * 3)
    if risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"
    report["privacy_scorecard"] = {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "sensitive_category_count": len(by_category),
        "high_risk_categories": high_risk_detected,
        "sensitive_columns_detected": sensitive_cols,
    }
    policy_violations: list[str] = []
    violation_details: list[dict[str, Any]] = []

    def _add_violation(code: str, detail: str) -> None:
        policy_violations.append(f"{code}:{detail}" if detail else code)
        violation_details.append({"code": code, "detail": detail, "severity": "high"})

    if (
        privacy_policy_max_risk_score is not None
        and risk_score > int(privacy_policy_max_risk_score)
    ):
        _add_violation(
            "risk_score_exceeds_threshold",
            f"{risk_score}>{int(privacy_policy_max_risk_score)}",
        )
    if (
        privacy_policy_max_sensitive_columns is not None
        and sensitive_cols > int(privacy_policy_max_sensitive_columns)
    ):
        _add_violation(
            "sensitive_columns_exceed_threshold",
            f"{sensitive_cols}>{int(privacy_policy_max_sensitive_columns)}",
        )
    if privacy_policy_fail_on_high_risk and privacy_mode == "strict" and high_risk_detected:
        _add_violation("high_risk_categories_present", ",".join(sorted(high_risk_detected)))
    configured_block_categories = set(privacy_policy_block_categories or [])
    detected_categories = set(by_category.keys())
    blocked_cats_detected = sorted(configured_block_categories & detected_categories)
    for cat in blocked_cats_detected:
        _add_violation("blocked_category_detected", cat)

    evaluated_mode = (
        privacy_policy_mode
        if privacy_policy_mode in ("advisory", "enforce")
        else "advisory"
    )
    policy_decision = (
        "block"
        if policy_violations and evaluated_mode == "enforce"
        else ("warn" if policy_violations else "allow")
    )
    policy_enforced = evaluated_mode == "enforce"
    report["privacy_policy"] = {
        "mode": privacy_mode,
        "policy_evaluated": True,
        "policy_mode": evaluated_mode,
        "policy_decision": policy_decision,
        "enforced": policy_enforced,
        "would_block": bool(policy_violations),
        "violations": policy_violations,
        "violation_details": violation_details,
        "violation_count": len(policy_violations),
        "max_risk_score_threshold": privacy_policy_max_risk_score,
        "max_sensitive_columns_threshold": privacy_policy_max_sensitive_columns,
        "fail_on_high_risk": privacy_policy_fail_on_high_risk,
        "blocked_categories": sorted(configured_block_categories),
        "blocked_categories_detected": blocked_cats_detected,
        "note": "Policy uses measured risk indicators from this report; this is not a formal privacy guarantee.",
    }
    report["privacy_audit"]["blocked"] = bool(
        report["privacy_policy"]["policy_decision"] == "block" and report["privacy_policy"]["enforced"]
    )

    if drift_events:
        report["schema_drift"] = {
            "total": len(drift_events),
            "events": drift_events,
        }

    if duplicate_pk_errors:
        report["duplicate_primary_keys"] = duplicate_pk_errors

    from data_forge.models.generation import GenerationMode

    if mode == GenerationMode.CDC:
        report["cdc_op_type_valid"] = cdc_valid

    return report


def _check_duplicate_pks(
    schema: SchemaModel,
    table_data: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Check for duplicate primary keys."""
    errors: list[dict[str, Any]] = []
    for table_name, rows in table_data.items():
        table = schema.get_table(table_name)
        pk_cols = table.primary_key if table else (list(rows[0].keys())[:1] if rows else [])
        if not pk_cols:
            continue
        pk_col = pk_cols[0]
        seen: set[Any] = set()
        for i, row in enumerate(rows):
            pk = row.get(pk_col)
            if pk is not None:
                if pk in seen:
                    errors.append({"table": table_name, "row_index": i, "pk_value": pk})
                seen.add(pk)
    return errors


def _check_cdc_op_types(table_data: dict[str, list[dict[str, Any]]]) -> bool:
    """Verify all rows have valid op_type when in CDC mode."""
    valid = {"INSERT", "UPDATE", "DELETE"}
    for rows in table_data.values():
        for row in rows:
            op = row.get("op_type")
            if op is not None and op not in valid:
                return False
    return True


def _ref_integrity(
    schema: SchemaModel,
    table_data: dict[str, list[dict[str, Any]]] | None = None,
    table_store: Any | None = None,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for rel in schema.relationships:
        if not rel.to_columns or not rel.from_columns:
            continue
        parent_pk_col = rel.to_columns[0]
        child_fk_col = rel.from_columns[0]

        parent_pks = {
            r.get(parent_pk_col)
            for r in _iter_rows_for_table(rel.to_table, table_data=table_data, table_store=table_store)
            if r.get(parent_pk_col) is not None
        }
        for i, row in enumerate(
            _iter_rows_for_table(rel.from_table, table_data=table_data, table_store=table_store)
        ):
            fk_val = row.get(child_fk_col)
            if fk_val is not None and fk_val not in parent_pks:
                errors.append(f"{rel.from_table}[{i}].{child_fk_col}={fk_val} missing in {rel.to_table}")
    return len(errors) == 0, errors


def validate_referential_integrity(
    schema: SchemaModel,
    table_data: dict[str, list[dict[str, Any]]],
) -> tuple[bool, list[str]]:
    """Public alias."""
    return _ref_integrity(schema, table_data=table_data)


def load_dataset_from_dir(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load tables from a directory of CSV, JSON, JSONL, or Parquet files."""
    import csv
    import json

    table_data: dict[str, list[dict[str, Any]]] = {}
    path = Path(path)
    if not path.is_dir():
        return table_data

    for f in sorted(path.iterdir()):
        if not f.is_file():
            continue
        name = f.stem
        suffix = f.suffix.lower()
        rows: list[dict[str, Any]] = []
        try:
            if suffix == ".csv":
                with f.open(encoding="utf-8", newline="") as fp:
                    reader = csv.DictReader(fp)
                    rows = list(reader)
            elif suffix == ".json":
                data = json.loads(f.read_text(encoding="utf-8"))
                rows = data if isinstance(data, list) else []
            elif suffix == ".jsonl" or suffix == ".ndjson":
                for line in f.read_text(encoding="utf-8").strip().split("\n"):
                    if line:
                        rows.append(json.loads(line))
            elif suffix == ".parquet":
                import pyarrow.parquet as pq
                tbl = pq.read_table(f)
                rows = tbl.to_pylist()
            if rows:
                table_data[name] = rows
        except Exception:
            continue
    return table_data


def validate_schema_compliance(
    table_name: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    schema_table: Any,
) -> tuple[bool, list[str]]:
    """Check rows match schema (columns, nullability)."""
    from data_forge.models.schema import TableDef

    errors: list[str] = []
    if not schema_table or not isinstance(schema_table, TableDef):
        return True, []
    expected = {c.name for c in schema_table.columns}
    for i, row in enumerate(rows):
        for k in row:
            if k not in expected:
                errors.append(f"{table_name} row {i}: unexpected column '{k}'")
        for col in schema_table.columns:
            if not col.nullable and row.get(col.name) is None:
                errors.append(f"{table_name} row {i}: required '{col.name}' is null")
    return len(errors) == 0, errors
