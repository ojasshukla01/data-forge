"""Pydantic request/response models for the API."""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class GenerationMode(str, Enum):
    FULL_SNAPSHOT = "full_snapshot"
    INCREMENTAL = "incremental"
    CDC = "cdc"


class DataLayer(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    ALL = "all"


class DriftProfile(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class MessinessProfile(str, Enum):
    CLEAN = "clean"
    REALISTIC = "realistic"
    CHAOTIC = "chaotic"


class PipelineSimulationSchema(BaseModel):
    """Pipeline simulation config for API requests."""

    enabled: bool = False
    scenario: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    event_density: str = "medium"
    event_pattern: str = "steady"
    parallel_streams: int = 1
    late_arrival_ratio: float = 0.0
    replay_mode: str = "ordered"


class BenchmarkConfigSchema(BaseModel):
    """Benchmark config for API requests."""

    enabled: bool = False
    profile: str | None = None
    scale_preset: str | None = None
    parallel_tables: int = 1
    batch_size: int = 1000
    write_strategy: str = "auto"
    iterations: int = 3
    collect_stage_metrics: bool = True


class GenerateRequest(BaseModel):
    """Request body for /api/generate."""

    pack: str | None = None
    custom_schema_id: str | None = None  # Use schema from Custom Schema Studio
    schema_path: str | None = None
    rules_path: str | None = None
    schema_text: str | None = None
    schema_format: str | None = None  # sql, json
    seed: int = 42
    scale: int = 1000
    include_anomalies: bool = False
    anomaly_ratio: float = 0.02
    mode: GenerationMode = GenerationMode.FULL_SNAPSHOT
    layer: DataLayer = DataLayer.BRONZE
    drift_profile: DriftProfile = DriftProfile.NONE
    messiness: MessinessProfile = MessinessProfile.CLEAN
    privacy_mode: str = "warn"
    export_format: str = "parquet"
    load_target: str | None = None
    db_uri: str | None = None
    load_params: dict[str, Any] | None = None
    chunk_size: int | None = None
    batch_size: int = 1000
    export_ge: bool = False
    ge_dir: str | None = None
    export_airflow: bool = False
    airflow_dir: str | None = None
    airflow_template: str = "generate_only"
    export_dbt: bool = False
    dbt_dir: str | None = None
    contracts: bool = False
    batch_id: str | None = None
    change_ratio: float = 0.1
    write_manifest: bool = False
    pipeline_simulation: PipelineSimulationSchema | None = None
    benchmark: BenchmarkConfigSchema | None = None


class ValidateRequest(BaseModel):
    """Request for /api/validate."""

    schema_path: str
    data_path: str
    rules_path: str | None = None
    privacy_mode: str = "off"


class SchemaParseRequest(BaseModel):
    """Request for /api/schema/parse."""

    text: str
    format: str  # sql, json


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class PackInfo(BaseModel):
    id: str
    name: str | None = None
    description: str
    category: str | None = None
    tables_count: int | None = None
    relationships_count: int | None = None
    key_entities: list[str] | None = None
    recommended_use_cases: list[str] | None = None
    supported_features: list[str] | None = None
    supports_event_streams: bool = False
    simulation_event_types: list[str] | None = None
    benchmark_relevance: str | None = None  # low | medium | high


class TableSummary(BaseModel):
    name: str
    columns: list[str]
    primary_key: list[str]
    row_estimate: int | None = None


class CustomSchemaSummary(BaseModel):
    """Summary view of a custom schema in the registry."""

    id: str
    name: str
    description: str | None = None
    tags: list[str] | None = None
    version: int
    created_at: float | None = None
    updated_at: float | None = None


class CustomSchemaDetail(BaseModel):
    """Full custom schema definition and metadata."""

    id: str
    name: str
    description: str | None = None
    tags: list[str] | None = None
    version: int
    created_at: float | None = None
    updated_at: float | None = None
    schema: dict[str, Any]


class CustomSchemaVersionInfo(BaseModel):
    version: int
    updated_at: float | None = None


class CustomSchemaVersionsResponse(BaseModel):
    schema_id: str
    versions: list[CustomSchemaVersionInfo]
    current_version: int


class CustomSchemaCreate(BaseModel):
    """Request body for POST /api/custom-schemas."""

    name: str
    schema: dict[str, Any]
    description: str | None = None
    tags: list[str] | None = None
    created_from: str | None = None


class CustomSchemaUpdate(BaseModel):
    """Request body for PUT /api/custom-schemas/{schema_id}."""

    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    schema: dict[str, Any] | None = None


class CustomSchemaValidateRequest(BaseModel):
    """Request body for POST /api/custom-schemas/validate."""

    schema: dict[str, Any]


class CustomSchemaValidateResponse(BaseModel):
    """Response for POST /api/custom-schemas/validate."""

    valid: bool
    errors: list[str] = []
