"""Schema visualization and preview API."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from data_forge.domain_packs import get_pack
from data_forge.generators.generation_rules import apply_generation_rule, column_rule_to_generation_rule
from data_forge.models.schema import SchemaModel

router = APIRouter(prefix="/api/schema", tags=["schema"])


def _sample_value_for_type(data_type: str, row_idx: int) -> Any:
    """Generate a sample value for preview based on data type."""
    dt = (data_type or "string").lower()
    if dt in ("integer", "bigint"):
        return row_idx + 1
    if dt in ("float", "decimal", "percent", "currency"):
        return round(1.0 + row_idx * 0.1, 2)
    if dt == "boolean":
        return row_idx % 2 == 0
    if dt == "uuid":
        return str(uuid.uuid4())
    if dt == "email":
        return f"user{row_idx + 1}@example.com"
    if dt == "date":
        return str(date(2024, 1, 1 + row_idx))
    if dt in ("datetime", "timestamp"):
        return datetime(2024, 1, 1 + row_idx, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    if dt == "phone":
        return f"+1-555-{100 + row_idx:04d}"
    if dt == "url":
        return f"https://example.com/item/{row_idx + 1}"
    return f"sample_{row_idx + 1}"


@router.post("/preview")
def preview_sample_data(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """
    Generate sample rows for a schema (preview, no persistence).
    Body: { "schema": SchemaModel-like dict, "rows_per_table": int (default 3) }
    Returns: { "table_name": [row1, row2, ...], ... }
    """
    schema_dict = payload.get("schema")
    if not isinstance(schema_dict, dict):
        raise HTTPException(status_code=400, detail="schema is required and must be an object")
    try:
        model = SchemaModel.model_validate(schema_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid schema: {e}") from e
    # Safety: cap tables and rows to avoid excessive preview load
    if len(model.tables) > 50:
        raise HTTPException(status_code=400, detail="Schema has too many tables for preview (max 50)")
    n = int(payload.get("rows_per_table", 3))
    n = min(max(n, 1), 20)
    out: dict[str, list[dict[str, Any]]] = {}
    seed = 42
    for t in model.tables:
        rows = []
        for i in range(n):
            row: dict[str, Any] = {}
            for c in t.columns:
                if getattr(c, "generation_rule", None):
                    rule_dict = {"rule_type": c.generation_rule.rule_type, "params": c.generation_rule.params}
                    gr = column_rule_to_generation_rule(t.name, c.name, rule_dict)
                    if gr is not None:
                        row[c.name] = apply_generation_rule(gr, i, seed, locale="en_US")
                    else:
                        dt = getattr(c.data_type, "value", str(c.data_type)) if hasattr(c.data_type, "value") else str(c.data_type)
                        row[c.name] = _sample_value_for_type(dt, i)
                else:
                    dt = getattr(c.data_type, "value", str(c.data_type)) if hasattr(c.data_type, "value") else str(c.data_type)
                    row[c.name] = _sample_value_for_type(dt, i)
            rows.append(row)
        out[t.name] = rows
    return out


@router.get("/visualize")
def visualize_schema(pack_id: str = Query(..., description="Domain pack ID")) -> dict:
    """
    Return schema structure as nodes and edges for graph visualization.
    Uses domain pack schema; relationships become edges.
    """
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack not found: {pack_id}")
    schema = pack.schema
    nodes = []
    edges = []
    for i, t in enumerate(schema.tables):
        pk = t.primary_key or [c.name for c in t.columns if getattr(c, "primary_key", False)]
        cols = [
            {
                "name": c.name,
                "type": getattr(c.data_type, "value", str(c.data_type)),
                "nullable": c.nullable,
                "pk": c.name in pk,
            }
            for c in t.columns
        ]
        nodes.append({
            "id": t.name,
            "type": "table",
            "data": {
                "label": t.name,
                "columns": cols,
                "primaryKey": pk,
            },
            "position": {"x": (i % 4) * 260, "y": (i // 4) * 200},
        })
    seen: set[tuple[str, str]] = set()
    for r in schema.relationships:
        key = (r.from_table, r.to_table, tuple(r.from_columns), tuple(r.to_columns))
        if key in seen:
            continue
        seen.add(key)
        edges.append({
            "id": f"e-{r.from_table}-{r.to_table}-{r.name}",
            "source": r.from_table,
            "target": r.to_table,
            "label": r.name,
        })
    return {"nodes": nodes, "edges": edges, "pack_id": pack_id}
