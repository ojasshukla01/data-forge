"""Schema models: tables, columns, relationships, data types."""

from enum import Enum
from typing import Any

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
    generator_hint: str | None = None  # e.g. "name", "email", "company"
    description: str | None = None


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
    description: str | None = None
    row_estimate: int | None = None  # Hint for scale
    order: int = 0  # Generation order (dependencies first)


class SchemaModel(BaseModel):
    """Full schema: multiple tables and relationships."""

    name: str = "default"
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
        in_degree = {n: 0 for n in table_names}
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
