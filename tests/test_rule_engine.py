"""Tests for rule engine."""

from data_forge.models.rules import BusinessRule, RuleType
from data_forge.rule_engine import evaluate_rule


def test_evaluate_rule_order_success():
    rule = BusinessRule(
        name="dates_order",
        rule_type=RuleType.ORDER,
        table="t",
        expression="started_at <= ended_at",
    )
    row = {"started_at": "2020-01-01", "ended_at": "2020-02-01"}
    passed, err = evaluate_rule(rule, "t", row)
    assert passed
    assert err is None


def test_evaluate_rule_order_failure():
    rule = BusinessRule(
        name="dates_order",
        rule_type=RuleType.ORDER,
        table="t",
        expression="started_at <= ended_at",
    )
    row = {"started_at": "2020-02-01", "ended_at": "2020-01-01"}
    passed, err = evaluate_rule(rule, "t", row)
    assert not passed
    assert err is not None
    assert "started_at" in err


def test_evaluate_rule_skips_other_table():
    rule = BusinessRule(
        name="dates_order",
        rule_type=RuleType.ORDER,
        table="other",
        expression="a <= b",
    )
    row = {"a": 10, "b": 1}
    passed, err = evaluate_rule(rule, "t", row)
    assert passed
    assert err is None


def test_evaluate_rule_range_success():
    rule = BusinessRule(
        name="qty_range",
        rule_type=RuleType.RANGE,
        table="t",
        fields=["quantity"],
        params={"min": 0, "max": 100},
    )
    row = {"quantity": 50}
    passed, err = evaluate_rule(rule, "t", row)
    assert passed


def test_evaluate_rule_range_failure():
    rule = BusinessRule(
        name="qty_range",
        rule_type=RuleType.RANGE,
        table="t",
        fields=["quantity"],
        params={"min": 0, "max": 100},
    )
    row = {"quantity": 150}
    passed, err = evaluate_rule(rule, "t", row)
    assert not passed
    assert "150" in err
