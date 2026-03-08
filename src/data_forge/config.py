"""Configuration and environment presets."""

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecurityError(Exception):
    """Raised when a path is outside allowed directories."""


def ensure_path_allowed(path: Path | str, project_root: Path | None = None) -> Path:
    """
    Resolve path and ensure it is within allowed directories.
    Allowed: project_root, project_root/schemas, project_root/rules, project_root/output.
    Raises SecurityError if path escapes.
    """
    path = Path(path).resolve()
    root = (project_root or Path.cwd()).resolve()
    allowed_dirs = [
        root,
        root / "schemas",
        root / "rules",
        root / "output",
    ]
    for allowed in allowed_dirs:
        try:
            path.relative_to(allowed)
            return path
        except ValueError:
            continue
    if path == root:
        return path
    raise SecurityError("Path outside allowed directories")


class EnvironmentPreset(str, Enum):
    """Target environment for generated data."""

    UNIT_TEST = "unit-test"  # Minimal, fast, deterministic
    INTEGRATION_TEST = "integration-test"  # Realistic relations, medium volume
    LOAD_TEST = "load-test"  # High volume, performance-focused
    DEMO_DATA = "demo-data"  # Human-friendly, demo-ready
    UAT = "uat"  # UAT-like, full scenarios


class OutputFormat(str, Enum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"
    PARQUET = "parquet"
    SQL = "sql"
    NDJSON = "ndjson"


class SchemaSource(str, Enum):
    """Supported schema input sources."""

    SQL_DDL = "sql_ddl"
    JSON_SCHEMA = "json_schema"
    OPENAPI = "openapi"
    PYDANTIC = "pydantic"


class PrivacyMode(str, Enum):
    """Privacy enforcement level."""

    OFF = "off"
    WARN = "warn"
    STRICT = "strict"


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_prefix="DATA_FORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Paths
    project_root: Path = Field(default_factory=lambda: Path.cwd())
    output_dir: Path = Field(default=Path("output"))
    schemas_dir: Path = Field(default=Path("schemas"))
    rules_dir: Path = Field(default=Path("rules"))

    # Generation
    default_seed: int = 42
    default_scale: int = 1000  # Base row count scale
    environment: EnvironmentPreset = EnvironmentPreset.INTEGRATION_TEST
    anomaly_ratio: float = 0.02  # Fraction of rows to inject anomalies into
    locale: str = "en_US"

    # Export
    default_format: OutputFormat = OutputFormat.PARQUET
    sql_dialect: Literal["postgresql", "mysql", "sqlite"] = "postgresql"

    # Privacy
    privacy_mode: str = "warn"
    redaction_enabled: bool = True

    # Contracts
    contracts_dir: Path = Field(default=Path("output/contracts"))

    # Snowflake (env: DATA_FORGE_SNOWFLAKE_*)
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_warehouse: str = ""
    snowflake_database: str = ""
    snowflake_schema: str = "PUBLIC"
    snowflake_role: str = ""

    # BigQuery (env: DATA_FORGE_BIGQUERY_*)
    bigquery_project: str = ""
    bigquery_dataset: str = ""

    # dbt
    dbt_dir: Path = Field(default=Path("dbt"))

    # Run retention (runs/ metadata only; artifacts in output/ are not auto-deleted)
    runs_retention_count: int = 100  # Keep last N run records
    runs_retention_days: float | None = None  # Prune older than N days (None = disabled)

    def get_output_path(self, name: str, fmt: OutputFormat | None = None) -> Path:
        """Resolve output path for a named dataset."""
        out = self.project_root / self.output_dir
        out.mkdir(parents=True, exist_ok=True)
        ext = (fmt or self.default_format).value
        return out / f"{name}.{ext}"
