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


class RuleSet(BaseModel):
    """Collection of rules for a schema or scenario."""

    name: str = "default"
    business_rules: list[BusinessRule] = Field(default_factory=list)
    distribution_rules: list[DistributionRule] = Field(default_factory=list)
    scenario: str | None = None  # e.g. "saas_billing", "ecommerce_holiday"
