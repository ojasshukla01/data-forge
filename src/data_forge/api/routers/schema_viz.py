"""Schema visualization API."""

from fastapi import APIRouter, HTTPException, Query

from data_forge.domain_packs import get_pack

router = APIRouter(prefix="/api/schema", tags=["schema"])


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
