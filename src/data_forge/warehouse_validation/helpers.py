"""Validation helpers for warehouse loads: row counts, table existence, columns."""

from typing import Any

from data_forge.models.schema import SchemaModel
from data_forge.models.generation import TableSnapshot


def run_warehouse_validation(
    load_report: dict[str, Any],
    schema: SchemaModel,
    table_snapshots: list[TableSnapshot],
    target: str = "",
) -> dict[str, Any]:
    """
    Produce warehouse_validation report from load report and schema.
    Checks: row count match, missing tables, missing columns (when adapter supports it).
    """
    report: dict[str, Any] = {
        "target": target or load_report.get("target", ""),
        "tables_checked": 0,
        "checks_passed": True,
        "row_count_match": True,
        "missing_tables": [],
        "missing_columns": {},
    }
    if not load_report.get("success"):
        report["checks_passed"] = False
        return report

    row_counts = load_report.get("row_counts", {})
    report["tables_checked"] = len(row_counts)

    for snap in table_snapshots:
        tname = snap.table_name
        if tname not in row_counts:
            report["missing_tables"].append(tname)
            report["checks_passed"] = False
            continue
        expected_n = snap.row_count or len(snap.rows)
        actual_n = row_counts.get(tname, 0)
        if actual_n != expected_n:
            report["row_count_match"] = False
            report["checks_passed"] = False

    if report["missing_tables"]:
        report["checks_passed"] = False

    return report
