"""Rule engine: load and evaluate business rules and distributions."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from data_forge.models.rules import (
    BusinessRule,
    DistributionRule,
    RuleSet,
    RuleType,
)

__all__ = ["load_rule_set", "RuleSet", "evaluate_rule"]


def load_rule_set(path: Path | str, project_root: Path | None = None) -> RuleSet:
    """Load a RuleSet from a YAML file."""
    from data_forge.config import Settings, ensure_path_allowed

    path = Path(path)
    root = project_root or Settings().project_root
    path = ensure_path_allowed(path, root)
    if not path.exists():
        return RuleSet(name=path.stem)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _dict_to_rule_set(data, name=path.stem)


def _dict_to_rule_set(data: dict[str, Any], name: str = "default") -> RuleSet:
    """Build RuleSet from dict (e.g. YAML)."""
    business = []
    for r in data.get("business_rules", []):
        if isinstance(r, dict):
            business.append(
                BusinessRule(
                    name=r.get("name", "unnamed"),
                    rule_type=RuleType(r.get("rule_type", "custom")),
                    table=r.get("table", ""),
                    description=r.get("description"),
                    expression=r.get("expression"),
                    fields=r.get("fields", []),
                    params=r.get("params", {}),
                    severity=r.get("severity", "error"),
                )
            )
    dist = []
    for d in data.get("distribution_rules", []):
        if isinstance(d, dict):
            dist.append(
                DistributionRule(
                    table=d.get("table", ""),
                    column=d.get("column", ""),
                    distribution=d.get("distribution", "uniform"),
                    params=d.get("params", {}),
                )
            )
    return RuleSet(
        name=data.get("name", name),
        business_rules=business,
        distribution_rules=dist,
        scenario=data.get("scenario"),
    )


def evaluate_rule(
    rule: BusinessRule,
    table_name: str,
    row: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> tuple[bool, str | None]:
    """
    Evaluate a business rule against a single row.
    Returns (passed, error_message).
    """
    if rule.table and rule.table != table_name:
        return True, None
    context = context or {}
    if rule.rule_type == RuleType.ORDER and rule.expression:
        # e.g. "created_at <= updated_at"
        return _eval_order(rule, row, context)
    if rule.rule_type == RuleType.RANGE and rule.fields:
        return _eval_range(rule, row, context)
    if rule.rule_type == RuleType.SUM and rule.expression:
        return _eval_sum(rule, row, context)
    if rule.rule_type == RuleType.EQUALITY and rule.expression:
        return _eval_equality(rule, row, context)
    return True, None


def _eval_order(rule: BusinessRule, row: dict[str, Any], context: dict[str, Any]) -> tuple[bool, str | None]:
    """Check date/field order (e.g. start <= end)."""
    # expression like "field_a <= field_b"
    import re
    m = re.match(r"(\w+)\s*(<=|>=|<|>)\s*(\w+)", (rule.expression or "").strip())
    if not m:
        return True, None
    fa, op, fb = m.group(1), m.group(2), m.group(3)
    a = row.get(fa)
    b = row.get(fb)
    if a is None or b is None:
        return True, None
    try:
        if op == "<=":
            ok = a <= b
        elif op == ">=":
            ok = a >= b
        elif op == "<":
            ok = a < b
        else:
            ok = a > b
        if not ok:
            return False, f"Rule {rule.name}: {fa} {op} {fb} violated"
        return True, None
    except TypeError:
        return True, None


def _eval_range(rule: BusinessRule, row: dict[str, Any], context: dict[str, Any]) -> tuple[bool, str | None]:
    """Check field in [min, max] from params."""
    min_v = rule.params.get("min")
    max_v = rule.params.get("max")
    for f in rule.fields:
        v = row.get(f)
        if v is None:
            continue
        try:
            if min_v is not None and v < min_v:
                return False, f"Rule {rule.name}: {f}={v} < min {min_v}"
            if max_v is not None and v > max_v:
                return False, f"Rule {rule.name}: {f}={v} > max {max_v}"
        except TypeError:
            pass
    return True, None


def _eval_sum(rule: BusinessRule, row: dict[str, Any], context: dict[str, Any]) -> tuple[bool, str | None]:
    """Check total = sum(children). Context may hold child rows."""
    # expression like "total = sum(amount)" or we use context["_children"]
    total_field = rule.params.get("total_field") or rule.fields[0] if rule.fields else None
    if not total_field:
        return True, None
    expected = row.get(total_field)
    if expected is None:
        return True, None
    children = context.get("_children", [])
    computed = sum((c.get(rule.params.get("child_field", "amount")) or 0) for c in children)
    if abs((expected or 0) - computed) > 1e-6:
        return False, f"Rule {rule.name}: total {expected} != sum(children) {computed}"
    return True, None


def _eval_equality(rule: BusinessRule, row: dict[str, Any], context: dict[str, Any]) -> tuple[bool, str | None]:
    """Check equality expression (e.g. field_a == field_b)."""
    if not rule.expression or "==" not in rule.expression:
        return True, None
    parts = rule.expression.split("==", 1)
    if len(parts) != 2:
        return True, None
    a = row.get(parts[0].strip())
    b = row.get(parts[1].strip())
    if a is None and b is None:
        return True, None
    if a != b:
        return False, f"Rule {rule.name}: {rule.expression} violated"
    return True, None
