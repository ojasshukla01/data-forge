"""API router for Custom Schema Studio / user-defined schemas."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from data_forge.api import custom_schema_store as store
from data_forge.api.schemas import (
    CustomSchemaSummary,
    CustomSchemaDetail,
    CustomSchemaVersionsResponse,
    CustomSchemaVersionInfo,
)

router = APIRouter(prefix="/api/custom-schemas", tags=["custom-schemas"])


@router.get("", response_model=list[CustomSchemaSummary])
def list_custom_schemas(limit: int = 100) -> list[CustomSchemaSummary]:
    """List custom schemas (latest version only)."""
    records = store.list_custom_schemas(limit=limit)
    out: list[CustomSchemaSummary] = []
    for r in records:
        out.append(
            CustomSchemaSummary(
                id=r["id"],
                name=r.get("name", r["id"]),
                description=r.get("description") or None,
                tags=r.get("tags") or [],
                version=int(r.get("version", 1)),
                created_at=r.get("created_at"),
                updated_at=r.get("updated_at"),
            )
        )
    return out


@router.post("", response_model=CustomSchemaDetail)
def create_custom_schema(payload: dict[str, Any]) -> CustomSchemaDetail:
    """Create a new custom schema.

    Expected payload:
    {
      "name": "...",
      "description": "...",
      "tags": [...],
      "schema": { ... SchemaModel-like dict ... }
    }
    """
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    schema = payload.get("schema")
    if not isinstance(schema, dict):
        raise HTTPException(status_code=400, detail="schema must be an object")

    rec = store.create_custom_schema(
        name=name,
        schema=schema,
        description=payload.get("description") or "",
        tags=payload.get("tags") or [],
        created_from=payload.get("created_from"),
    )
    latest_version = (rec.get("versions") or [])[-1]
    return CustomSchemaDetail(
        id=rec["id"],
        name=rec.get("name", rec["id"]),
        description=rec.get("description") or None,
        tags=rec.get("tags") or [],
        version=int(rec.get("version", 1)),
        created_at=rec.get("created_at"),
        updated_at=rec.get("updated_at"),
        schema=latest_version.get("schema") or {},
    )


@router.get("/{schema_id}", response_model=CustomSchemaDetail)
def get_custom_schema(schema_id: str) -> CustomSchemaDetail:
    rec = store.get_custom_schema(schema_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Schema not found")
    versions = rec.get("versions") or []
    if not versions:
        raise HTTPException(status_code=500, detail="Schema has no versions")
    latest = versions[-1]
    return CustomSchemaDetail(
        id=rec["id"],
        name=rec.get("name", rec["id"]),
        description=rec.get("description") or None,
        tags=rec.get("tags") or [],
        version=int(rec.get("version", 1)),
        created_at=rec.get("created_at"),
        updated_at=rec.get("updated_at"),
        schema=latest.get("schema") or {},
    )


@router.put("/{schema_id}", response_model=CustomSchemaDetail)
def update_custom_schema(schema_id: str, payload: dict[str, Any]) -> CustomSchemaDetail:
    """Update metadata and/or append a new version if schema is provided."""
    schema = payload.get("schema")
    meta = {
        "name": payload.get("name"),
        "description": payload.get("description"),
        "tags": payload.get("tags"),
    }
    rec = store.update_custom_schema(schema_id, schema=schema, **meta)
    if not rec:
        raise HTTPException(status_code=404, detail="Schema not found")
    versions = rec.get("versions") or []
    latest = versions[-1] if versions else {}
    return CustomSchemaDetail(
        id=rec["id"],
        name=rec.get("name", rec["id"]),
        description=rec.get("description") or None,
        tags=rec.get("tags") or [],
        version=int(rec.get("version", 1)),
        created_at=rec.get("created_at"),
        updated_at=rec.get("updated_at"),
        schema=latest.get("schema") or {},
    )


@router.delete("/{schema_id}")
def delete_custom_schema(schema_id: str) -> dict[str, Any]:
    if not store.delete_custom_schema(schema_id):
        raise HTTPException(status_code=404, detail="Schema not found")
    return {"deleted": schema_id}


@router.get("/{schema_id}/versions", response_model=CustomSchemaVersionsResponse)
def get_versions(schema_id: str) -> CustomSchemaVersionsResponse:
    data = store.get_custom_schema_versions(schema_id)
    if not data:
        raise HTTPException(status_code=404, detail="Schema not found")
    versions = [
        CustomSchemaVersionInfo(version=v["version"], updated_at=v.get("updated_at"))
        for v in data.get("versions") or []
    ]
    return CustomSchemaVersionsResponse(
        schema_id=data["schema_id"],
        versions=versions,
        current_version=int(data.get("current_version", 1)),
    )


@router.get("/{schema_id}/versions/{version}")
def get_version_detail(schema_id: str, version: int) -> dict[str, Any]:
    detail = store.get_custom_schema_version_detail(schema_id, version)
    if not detail:
        raise HTTPException(status_code=404, detail="Version not found")
    return detail


@router.get("/{schema_id}/diff")
def diff_versions(schema_id: str, left: int, right: int) -> dict[str, Any]:
    diff = store.diff_custom_schema_versions(schema_id, left, right)
    if not diff:
        raise HTTPException(status_code=404, detail="Cannot diff versions")
    return diff

