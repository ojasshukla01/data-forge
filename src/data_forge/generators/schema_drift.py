"""Schema drift simulation for source realism."""

import random
from typing import Any

from data_forge.models.generation import DriftProfile
from data_forge.models.schema import ColumnDef, DataType, SchemaModel, TableDef


def apply_drift(
    schema: SchemaModel,
    table_data: dict[str, list[dict[str, Any]]],
    profile: DriftProfile,
    seed: int,
) -> tuple[SchemaModel, dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """
    Apply schema drift to schema and table_data. Returns (modified schema, modified data, drift_events).
    """
    if profile == DriftProfile.NONE:
        return schema, table_data, []

    rng = random.Random(seed)
    counts = {
        DriftProfile.MILD: 1,
        DriftProfile.MODERATE: 2,
        DriftProfile.AGGRESSIVE: 4,
    }
    num_events = min(counts.get(profile, 0), sum(len(t.columns) for t in schema.tables))

    drift_events: list[dict[str, Any]] = []
    new_tables = []
    new_data = {k: [dict(r) for r in v] for k, v in table_data.items()}

    for table in schema.tables:
        tcopy = TableDef(name=table.name, columns=[ColumnDef(**c.model_dump()) for c in table.columns])
        cols = list(tcopy.columns)
        if not cols:
            new_tables.append(tcopy)
            continue

        events_this_table = 0
        max_per_table = max(1, num_events // len(schema.tables))

        for _ in range(max_per_table):
            if events_this_table >= max_per_table:
                break
            op = rng.choice(["add_column", "rename_column", "change_type", "nullability_change"])
            idx = rng.randint(0, len(cols) - 1) if cols else 0

            if op == "add_column" and rng.random() < 0.5:
                c = ColumnDef(name=f"_drift_{seed}_{len(drift_events)}", data_type=DataType.STRING, nullable=True)
                cols.append(c)
                for row in new_data.get(table.name, []):
                    row[c.name] = None
                drift_events.append({"table": table.name, "type": "add_column", "column": c.name})
                events_this_table += 1

            elif op == "rename_column" and cols:
                col = cols[idx]
                old_name = col.name
                new_name = f"{old_name}_renamed"
                col.name = new_name
                for row in new_data.get(table.name, []):
                    if old_name in row:
                        row[new_name] = row.pop(old_name)
                drift_events.append({"table": table.name, "type": "rename_column", "column": old_name, "to": new_name})
                events_this_table += 1

            elif op == "change_type" and cols:
                col = cols[idx]
                from_type = col.data_type.value
                if col.data_type == DataType.INTEGER:
                    col.data_type = DataType.STRING
                    to_type = "string"
                    for row in new_data.get(table.name, []):
                        if col.name in row and row[col.name] is not None:
                            row[col.name] = str(row[col.name])
                elif col.data_type == DataType.STRING:
                    col.data_type = DataType.INTEGER
                    to_type = "integer"
                    for row in new_data.get(table.name, []):
                        v = row.get(col.name)
                        if v is not None and isinstance(v, str) and v.isdigit():
                            row[col.name] = int(v)
                else:
                    to_type = from_type
                drift_events.append({"table": table.name, "type": "change_type", "column": col.name, "from": from_type, "to": to_type})
                events_this_table += 1

            elif op == "nullability_change" and cols:
                col = cols[idx]
                col.nullable = not col.nullable
                drift_events.append({"table": table.name, "type": "nullability_change", "column": col.name})
                events_this_table += 1

        tcopy.columns = cols
        new_tables.append(tcopy)

    new_schema = SchemaModel(
        name=schema.name,
        tables=new_tables,
        relationships=schema.relationships,
        source=schema.source,
        source_type=schema.source_type,
    )
    return new_schema, new_data, drift_events
