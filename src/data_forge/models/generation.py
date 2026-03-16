"""Models for generation requests, results, and provenance."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GenerationMode(str, Enum):
    """How data is generated: full snapshot, incremental, or CDC change events."""

    FULL_SNAPSHOT = "full_snapshot"
    INCREMENTAL = "incremental"
    CDC = "cdc"


class DataLayer(str, Enum):
    """Data layer: bronze (raw), silver (cleaned), gold (curated), or all."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    ALL = "all"


class DriftProfile(str, Enum):
    """Schema drift intensity for source simulation."""

    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class MessinessProfile(str, Enum):
    """Source system messiness level for bronze generation."""

    CLEAN = "clean"
    REALISTIC = "realistic"
    CHAOTIC = "chaotic"


class Provenance(BaseModel):
    """Provenance for a row or field: why it exists and how it was produced."""

    template_id: str | None = None
    rule_ids: list[str] = Field(default_factory=list)
    anomaly_injected: str | None = None
    parent_record_ref: str | None = None  # e.g. "orders#123"
    seed_used: int | None = None


class TableSnapshot(BaseModel):
    """Generated data for one table with optional provenance."""

    table_name: str
    columns: list[str]
    rows: list[dict[str, Any]]
    provenance: list[Provenance] | None = None  # One per row if explain mode
    row_count: int = 0
    layer: str | None = None  # bronze, silver, gold
    cdc_events: list[dict[str, Any]] | None = None  # For CDC mode

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.rows and not self.row_count:
            self.row_count = len(self.rows)
        if self.rows and not self.columns:
            self.columns = list(self.rows[0].keys())


class GenerationRequest(BaseModel):
    """Request to generate synthetic data."""

    schema_name: str
    rule_set_name: str | None = None
    seed: int = 42
    scale: int = 1000
    environment: str = "integration-test"
    include_anomalies: bool = False
    anomaly_ratio: float = 0.02
    with_provenance: bool = False
    tables_filter: list[str] | None = None  # If set, only these tables
    locale: str = "en_US"
    # ETL / ELT realism
    mode: GenerationMode = GenerationMode.FULL_SNAPSHOT
    layer: DataLayer = DataLayer.BRONZE
    batch_id: str | None = None
    change_ratio: float = 0.1  # Fraction of rows that are new/changed (incremental/cdc)
    drift_profile: DriftProfile = DriftProfile.NONE
    messiness: MessinessProfile = MessinessProfile.CLEAN
    privacy_mode: str = "warn"  # off | warn | strict
    privacy_policy_mode: str = "advisory"  # advisory | enforce
    privacy_policy_max_risk_score: int | None = None
    privacy_policy_max_sensitive_columns: int | None = None
    privacy_policy_fail_on_high_risk: bool = False
    privacy_policy_block_categories: list[str] | None = None
    load_target: str | None = None  # sqlite | duckdb | postgres | snowflake | bigquery
    db_uri: str | None = None  # connection string or path
    load_params: dict[str, Any] | None = None  # cloud-specific (sf-*, bq-*)
    chunk_size: int | None = None  # generate large tables in chunks
    batch_size: int = 1000  # batch size for DB inserts
    export_format: str | None = None  # for performance warnings (parquet, csv, json, etc.)
    layer_materialization: str = "eager"  # eager | lazy (lazy reduces layer=all memory pressure)


class GenerationResult(BaseModel):
    """Result of a generation run."""

    request: GenerationRequest
    tables: list[TableSnapshot] = Field(default_factory=list)
    quality_report: dict[str, Any] = Field(default_factory=dict)
    duration_seconds: float = 0.0
    success: bool = True
    errors: list[str] = Field(default_factory=list)
    layers_data: dict[str, dict[str, list[dict[str, Any]]]] | None = None  # bronze/silver/gold when layer=all
    drift_events: list[dict[str, Any]] = Field(default_factory=list)
    warehouse_load: dict[str, Any] | None = None  # load result when load_target set
    timings: dict[str, float] = Field(default_factory=dict)
    performance_warnings: list[str] = Field(default_factory=list)
    benchmark_results: dict[str, Any] | None = None
