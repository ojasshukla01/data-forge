"""Tests for validators."""

from data_forge.models.schema import ColumnDef, RelationshipDef, SchemaModel, TableDef
from data_forge.validators.quality import (
    compute_quality_report,
    validate_referential_integrity,
    load_dataset_from_dir,
)
from data_forge.models.rules import BusinessRule, RuleSet, RuleType


def test_validate_referential_integrity_pass():
    schema = SchemaModel(
        tables=[
            TableDef(name="parents", columns=[ColumnDef(name="id", primary_key=True)], primary_key=["id"]),
            TableDef(name="children", columns=[ColumnDef(name="id"), ColumnDef(name="parent_id")], primary_key=["id"]),
        ],
        relationships=[
            RelationshipDef(
                name="fk",
                from_table="children",
                from_columns=["parent_id"],
                to_table="parents",
                to_columns=["id"],
            ),
        ],
    )
    table_data = {
        "parents": [{"id": 1}, {"id": 2}],
        "children": [{"id": 10, "parent_id": 1}, {"id": 11, "parent_id": 2}],
    }
    ok, errors = validate_referential_integrity(schema, table_data)
    assert ok
    assert len(errors) == 0


def test_validate_referential_integrity_fail():
    schema = SchemaModel(
        tables=[
            TableDef(name="parents", columns=[ColumnDef(name="id")], primary_key=["id"]),
            TableDef(name="children", columns=[ColumnDef(name="id"), ColumnDef(name="parent_id")]),
        ],
        relationships=[
            RelationshipDef(
                name="fk",
                from_table="children",
                from_columns=["parent_id"],
                to_table="parents",
                to_columns=["id"],
            ),
        ],
    )
    table_data = {
        "parents": [{"id": 1}],
        "children": [{"id": 10, "parent_id": 99}],
    }
    ok, errors = validate_referential_integrity(schema, table_data)
    assert not ok
    assert len(errors) >= 1
    assert "99" in errors[0]


def test_compute_quality_report_includes_rule_violations():
    schema = SchemaModel(
        tables=[TableDef(name="t", columns=[ColumnDef(name="a"), ColumnDef(name="b")])],
    )
    rule_set = RuleSet(
        business_rules=[
            BusinessRule(
                name="a_lt_b",
                rule_type=RuleType.ORDER,
                table="t",
                expression="a <= b",
            ),
        ],
    )
    table_data = {"t": [{"a": 1, "b": 2}, {"a": 10, "b": 5}]}
    report = compute_quality_report(schema, table_data, rule_set=rule_set)
    assert "rule_violations" in report
    rv = report["rule_violations"]
    assert rv["total"] >= 1
    assert "by_rule" in rv
    assert "a_lt_b" in rv["by_rule"]


def test_compute_quality_report_includes_privacy_summary():
    schema = SchemaModel(
        tables=[TableDef(name="users", columns=[ColumnDef(name="id"), ColumnDef(name="email")])],
    )
    table_data = {"users": [{"id": 1, "email": "a@b.com"}]}
    pii_detection = {"users": {"id": "unclassified", "email": "email"}}
    report = compute_quality_report(schema, table_data, pii_detection=pii_detection)
    assert "privacy_summary" in report
    ps = report["privacy_summary"]
    assert "total_sensitive_columns" in ps
    assert "by_category" in ps
    assert "high_risk_categories_detected" in ps
    assert ps["total_sensitive_columns"] >= 1
    assert "email" in ps.get("by_category", {})


def test_load_dataset_from_dir_empty(tmp_path):
    data = load_dataset_from_dir(tmp_path)
    assert data == {}


def test_load_dataset_from_dir_csv(tmp_path):
    csv_file = tmp_path / "t.csv"
    csv_file.write_text("a,b\n1,2\n3,4\n")
    data = load_dataset_from_dir(tmp_path)
    assert "t" in data
    assert data["t"] == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
