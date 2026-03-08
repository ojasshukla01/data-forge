"""Domain packs API router."""

from fastapi import APIRouter

from data_forge.domain_packs import list_packs, get_pack, get_pack_metadata
from data_forge.api.schemas import PackInfo, TableSummary

router = APIRouter(prefix="/api/domain-packs", tags=["domain-packs"])


@router.get("")
def get_domain_packs() -> list[PackInfo]:
    """List available domain packs with rich metadata."""
    packs = list_packs()
    result: list[PackInfo] = []
    for pack_id, desc in packs:
        pack = get_pack(pack_id)
        meta = get_pack_metadata(pack_id)
        count = len(pack.schema.tables) if pack else None
        rel_count = len(pack.schema.relationships) if pack else None
        result.append(
            PackInfo(
                id=pack_id,
                name=meta.get("name") if meta else None,
                description=desc,
                category=meta.get("category") if meta else None,
                tables_count=count,
                relationships_count=rel_count,
                key_entities=meta.get("key_entities") if meta else None,
                recommended_use_cases=meta.get("recommended_use_cases") if meta else None,
                supported_features=meta.get("supported_features") if meta else None,
                supports_event_streams=meta.get("supports_event_streams", False) if meta else False,
                simulation_event_types=meta.get("simulation_event_types") if meta else None,
                benchmark_relevance=meta.get("benchmark_relevance") if meta else None,
            )
        )
    return result


@router.get("/{pack_id}")
def get_pack_detail(pack_id: str) -> dict:
    """Get pack details including tables, schema, and rich metadata."""
    pack = get_pack(pack_id)
    if not pack:
        return {"error": "Pack not found"}
    meta = get_pack_metadata(pack_id)
    tables = [
        TableSummary(
            name=t.name,
            columns=[c.name for c in t.columns],
            primary_key=t.primary_key or [c.name for c in t.columns if getattr(c, "primary_key", False)],
            row_estimate=getattr(t, "row_estimate", None),
        )
        for t in pack.schema.tables
    ]
    out = {
        "id": pack_id,
        "name": pack.name,
        "description": pack.description,
        "tables": [t.model_dump() for t in tables],
        "relationships_count": len(pack.schema.relationships),
    }
    if meta:
        out["category"] = meta.get("category")
        out["key_entities"] = meta.get("key_entities")
        out["recommended_use_cases"] = meta.get("recommended_use_cases")
        out["supported_features"] = meta.get("supported_features")
        out["supports_event_streams"] = meta.get("supports_event_streams", False)
        out["simulation_event_types"] = meta.get("simulation_event_types")
        out["benchmark_relevance"] = meta.get("benchmark_relevance")
    return out
