"""Execute GenerationRule: faker, uuid, sequence, range. Overrides generator_hint when rule exists."""

from __future__ import annotations

import random
import uuid as uuid_module
from typing import Any

from faker import Faker

from data_forge.models.rules import GenerationRule, GenerationRuleType


VALID_RULE_TYPES = {t.value for t in GenerationRuleType}


def column_rule_to_generation_rule(table: str, column: str, rule: dict[str, Any]) -> GenerationRule | None:
    """Build a GenerationRule from a column-level rule dict. Returns None if rule_type invalid."""
    rt = (rule.get("rule_type") or "").lower().strip()
    if rt not in VALID_RULE_TYPES:
        return None
    rule_type = GenerationRuleType(rt)
    params = dict(rule.get("params") or {})
    return GenerationRule(table=table, column=column, rule_type=rule_type, params=params)


def validate_generation_rule(rule: GenerationRule) -> list[str]:
    """
    Validate a single generation rule. Returns list of error messages; empty means valid.
    """
    errors: list[str] = []
    rt = rule.rule_type.value if hasattr(rule.rule_type, "value") else str(rule.rule_type)
    if rt not in VALID_RULE_TYPES:
        errors.append(f"Unknown rule_type: {rt}. Valid: faker, uuid, sequence, range, static, weighted_choice")
        return errors

    params = rule.params or {}

    # null_probability: optional float in [0, 1)
    np_val = params.get("null_probability")
    if np_val is not None:
        if not isinstance(np_val, (int, float)):
            errors.append("params.null_probability must be a number")
        elif not (0 <= np_val < 1):
            errors.append("params.null_probability must be in [0, 1)")

    if rt == "faker":
        provider = params.get("provider")
        if not provider:
            errors.append("faker rule requires params.provider")
        elif not isinstance(provider, str):
            errors.append("faker params.provider must be a string")

    elif rt == "sequence":
        start = params.get("start", 1)
        step = params.get("step", 1)
        if not isinstance(start, (int, float)):
            errors.append("sequence params.start must be a number")
        if not isinstance(step, (int, float)):
            errors.append("sequence params.step must be a number")

    elif rt == "static":
        if "value" not in params:
            errors.append("static rule requires params.value")

    elif rt == "range":
        min_v = params.get("min")
        max_v = params.get("max")
        if min_v is None and max_v is None:
            errors.append("range rule requires params.min and/or params.max")
        if min_v is not None and not isinstance(min_v, (int, float)):
            errors.append("range params.min must be a number")
        if max_v is not None and not isinstance(max_v, (int, float)):
            errors.append("range params.max must be a number")
        if min_v is not None and max_v is not None:
            try:
                if float(min_v) > float(max_v):
                    errors.append("range params.min must be <= params.max")
            except (TypeError, ValueError):
                pass

    elif rt == "weighted_choice":
        choices = params.get("choices")
        if not isinstance(choices, list):
            errors.append("weighted_choice rule requires params.choices (list)")
        elif len(choices) == 0:
            errors.append("weighted_choice params.choices must not be empty")
        else:
            weights = params.get("weights")
            if weights is not None:
                if not isinstance(weights, list):
                    errors.append("weighted_choice params.weights must be a list")
                elif len(weights) != len(choices):
                    errors.append("weighted_choice params.weights length must match params.choices")
                else:
                    for i, w in enumerate(weights):
                        if not isinstance(w, (int, float)) or w < 0:
                            errors.append(f"weighted_choice params.weights[{i}] must be a non-negative number")
                            break

    return errors


def apply_generation_rule(
    rule: GenerationRule,
    row_index: int,
    seed: int,
    locale: str = "en_US",
) -> Any:
    """
    Generate a value for a column using the given generation rule.
    If params.null_probability is set and rng.random() < p, returns None.
    """
    rt = rule.rule_type.value if hasattr(rule.rule_type, "value") else str(rule.rule_type)
    params = rule.params or {}
    rng = random.Random(seed + row_index * 37 + hash(rule.table) + hash(rule.column))

    # null_probability: optional chance to return None
    np_val = params.get("null_probability")
    if np_val is not None and isinstance(np_val, (int, float)) and 0 <= np_val < 1:
        if rng.random() < float(np_val):
            return None

    if rt == "faker":
        provider = (params.get("provider") or "name").lower()
        faker = Faker(locale)
        faker.seed_instance(seed + row_index)
        if provider in ("name", "full_name", "person"):
            return faker.name()
        if provider in ("email", "mail"):
            return faker.email()
        if provider in ("phone", "tel"):
            return faker.phone_number()
        if provider in ("company", "org", "organization"):
            return faker.company()
        if provider in ("address", "street"):
            return faker.address().replace("\n", ", ")
        if provider in ("city",):
            return faker.city()
        if provider in ("country",):
            return faker.country_code()
        if provider in ("url",):
            return faker.url()
        if provider in ("uuid", "id", "guid"):
            return str(uuid_module.uuid4())
        if hasattr(faker, provider):
            return getattr(faker, provider)()
        return faker.name()

    if rt == "uuid":
        return str(uuid_module.UUID(int=rng.getrandbits(128)))

    if rt == "sequence":
        start = int(params.get("start", 1))
        step = int(params.get("step", 1))
        return start + row_index * step

    if rt == "static":
        return params.get("value")

    if rt == "range":
        min_v = params.get("min")
        max_v = params.get("max")
        if min_v is None:
            min_v = 0
        if max_v is None:
            max_v = 100
        lo, hi = float(min_v), float(max_v)
        if lo == hi:
            return lo
        if int(lo) == lo and int(hi) == hi:
            return rng.randint(int(lo), int(hi))
        return round(rng.uniform(lo, hi), 4)

    if rt == "weighted_choice":
        choices = params.get("choices") or []
        weights = params.get("weights")
        if not choices:
            return None
        if weights is not None and len(weights) == len(choices):
            return rng.choices(choices, weights=weights, k=1)[0]
        return rng.choice(choices)

    return None
