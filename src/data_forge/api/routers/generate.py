"""Generate API router."""

from typing import Any

from fastapi import APIRouter, HTTPException

from data_forge.api.schemas import GenerateRequest
from data_forge.api.services import run_generate

router = APIRouter(prefix="/api", tags=["generate"])


@router.post("/generate")
def api_generate(req: GenerateRequest) -> dict[str, Any]:
    """Run synthetic data generation."""
    result = run_generate(req)
    if not result.get("success") and result.get("errors"):
        raise HTTPException(status_code=400, detail=result["errors"])
    return result
