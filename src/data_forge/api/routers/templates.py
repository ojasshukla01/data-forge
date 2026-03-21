"""Templates API: unified list of built-in + user templates with CRUD operations."""

from typing import Any

from fastapi import APIRouter, HTTPException

from data_forge.api import custom_schema_store as schema_store
from data_forge.api import template_registry as registry
from data_forge.api.schemas import PackInfo
from data_forge.domain_packs import get_pack, get_pack_metadata, list_packs

router = APIRouter(prefix="/api/templates", tags=["templates"])


def _pack_to_info(pack_id: str, source: str = "builtin") -> PackInfo | None:
    pack = get_pack(pack_id)
    if not pack:
        return None
    meta = get_pack_metadata(pack_id)
    count = len(pack.schema.tables) if pack else None
    rel_count = len(pack.schema.relationships) if pack else None
    desc = next((d for pid, d in list_packs() if pid == pack_id), "")
    return PackInfo(
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
        source=source,
    )


def _schema_to_info(rec: dict[str, Any]) -> PackInfo:
    schema = (rec.get("versions") or [{}])[-1].get("schema") or {}
    tables = schema.get("tables") or []
    rels = schema.get("relationships") or []
    return PackInfo(
        id=rec["id"],
        name=rec.get("name", rec["id"]),
        description=rec.get("description") or "Custom schema",
        category="Custom",
        tables_count=len(tables),
        relationships_count=len(rels),
        key_entities=[t.get("name") for t in tables[:5] if t.get("name")],
        source="user",
    )


@router.get("", response_model=list[PackInfo])
def list_templates() -> list[PackInfo]:
    """List all templates: built-in (not hidden) + user templates."""
    hidden = set(registry.get_hidden_builtin())
    user_ids = registry.get_user_template_ids()
    result: list[PackInfo] = []

    for pack_id, _ in list_packs():
        if pack_id in hidden:
            continue
        info = _pack_to_info(pack_id, source="builtin")
        if info:
            result.append(info)

    for schema_id in user_ids:
        rec = schema_store.get_custom_schema(schema_id)
        if rec:
            result.append(_schema_to_info(rec))

    return result


@router.post("/from-pack/{pack_id}", response_model=PackInfo)
def add_template_from_pack(pack_id: str) -> PackInfo:
    """Clone a built-in pack to a custom schema and add as user template."""
    pack = get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    meta = get_pack_metadata(pack_id)
    name = meta.get("name", pack_id.replace("_", " ").title()) if meta else pack_id.replace("_", " ").title()
    schema_dict = pack.schema.model_dump()
    rec = schema_store.create_custom_schema(
        name=f"{name} (template)",
        schema=schema_dict,
        description=pack.description,
        tags=["template", "from-pack"],
        created_from=f"pack:{pack_id}",
    )
    schema_id = rec["id"]
    registry.add_user_template(schema_id)
    return _schema_to_info(rec)


@router.post("/from-schema/{schema_id}", response_model=PackInfo)
def add_template_from_schema(schema_id: str) -> PackInfo:
    """Add an existing custom schema as a user template."""
    rec = schema_store.get_custom_schema(schema_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Schema not found")
    registry.add_user_template(schema_id)
    return _schema_to_info(rec)


@router.delete("/{template_id}")
def remove_template(template_id: str) -> dict[str, str]:
    """Remove a template: hide built-in, or remove user template from list."""
    if template_id.startswith("schema_"):
        if registry.remove_user_template(template_id):
            return {"status": "removed", "id": template_id}
        raise HTTPException(status_code=404, detail="User template not found")
    if registry.hide_builtin(template_id):
        return {"status": "hidden", "id": template_id}
    raise HTTPException(status_code=404, detail="Template not found")


@router.post("/{template_id}/unhide")
def unhide_template(template_id: str) -> dict[str, str]:
    """Unhide a previously hidden built-in pack."""
    if registry.unhide_builtin(template_id):
        return {"status": "unhidden", "id": template_id}
    raise HTTPException(status_code=404, detail="Pack was not hidden")


@router.get("/hidden")
def list_hidden() -> list[str]:
    """List hidden built-in pack IDs (for restore UI)."""
    return registry.get_hidden_builtin()
