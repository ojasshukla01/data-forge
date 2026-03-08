"""Table-level generation: full rows from schema + rules + distributions."""

from typing import Any

from data_forge.models.schema import TableDef
from data_forge.models.rules import RuleSet
from data_forge.generators.primitives import PrimitiveGenerator
from data_forge.generators.distributions import apply_distribution


def generate_table(
    table: TableDef,
    row_count: int,
    primitive_gen: PrimitiveGenerator,
    rule_set: RuleSet | None,
    parent_key_supplier: dict[str, list[Any]] | None,
    seed: int,
    offset: int = 0,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Generate rows for table. When offset/limit set, generates slice [offset:offset+limit].
    parent_key_supplier maps (table_name, column_name) or table_name -> list of PKs for FK resolution.
    """
    if limit is not None:
        end = min(offset + limit, row_count)
        n = end - offset
        if n <= 0:
            return []
        indices = range(offset, end)
    else:
        n = row_count
        indices = range(row_count)
    rows: list[dict[str, Any]] = []
    pk_columns = table.primary_key or [
        c.name for c in table.columns if c.primary_key
    ]
    dist_rules = {}
    if rule_set:
        for d in rule_set.distribution_rules:
            if d.table == table.name:
                dist_rules[d.column] = d

    for idx, i in enumerate(indices):
        row: dict[str, Any] = {}
        for col in table.columns:
            # If this column is a FK, take from parent_key_supplier
            key = (table.name, col.name)
            if parent_key_supplier:
                # Format: parent_key_supplier can be { "parent_table": [pk1, pk2, ...] }
                # and we have a relationship table -> parent_table on col.name
                supplied = parent_key_supplier.get(col.name)
                if supplied is not None and isinstance(supplied, list) and len(supplied) > idx:
                    row[col.name] = supplied[idx]
                    continue
                # Or keyed by "table.column" for child table FK column
                by_table_col = parent_key_supplier.get(f"{table.name}.{col.name}")
                if by_table_col is not None and isinstance(by_table_col, list) and len(by_table_col) > idx:
                    row[col.name] = by_table_col[idx]
                    continue
            val = primitive_gen.generate_value(col, row_index=i)
            if dist_rules.get(col.name):
                val = apply_distribution(
                    val,
                    dist_rules[col.name].distribution,
                    dist_rules[col.name].params,
                    seed + i,
                )
            row[col.name] = val
        rows.append(row)

    # Enforce uniqueness on PK/unique columns with deterministic ids
    pk_set = set(pk_columns)
    if pk_set:
        for local_i, row in enumerate(rows):
            global_i = offset + local_i
            for pk in pk_set:
                if pk in row:
                    row[pk] = seed + hash(table.name) % 100000 + global_i
    return rows
