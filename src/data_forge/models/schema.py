"""Schema models: tables, columns, relationships, data types."""

from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, Field


class DataType(str, Enum):
    """Logical data types for column generation."""

    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    BIGINT = "bigint"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIMESTAMP = "timestamp"
    UUID = "uuid"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    JSON = "json"
    ENUM = "enum"
    CURRENCY = "currency"
    PERCENT = "percent"


class ColumnGenerationRule(BaseModel):
    """Per-column generation rule embedded in schema. Overrides generator_hint when present."""

    rule_type: str  # faker, uuid, sequence, range
    params: dict[str, Any] = Field(default_factory=dict)


class ColumnDef(BaseModel):
    """Definition of a single column."""

    name: str
    data_type: DataType = DataType.STRING
    nullable: bool = True
    unique: bool = False
    primary_key: bool = False
    default: Any = None
    min_length: int | None = None
    max_length: int | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    enum_values: list[str] | None = None
    pattern: str | None = None
    check: str | None = None  # Check constraint expression, e.g. "amount >= 0"
    generator_hint: str | None = None  # e.g. "name", "email", "company"
    generation_rule: ColumnGenerationRule | None = None  # Overrides generator_hint
    description: str | None = None
    display_name: str | None = None  # Human-friendly label for UI


class RelationshipDef(BaseModel):
    """Foreign key / relationship between tables."""

    name: str
    from_table: str
    from_columns: list[str]
    to_table: str
    to_columns: list[str]
    cardinality: str = "many-to-one"  # many-to-one, one-to-one, one-to-many
    optional: bool = False
    on_delete: str | None = None  # CASCADE, SET NULL, etc.


class TableDef(BaseModel):
    """Definition of a table/entity."""

    name: str
    columns: list[ColumnDef] = Field(default_factory=list)
    primary_key: list[str] = Field(default_factory=list)
    unique_constraints: list[list[str]] | None = None  # Multi-column unique, e.g. [["org_id", "slug"]]
    description: str | None = None
    row_estimate: int | None = None  # Hint for scale
    order: int = 0  # Generation order (dependencies first)
    tags: list[str] | None = None  # Labels for grouping


