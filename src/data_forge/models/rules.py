"""Rule models: business rules, distributions, constraints."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """Kind of rule."""

    EQUALITY = "equality"  # field_a == field_b or expr
    SUM = "sum"  # total = sum(children)
    RANGE = "range"  # min <= field <= max
    ORDER = "order"  # date_a <= date_b
    REFERENCE = "reference"  # FK exists
    UNIQUENESS = "uniqueness"
    ENUM = "enum"  # value in allowed set
    PATTERN = "pattern"
    CUSTOM = "custom"  # expression or callback name


class BusinessRule(BaseModel):
    """A single business constraint."""

    name: str
    rule_type: RuleType
    table: str
    description: str | None = None
    # Expression-style: "total = sum(line_items.amount)"
    expression: str | None = None
    # Or field-level
    fields: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)
    severity: str = "error"  # error, warn


class DistributionRule(BaseModel):
    """Distribution hint for a column or table."""

    table: str
    column: str
    distribution: str  # uniform, normal, skewed, categorical, seasonal
    params: dict[str, Any] = Field(default_factory=dict)
    # e.g. {"weights": [0.7, 0.2, 0.1], "categories": ["A","B","C"]}


class GenerationRuleType(str, Enum):
    """Column value generation strategy."""

    FAKER = "faker"  # Faker provider: name, email, company, etc.
    UUID = "uuid"  # UUID v4
    SEQUENCE = "sequence"  # Integer sequence (start, step)
    RANGE = "range"  # Random in [min, max]
    STATIC = "static"  # Constant value from params.value
    WEIGHTED_CHOICE = "weighted_choice"  # Pick from choices by weight


class GenerationRule(BaseModel):
    """Per-column generation rule: faker, uuid, sequence, range."""

    table: str
    column: str
    rule_type: GenerationRuleType
    params: dict[str, Any] = Field(default_factory=dict)
    # faker: {"provider": "name"} or {"provider": "email"}
    # uuid: {}
    # sequence: {"start": 1, "step": 1}
    # range: {"min": 0, "max": 100} or {"min": 0.0, "max": 1.0}


class RuleSet(BaseModel):
    """Collection of rules for a schema or scenario."""

    name: str = "default"
    business_rules: list[BusinessRule] = Field(default_factory=list)
    distribution_rules: list[DistributionRule] = Field(default_factory=list)
    generation_rules: list[GenerationRule] = Field(default_factory=list)
    scenario: str | None = None  # e.g. "saas_billing", "ecommerce_holiday"
