"""Resolve FK references: assign parent PKs to child rows (1:N, N:1)."""

from __future__ import annotations

from typing import Any, Protocol

from data_forge.models.schema import SchemaModel, TableDef


class TableStoreLike(Protocol):
    def materialize_table(self, table_name: str) -> list[dict[str, Any]]: ...

    def set_table_rows(self, table_name: str, rows: list[dict[str, Any]]) -> None: ...


class RelationshipBuilder:
    """Fills in foreign key columns from parent table PKs."""

    def __init__(self, schema: SchemaModel):
        self.schema = schema

    def assign_foreign_keys(
        self,
        table_data: dict[str, list[dict[str, Any]]],
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Mutate table_data in place: for each child table, set FK columns to
        parent PK values. Parent tables must already be in table_data with PKs.
        """
        for rel in self.schema.relationships:
            parent_rows = table_data.get(rel.to_table)
            child_rows = table_data.get(rel.from_table)
            if not parent_rows or not child_rows:
                continue
            parent_pk_col = rel.to_columns[0] if rel.to_columns else _infer_pk(self.schema.get_table(rel.to_table))
            child_fk_col = rel.from_columns[0] if rel.from_columns else None
            if not parent_pk_col or not child_fk_col:
                continue
            parent_pks = [r.get(parent_pk_col) for r in parent_rows if r.get(parent_pk_col) is not None]
            if not parent_pks:
                continue
            # Assign each child row a parent PK (many-to-one: repeat parent PKs)
            for i, row in enumerate(child_rows):
                row[child_fk_col] = parent_pks[i % len(parent_pks)]
        return table_data

    def assign_foreign_keys_store(self, table_store: TableStoreLike) -> None:
        """Resolve FK values directly through a table store backend."""
        for rel in self.schema.relationships:
            parent_rows = table_store.materialize_table(rel.to_table)
            child_rows = table_store.materialize_table(rel.from_table)
            if not parent_rows or not child_rows:
                continue
            parent_pk_col = rel.to_columns[0] if rel.to_columns else _infer_pk(self.schema.get_table(rel.to_table))
            child_fk_col = rel.from_columns[0] if rel.from_columns else None
            if not parent_pk_col or not child_fk_col:
                continue
            parent_pks = [r.get(parent_pk_col) for r in parent_rows if r.get(parent_pk_col) is not None]
            if not parent_pks:
                continue
            for i, row in enumerate(child_rows):
                row[child_fk_col] = parent_pks[i % len(parent_pks)]
            table_store.set_table_rows(rel.from_table, child_rows)


def _infer_pk(table: TableDef | None) -> str | None:
    if not table:
        return None
    for pk_col in table.primary_key:
        return pk_col
    for col in table.columns:
        if col.primary_key:
            return col.name
    return table.columns[0].name if table.columns else None
