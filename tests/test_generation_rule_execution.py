"""Tests for generation rule execution: faker, uuid, sequence, range."""

from data_forge.models.schema import ColumnDef, DataType, TableDef
from data_forge.models.rules import GenerationRule, GenerationRuleType, RuleSet
from data_forge.generators.primitives import PrimitiveGenerator
from data_forge.generators.table import generate_table
from data_forge.generators.generation_rules import apply_generation_rule, validate_generation_rule


def test_faker_rule_applied():
    """Faker rule generates values from provider."""
    rule = GenerationRule(table="users", column="email", rule_type=GenerationRuleType.FAKER, params={"provider": "email"})
    val = apply_generation_rule(rule, row_index=0, seed=42)
    assert isinstance(val, str)
    assert "@" in val and "." in val

    rule2 = GenerationRule(table="users", column="name", rule_type=GenerationRuleType.FAKER, params={"provider": "name"})
    val2 = apply_generation_rule(rule2, row_index=0, seed=42)
    assert isinstance(val2, str)
    assert " " in val2


def test_uuid_rule_applied():
    """UUID rule generates uuid4 strings."""
    rule = GenerationRule(table="users", column="id", rule_type=GenerationRuleType.UUID, params={})
    val = apply_generation_rule(rule, row_index=0, seed=42)
    assert isinstance(val, str)
    assert len(val) == 36
    assert val.count("-") == 4


def test_sequence_increments():
    """Sequence rule increments per row."""
    rule = GenerationRule(table="items", column="seq", rule_type=GenerationRuleType.SEQUENCE, params={"start": 10, "step": 2})
    v0 = apply_generation_rule(rule, row_index=0, seed=1)
    v1 = apply_generation_rule(rule, row_index=1, seed=1)
    v2 = apply_generation_rule(rule, row_index=2, seed=1)
    assert v0 == 10
    assert v1 == 12
    assert v2 == 14


def test_range_respects_bounds():
    """Range rule returns values within min/max."""
    rule = GenerationRule(table="nums", column="val", rule_type=GenerationRuleType.RANGE, params={"min": 5, "max": 10})
    for _ in range(20):
        val = apply_generation_rule(rule, row_index=0, seed=42)
        assert 5 <= val <= 10

    rule_float = GenerationRule(table="nums", column="val", rule_type=GenerationRuleType.RANGE, params={"min": 0.0, "max": 1.0})
    val = apply_generation_rule(rule_float, row_index=0, seed=99)
    assert 0 <= val <= 1


def test_generate_table_with_generation_rules():
    """Table generation applies generation_rules when present."""
    table = TableDef(
        name="test",
        columns=[
            ColumnDef(name="id", data_type=DataType.INTEGER),
            ColumnDef(name="email", data_type=DataType.STRING),
        ],
        primary_key=["id"],
    )
    rule_set = RuleSet(
        generation_rules=[
            GenerationRule(table="test", column="id", rule_type=GenerationRuleType.SEQUENCE, params={"start": 1, "step": 1}),
            GenerationRule(table="test", column="email", rule_type=GenerationRuleType.FAKER, params={"provider": "email"}),
        ]
    )
    prim = PrimitiveGenerator(seed=42)
    rows = generate_table(table, row_count=5, primitive_gen=prim, rule_set=rule_set, parent_key_supplier=None, seed=42)
    assert len(rows) == 5
    assert rows[0]["id"] == 1
    assert rows[1]["id"] == 2
    assert rows[4]["id"] == 5
    for r in rows:
        assert "@" in r["email"]


def test_validate_unknown_rule_type():
    """Unknown rule_type returns error."""
    rule = GenerationRule.model_construct(table="t", column="c", rule_type="invalid", params={})
    errors = validate_generation_rule(rule)
    assert len(errors) > 0
    assert "Unknown" in errors[0] or "unknown" in errors[0].lower()


def test_validate_faker_missing_provider():
    """Faker rule without provider returns error."""
    rule = GenerationRule(table="t", column="c", rule_type=GenerationRuleType.FAKER, params={})
    errors = validate_generation_rule(rule)
    assert len(errors) > 0
    assert "provider" in errors[0].lower()


def test_validate_range_invalid():
    """Range rule with min > max returns error."""
    rule = GenerationRule(table="t", column="c", rule_type=GenerationRuleType.RANGE, params={"min": 10, "max": 5})
    errors = validate_generation_rule(rule)
    assert len(errors) > 0
