"""Data quality report: schema validity, referential integrity, rule violations, basic stats."""

from pathlib import Path
from typing import Any

from data_forge.models.schema import SchemaModel
from data_forge.models.rules import RuleSet
from data_forge.pii.redaction import RedactionConfig, redact_samples


def _collect_rule_violations(
    schema: SchemaModel,
    table_data: dict[str, list[dict[str, Any]]],
    rule_set: RuleSet,
    pii_detection: dict[str, dict[str, str]] | None = None,
    redaction_config: RedactionConfig | None = None,
) -> dict[str, Any]:
    """Evaluate business rules on all rows; return violations structure."""
    violations: list[dict[str, Any]] = []
    by_rule: dict[str, int] = {}
    samples_per_rule: dict[str, list[dict[str, Any]]] = {}
    max_samples_per_rule = 10

    for table_name, rows in table_data.items():
        applicable = [r for r in rule_set.business_rules if r.table == table_name]
        for row_idx, row in enumerate(rows):
            context: dict[str, Any] = {}
            for rule in applicable:
                passed, err_msg = _evaluate_rule_impl(rule, table_name, row, context)
                if not passed and err_msg:
                    row_snippet = dict(list(row.items())[:5])
                    if pii_detection and redaction_config and redaction_config.enabled:
                        row_snippet = redact_samples(
                            [row_snippet], table_name, pii_detection, redaction_config
                        )[0]
                    violations.append({
                        "table": table_name,
                        "rule": rule.name,
                        "row_index": row_idx,
                        "message": err_msg,
                        "row": row_snippet,
                    })
                    by_rule[rule.name] = by_rule.get(rule.name, 0) + 1
                    if rule.name not in samples_per_rule:
                        samples_per_rule[rule.name] = []
                    if len(samples_per_rule[rule.name]) < max_samples_per_rule:
                        row_sample = dict(row)
                        if pii_detection and redaction_config and redaction_config.enabled:
                            row_sample = redact_samples(
                                [row_sample], table_name, pii_detection, redaction_config
                            )[0]
                        samples_per_rule[rule.name].append({
                            "table": table_name,
                            "rule": rule.name,
                            "row_index": row_idx,
                            "row": row_sample,
                        })

    samples = []
    for _name, lst in samples_per_rule.items():
        samples.extend(lst[:max_samples_per_rule])

    if not violations:
        return {"total": 0}
    return {
        "total": len(violations),
        "by_rule": by_rule,
        "samples": samples[:50],
    }


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
    table_data: dict[str, list[dict[str, Any]]],
    rule_set: RuleSet | None = None,
    mode: "Any" = None,
    layer: "Any" = None,
    drift_events: list[dict[str, Any]] | None = None,
    pii_detection: dict[str, dict[str, str]] | None = None,
    privacy_mode: str = "off",
    redaction_config: RedactionConfig | None = None,
    privacy_warnings: list[str] | None = None,
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

    for table_name, rows in table_data.items():
        table = schema.get_table(table_name)
        cols = list(rows[0].keys()) if rows else []
        if table:
            cols = [c.name for c in table.columns]
        n_rows = len(rows)
        null_count = sum(1 for r in rows for v in r.values() if v is None)
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

    ok, ref_errors = _ref_integrity(schema, table_data)
    report["referential_integrity"] = ok
    report["referential_errors"] = ref_errors
    report["summary"] = {
        "total_rows": total_rows,
        "total_tables": len(table_data),
        "total_nulls": total_nulls,
        "total_cells": total_cells,
        "overall_null_ratio": round(total_nulls / total_cells, 4) if total_cells else 0,
    }
    if ref_errors:
        report["schema_validity_score"] = max(0, 1.0 - len(ref_errors) / max(total_rows, 1) * 0.1)

    if rule_set and rule_set.business_rules:
        report["rule_violations"] = _collect_rule_violations(
            schema, table_data, rule_set,
            pii_detection=pii_detection,
            redaction_config=redaction_config,
        )
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
    if pii_detection:
        for tcols in pii_detection.values():
            for cat in tcols.values():
                if cat != "unclassified":
                    sensitive_cols += 1
    report["privacy_audit"] = {
        "mode": privacy_mode,
        "sensitive_columns_detected": sensitive_cols,
        "redactions_applied": redactions_count,
        "warnings": privacy_warnings or [],
        "blocked": False,
    }

    if drift_events:
        report["schema_drift"] = {
            "total": len(drift_events),
            "events": drift_events,
        }

    dup_pks = _check_duplicate_pks(schema, table_data)
    if dup_pks:
        report["duplicate_primary_keys"] = dup_pks

    from data_forge.models.generation import GenerationMode

    if mode == GenerationMode.CDC:
        op_valid = _check_cdc_op_types(table_data)
        report["cdc_op_type_valid"] = op_valid

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
    table_data: dict[str, list[dict[str, Any]]],
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for rel in schema.relationships:
        if not rel.to_columns or not rel.from_columns:
            continue
        parent_rows = table_data.get(rel.to_table, [])
        child_rows = table_data.get(rel.from_table, [])
        parent_pk_col = rel.to_columns[0]
        child_fk_col = rel.from_columns[0]
        parent_pks = {r.get(parent_pk_col) for r in parent_rows if r.get(parent_pk_col) is not None}
        for i, row in enumerate(child_rows):
            fk_val = row.get(child_fk_col)
            if fk_val is not None and fk_val not in parent_pks:
                errors.append(f"{rel.from_table}[{i}].{child_fk_col}={fk_val} missing in {rel.to_table}")
    return len(errors) == 0, errors


def validate_referential_integrity(
    schema: SchemaModel,
    table_data: dict[str, list[dict[str, Any]]],
) -> tuple[bool, list[str]]:
    """Public alias."""
    return _ref_integrity(schema, table_data)


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
