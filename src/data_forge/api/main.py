"""Data Forge API - FastAPI application."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data_forge.api.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    RequestSizeLimitMiddleware,
)
from data_forge.api.routers import (
    domain_packs,
    generate,
    preflight,
    validate,
    artifacts,
    schema_viz,
    runs,
    benchmark,
    scenarios,
    custom_schemas,
)
from data_forge.api.schemas import HealthResponse, HealthReadyResponse
from data_forge import __version__
from data_forge.config import Settings

app = FastAPI(
    title="Data Forge API",
    description="Schema-aware synthetic data platform API",
    version=__version__,
)

settings = Settings()


def _allowed_origins() -> list[str]:
    raw = os.getenv("DATA_FORGE_CORS_ALLOW_ORIGINS", "")
    if not raw.strip():
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    vals = [v.strip() for v in raw.split(",")]
    return [v for v in vals if v]

app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(domain_packs.router)
app.include_router(generate.router)
app.include_router(preflight.router)
app.include_router(validate.router)
app.include_router(artifacts.router)
app.include_router(schema_viz.router)
app.include_router(runs.router)
app.include_router(benchmark.router)
app.include_router(scenarios.router)
app.include_router(custom_schemas.router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@app.get("/health/ready", response_model=HealthReadyResponse)
def health_ready() -> HealthReadyResponse:
    output_dir = (settings.project_root / settings.output_dir).resolve()
    checks = {"output_dir_writable": False}
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".ready_check.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        checks["output_dir_writable"] = True
    except OSError:
        checks["output_dir_writable"] = False
    status = "ok" if all(checks.values()) else "degraded"
    return HealthReadyResponse(status=status, version=__version__, checks=checks)
