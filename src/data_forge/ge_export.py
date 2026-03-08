"""Great Expectations-compatible export: expectation suites and checkpoints."""

import json
from pathlib import Path
from typing import Any

from data_forge.models.schema import SchemaModel
from data_forge.models.rules import RuleSet, RuleType


def build_expectation_suite(
    table_name: str,
    schema: SchemaModel,
    rule_set: RuleSet | None = None,
) -> dict[str, Any]:
    """
    Build a GE-compatible expectation suite for a table.
    Includes: row count > 0, PK uniqueness, PK/FK non-null, enum domains, basic types.
    """
    table = schema.get_table(table_name)
    if not table:
        return {"expectation_suite_name": f"{table_name}_suite", "expectations": []}

    expectations: list[dict[str, Any]] = []

    # Table row count > 0
    expectations.append({
        "expectation_type": "expect_table_row_count_to_be_between",
        "kwargs": {"min_value": 1, "max_value": None},
        "meta": {"notes": "Table should have at least one row"},
    })

    pk_cols = table.primary_key or [c.name for c in table.columns if c.primary_key]
    if not pk_cols and any(c.primary_key for c in table.columns):
        pk_cols = [c.name for c in table.columns if c.primary_key]

    # Primary key non-null and unique
    for col_name in pk_cols:
        expectations.append({
            "expectation_type": "expect_column_values_to_not_be_null",
            "kwargs": {"column": col_name},
            "meta": {"notes": "Primary key must not be null"},
        })
        expectations.append({
            "expectation_type": "expect_column_values_to_be_unique",
            "kwargs": {"column": col_name},
            "meta": {"notes": "Primary key must be unique"},
        })

    # Foreign key columns (from relationships where this table is child)
    fk_cols: set[str] = set()
    for rel in schema.get_relationships_to(table_name):
        fk_cols.update(rel.from_columns)
    for col_name in fk_cols:
        if col_name not in pk_cols:
            expectations.append({
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": col_name},
            })

    # Categorical / enum domain
    for col in table.columns:
        if col.enum_values:
            expectations.append({
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {"column": col.name, "value_set": col.enum_values},
                "meta": {"notes": f"Enum domain: {col.enum_values[:5]}{'...' if len(col.enum_values) > 5 else ''}"},
            })

    # Rule engine mapping: RANGE, ENUM from business rules
    if rule_set:
        for rule in rule_set.business_rules:
            if rule.table != table_name:
                continue
            if rule.rule_type == RuleType.RANGE and rule.fields and "min" in rule.params and "max" in rule.params:
                for f in rule.fields:
                    expectations.append({
                        "expectation_type": "expect_column_values_to_be_between",
                        "kwargs": {
                            "column": f,
                            "min_value": rule.params.get("min"),
                            "max_value": rule.params.get("max"),
                        },
                        "meta": {"notes": f"Rule: {rule.name}"},
                    })
            elif rule.rule_type == RuleType.ENUM and rule.params.get("values"):
                for f in rule.fields or [rule.params.get("column", "")]:
                    if f:
                        expectations.append({
                            "expectation_type": "expect_column_values_to_be_in_set",
                            "kwargs": {"column": f, "value_set": rule.params["values"]},
                            "meta": {"notes": f"Rule: {rule.name}"},
                        })

    return {
        "expectation_suite_name": f"{table_name}_suite",
        "expectations": expectations,
        "meta": {"data_forge_schema": schema.name, "table": table_name},
    }


def export_ge(
    schema: SchemaModel,
    rule_set: RuleSet | None,
    output_dir: Path | str,
) -> dict[str, Any]:
    """
    Export GE-compatible expectation suites and a checkpoint.
    Returns report: {suites_generated, checkpoint_path, output_dir, ...}
    """
    output_dir = Path(output_dir)
    expectations_dir = output_dir / "expectations"
    checkpoints_dir = output_dir / "checkpoints"
    expectations_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    suite_names: list[str] = []
    for table in schema.tables:
        suite = build_expectation_suite(table.name, schema, rule_set)
        path = expectations_dir / f"{table.name}_suite.json"
        path.write_text(json.dumps(suite, indent=2), encoding="utf-8")
        suite_names.append(suite["expectation_suite_name"])

    # Simple checkpoint config (GE v3 style)
    checkpoint = {
        "name": "data_forge_checkpoint",
        "config_version": 1.0,
        "class_name": "SimpleCheckpoint",
        "validations": [
            {"batch_request": {"datasource_name": "data_forge", "data_asset_name": name}, "expectation_suite_name": name}
            for name in suite_names
        ],
    }
    cp_path = checkpoints_dir / "data_forge_checkpoint.json"
    cp_path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

    return {
        "enabled": True,
        "output_dir": str(output_dir),
        "suites_generated": len(suite_names),
        "suite_names": suite_names,
        "expectations_path": str(expectations_dir),
        "checkpoint_path": str(cp_path),
    }
