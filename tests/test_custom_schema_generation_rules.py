"""Tests for column-level generation rules in custom schemas (SchemaModel / ColumnDef)."""

import re

from data_forge.engine import run_generation
from data_forge.generators.generation_rules import column_rule_to_generation_rule
from data_forge.models.generation import GenerationRequest
from data_forge.models.rules import GenerationRuleType
from data_forge.models.schema import ColumnDef, ColumnGenerationRule, DataType, SchemaModel, TableDef


def test_column_rule_to_generation_rule_valid() -> None:
    """column_rule_to_generation_rule builds GenerationRule for valid rule_type."""
    gr = column_rule_to_generation_rule("t", "c", {"rule_type": "uuid", "params": {}})
    assert gr is not None
    assert gr.table == "t"
    assert gr.column == "c"
    assert gr.rule_type == GenerationRuleType.UUID

    gr2 = column_rule_to_generation_rule("users", "email", {"rule_type": "faker", "params": {"provider": "email"}})
    assert gr2 is not None
    assert gr2.rule_type == GenerationRuleType.FAKER
    assert gr2.params == {"provider": "email"}


def test_column_rule_to_generation_rule_invalid_returns_none() -> None:
    """column_rule_to_generation_rule returns None for unknown rule_type."""
    assert column_rule_to_generation_rule("t", "c", {"rule_type": "unknown", "params": {}}) is None
    assert column_rule_to_generation_rule("t", "c", {"rule_type": "", "params": {}}) is None


def test_static_generation_rule() -> None:
    """static rule returns params.value for all rows."""
    from data_forge.generators.generation_rules import apply_generation_rule
    from data_forge.models.rules import GenerationRule, GenerationRuleType

    gr = GenerationRule(table="t", column="c", rule_type=GenerationRuleType.STATIC, params={"value": "fixed"})
    assert apply_generation_rule(gr, 0, 42) == "fixed"
    assert apply_generation_rule(gr, 99, 123) == "fixed"


def test_weighted_choice_generation_rule() -> None:
    """weighted_choice rule returns values from choices, optionally weighted."""
    from data_forge.generators.generation_rules import apply_generation_rule
    from data_forge.models.rules import GenerationRule, GenerationRuleType

    choices = ["active", "inactive", "pending"]
    gr = GenerationRule(
        table="t",
        column="status",
        rule_type=GenerationRuleType.WEIGHTED_CHOICE,
        params={"choices": choices},
    )
    for i in range(20):
        val = apply_generation_rule(gr, i, 42)
        assert val in choices

    gr2 = GenerationRule(
        table="t",
        column="status",
        rule_type=GenerationRuleType.WEIGHTED_CHOICE,
        params={"choices": choices, "weights": [0.5, 0.3, 0.2]},
    )
    for i in range(20):
        val = apply_generation_rule(gr2, i, 99)
        assert val in choices


def test_weighted_choice_column_rule_to_generation_rule() -> None:
    """column_rule_to_generation_rule accepts weighted_choice."""
    gr = column_rule_to_generation_rule(
        "t",
        "status",
        {"rule_type": "weighted_choice", "params": {"choices": ["a", "b", "c"]}},
    )
    assert gr is not None
    assert gr.rule_type == GenerationRuleType.WEIGHTED_CHOICE
    assert gr.params == {"choices": ["a", "b", "c"]}


def test_null_probability_returns_none_sometimes() -> None:
    """null_probability param causes some rows to return None."""
    from data_forge.generators.generation_rules import apply_generation_rule
    from data_forge.models.rules import GenerationRule, GenerationRuleType

    gr = GenerationRule(
        table="t",
        column="c",
        rule_type=GenerationRuleType.STATIC,
        params={"value": "x", "null_probability": 0.5},
    )
    results = [apply_generation_rule(gr, i, 42) for i in range(100)]
    null_count = sum(1 for v in results if v is None)
    assert 10 <= null_count <= 90  # ~50% with some variance


def test_null_probability_validation() -> None:
    """validate_generation_rule rejects invalid null_probability."""
    from data_forge.generators.generation_rules import validate_generation_rule
    from data_forge.models.rules import GenerationRule, GenerationRuleType

    gr = GenerationRule(
        table="t",
        column="c",
        rule_type=GenerationRuleType.STATIC,
        params={"value": "x", "null_probability": 1.5},
    )
    errs = validate_generation_rule(gr)
    assert any("null_probability" in e for e in errs)


