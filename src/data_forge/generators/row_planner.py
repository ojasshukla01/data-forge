"""
Row/cardinality planning for generation. Decouples "how many rows per table" from the main pipeline.

The default planner uses table-name heuristics for backward compatibility. Override or extend
via a custom planner for domain-agnostic or relationship-aware cardinality (future).
"""

from typing import Protocol

from data_forge.models.schema import SchemaModel, TableDef


class RowPlanner(Protocol):
    """Protocol for computing row counts per table from schema and scale."""

    def plan_row_counts(
        self,
        schema: SchemaModel,
        scale: int,
        tables_filter: list[str] | None = None,
    ) -> dict[str, int]:
        """Return map of table name -> row count. Only tables in dependency order (and filter) need entries."""
        ...


def default_plan_row_counts(
    schema: SchemaModel,
    scale: int,
    tables_filter: list[str] | None = None,
) -> dict[str, int]:
    """
    Default row planner: uses table-name heuristics for backward compatibility.
    - users, customers, organizations, products -> scale
    - orders, invoices, subscriptions -> max(scale//2, scale*2)
    - table name containing line/item/detail -> scale * 3
    - else -> scale
    """
    tables_order = schema.dependency_order()
    if tables_filter:
        tables_order = [t for t in tables_order if t.name in tables_filter]
    result: dict[str, int] = {}
    for table in tables_order:
        result[table.name] = _row_count_for_table(table, scale)
    return result


def _row_count_for_table(table: TableDef, scale: int) -> int:
    """Single-table row count using current heuristics. Kept separate for testing and overrides."""
    if table.name in ("users", "customers", "organizations", "products"):
        return scale
    if table.name in ("orders", "invoices", "subscriptions"):
        return max(scale // 2, scale * 2)
    if "line" in table.name or "item" in table.name or "detail" in table.name:
        return scale * 3
    return scale