class SchemaModel(BaseModel):
    """Full schema: multiple tables and relationships."""

    name: str = "default"
    description: str | None = None  # Schema-level description
    tables: list[TableDef] = Field(default_factory=list)
    relationships: list[RelationshipDef] = Field(default_factory=list)
    source: str | None = None  # File path or identifier
    source_type: str | None = None  # sql_ddl, json_schema, openapi

    def get_table(self, name: str) -> TableDef | None:
        """Get table by name."""
        for t in self.tables:
            if t.name == name:
                return t
        return None

    def get_relationships_from(self, table: str) -> list[RelationshipDef]:
        """Relationships where this table is the parent (from)."""
        return [r for r in self.relationships if r.from_table == table]

    def get_relationships_to(self, table: str) -> list[RelationshipDef]:
        """Relationships where this table is the child (to)."""
        return [r for r in self.relationships if r.to_table == table]

    def dependency_order(self) -> list[TableDef]:
        """Return tables in order suitable for generation (parents first)."""
        # Topological sort: table with FK (from_table) depends on to_table; we want to_table first
        table_names = {t.name for t in self.tables}
        in_degree = dict.fromkeys(table_names, 0)
        for r in self.relationships:
            if r.from_table in table_names:
                in_degree[r.from_table] = in_degree.get(r.from_table, 0) + 1
        order: list[str] = []
        remaining = set(table_names)
        while remaining:
            ready = [n for n in remaining if in_degree[n] == 0]
            if not ready:
                ready = list(remaining)
            for n in sorted(ready):
                order.append(n)
                remaining.discard(n)
                for r in self.relationships:
                    if r.to_table == n and r.from_table in remaining:
                        in_degree[r.from_table] -= 1
        name_to_table = {t.name: t for t in self.tables}
        return [name_to_table[n] for n in order if n in name_to_table]

    MAX_TABLES: ClassVar[int] = 100
    MAX_COLUMNS_PER_TABLE: ClassVar[int] = 200
    MAX_RELATIONSHIPS: ClassVar[int] = 100

    def validate_schema(self) -> list[str]:
        """
        Validate schema structure. Returns list of error messages; empty means valid.
        Checks: size limits, unique table names, unique column names per table,
        primary_key refs, unique_constraints refs, relationship table/column refs.
        """
        errors: list[str] = []
        if len(self.tables) > self.MAX_TABLES:
            errors.append(f"Schema exceeds maximum tables ({self.MAX_TABLES})")
        for t in self.tables:
            if len(t.columns) > self.MAX_COLUMNS_PER_TABLE:
                errors.append(f"Table '{t.name}' exceeds maximum columns ({self.MAX_COLUMNS_PER_TABLE})")
        if len(self.relationships) > self.MAX_RELATIONSHIPS:
            errors.append(f"Schema exceeds maximum relationships ({self.MAX_RELATIONSHIPS})")
        table_names = [t.name for t in self.tables]
        if len(table_names) != len(set(table_names)):
            seen: dict[str, int] = {}
            for n in table_names:
                seen[n] = seen.get(n, 0) + 1
            for n, cnt in seen.items():
                if cnt > 1:
                    errors.append(f"Duplicate table name: {n}")

        name_to_table = {t.name: t for t in self.tables}
        for t in self.tables:
            col_names = [c.name for c in t.columns]
            if len(col_names) != len(set(col_names)):
                seen_c: dict[str, int] = {}
                for n in col_names:
                    seen_c[n] = seen_c.get(n, 0) + 1
                for n, cnt in seen_c.items():
                    if cnt > 1:
                        errors.append(f"Table '{t.name}': duplicate column name: {n}")

            for pk in t.primary_key:
                if pk not in col_names:
                    errors.append(f"Table '{t.name}': primary_key '{pk}' not in columns")

            for uc in t.unique_constraints or []:
                for col in uc:
                    if col not in col_names:
                        errors.append(f"Table '{t.name}': unique_constraint column '{col}' not in columns")

        for r in self.relationships:
            if r.from_table not in name_to_table:
                errors.append(f"Relationship '{r.name}': from_table '{r.from_table}' not found")
            if r.to_table not in name_to_table:
                errors.append(f"Relationship '{r.name}': to_table '{r.to_table}' not found")
            if r.from_table in name_to_table:
                from_cols = [col.name for col in name_to_table[r.from_table].columns]
                for col_name in r.from_columns:
                    if col_name not in from_cols:
                        errors.append(f"Relationship '{r.name}': from_column '{col_name}' not in table '{r.from_table}'")
            if r.to_table in name_to_table:
                to_cols = [col.name for col in name_to_table[r.to_table].columns]
                for col_name in r.to_columns:
                    if col_name not in to_cols:
                        errors.append(f"Relationship '{r.name}': to_column '{col_name}' not in table '{r.to_table}'")

        for t in self.tables:
            for c in t.columns:
                if c.generation_rule is None:
                    continue
                from data_forge.generators.generation_rules import (
                    column_rule_to_generation_rule,
                    validate_generation_rule,
                )
                rule_dict = {"rule_type": c.generation_rule.rule_type, "params": c.generation_rule.params}
                gr = column_rule_to_generation_rule(t.name, c.name, rule_dict)
                if gr is None:
                    errors.append(f"Table '{t.name}' column '{c.name}': invalid rule_type '{c.generation_rule.rule_type}'. Use: faker, uuid, sequence, range, static, weighted_choice")
                else:
                    val_errs = validate_generation_rule(gr)
                    for e in val_errs:
                        errors.append(f"Table '{t.name}' column '{c.name}': {e}")

        return errors

    def collect_warnings(self) -> list[str]:
        """
        Collect advisory warnings (non-blocking). Returns list of warning messages.
        """
        warnings: list[str] = []
        for t in self.tables:
            if not t.columns:
                warnings.append(f"Table '{t.name}' has no columns")
        for r in self.relationships:
            if r.from_table == r.to_table:
                warnings.append(f"Relationship '{r.name}': self-reference (from_table == to_table)")
        return warnings