def test_weighted_choice_validation_rejects_empty_choices() -> None:
    """validate_generation_rule rejects weighted_choice with empty choices."""
    from data_forge.generators.generation_rules import validate_generation_rule
    from data_forge.models.rules import GenerationRule, GenerationRuleType

    gr = GenerationRule(
        table="t",
        column="c",
        rule_type=GenerationRuleType.WEIGHTED_CHOICE,
        params={"choices": []},
    )
    errs = validate_generation_rule(gr)
    assert any("choices" in e for e in errs)


def test_schema_model_validates_column_generation_rules() -> None:
    """SchemaModel.validate_schema rejects invalid rule_type in column generation_rule."""
    schema = SchemaModel(
        name="test",
        tables=[
            TableDef(
                name="users",
                columns=[
                    ColumnDef(name="id", data_type=DataType.INTEGER, primary_key=True),
                    ColumnDef(
                        name="email",
                        data_type=DataType.STRING,
                        generation_rule=ColumnGenerationRule(rule_type="invalid_type", params={}),
                    ),
                ],
                primary_key=["id"],
            ),
        ],
    )
    errors = schema.validate_schema()
    assert any("invalid rule_type" in e for e in errors)


def test_schema_model_validates_faker_provider_required() -> None:
    """SchemaModel.validate_schema rejects faker rule without provider."""
    schema = SchemaModel(
        name="test",
        tables=[
            TableDef(
                name="users",
                columns=[
                    ColumnDef(name="id", data_type=DataType.INTEGER, primary_key=True),
                    ColumnDef(
                        name="email",
                        data_type=DataType.STRING,
                        generation_rule=ColumnGenerationRule(rule_type="faker", params={}),
                    ),
                ],
                primary_key=["id"],
            ),
        ],
    )
    errors = schema.validate_schema()
    assert any("provider" in e for e in errors)


def test_schema_model_accepts_valid_column_generation_rule() -> None:
    """SchemaModel.validate_schema accepts valid column generation_rule."""
    schema = SchemaModel(
        name="test",
        tables=[
            TableDef(
                name="users",
                columns=[
                    ColumnDef(name="id", data_type=DataType.INTEGER, primary_key=True),
                    ColumnDef(
                        name="email",
                        data_type=DataType.STRING,
                        generation_rule=ColumnGenerationRule(rule_type="faker", params={"provider": "email"}),
                    ),
                ],
                primary_key=["id"],
            ),
        ],
    )
    errors = schema.validate_schema()
    assert errors == []


def test_engine_uses_column_generation_rules() -> None:
    """run_generation applies column-level generation_rule when no RuleSet rules."""
    schema = SchemaModel(
        name="test",
        tables=[
            TableDef(
                name="widgets",
                columns=[
                    ColumnDef(
                        name="id",
                        data_type=DataType.INTEGER,
                        primary_key=True,
                        generation_rule=ColumnGenerationRule(rule_type="sequence", params={"start": 1, "step": 1}),
                    ),
                    ColumnDef(
                        name="ref",
                        data_type=DataType.UUID,
                        generation_rule=ColumnGenerationRule(rule_type="uuid", params={}),
                    ),
                ],
                primary_key=["id"],
            ),
        ],
    )
    req = GenerationRequest(schema_name="test", scale=5, seed=100)
    result = run_generation(req, schema=schema)
    assert result.success
    rows = result.tables[0].rows
    assert len(rows) >= 5
    assert rows[0]["id"] == 1
    assert rows[1]["id"] == 2
    assert rows[2]["id"] == 3
    assert rows[3]["id"] == 4
    assert rows[4]["id"] == 5
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    for r in rows[:5]:
        assert uuid_pattern.match(r["ref"]) is not None


def test_preview_uses_column_generation_rules() -> None:
    """POST /api/schema/preview applies column generation_rule in preview."""
    from fastapi.testclient import TestClient

    from data_forge.api.main import app

    client = TestClient(app)
    schema = {
        "name": "preview_test",
        "tables": [
            {
                "name": "t1",
                "columns": [
                    {
                        "name": "seq",
                        "data_type": "integer",
                        "generation_rule": {"rule_type": "sequence", "params": {"start": 10, "step": 2}},
                    },
                    {
                        "name": "label",
                        "data_type": "string",
                        "generation_rule": {"rule_type": "faker", "params": {"provider": "name"}},
                    },
                ],
                "primary_key": [],
            },
        ],
        "relationships": [],
    }
    resp = client.post("/api/schema/preview", json={"schema": schema, "rows_per_table": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert "t1" in data
    rows = data["t1"]
    assert len(rows) == 3
    assert rows[0]["seq"] == 10
    assert rows[1]["seq"] == 12
    assert rows[2]["seq"] == 14
    assert all(isinstance(r["label"], str) and len(r["label"]) > 0 for r in rows)
