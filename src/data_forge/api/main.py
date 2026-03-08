"""Data Forge API - FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data_forge.api.routers import domain_packs, generate, preflight, validate, artifacts, schema_viz, runs, benchmark, scenarios
from data_forge.api.schemas import HealthResponse
from data_forge import __version__

app = FastAPI(
    title="Data Forge API",
    description="Schema-aware synthetic data platform API",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", version=__version__)
