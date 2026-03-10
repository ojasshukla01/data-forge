"""
Versioned, nested run/scenario config schema.
Backward compatible: legacy flat configs are normalized via normalize_legacy_config().
"""

from typing import Any

from pydantic import BaseModel, Field

CONFIG_SCHEMA_VERSION = 1


class GenerationConfig(BaseModel):
    """Core generation parameters."""

    pack: str | None = None
    schema_path: str | None = None
    rules_path: str | None = None
    seed: int = 42
    scale: int = 1000
    mode: str = "full_snapshot"
    layer: str = "bronze"
    include_anomalies: bool = False
    anomaly_ratio: float = 0.02
    drift_profile: str = "none"
    messiness: str = "clean"
    batch_id: str | None = None
    change_ratio: float = 0.1
    tables_filter: list[str] | None = None
    locale: str = "en_US"
    chunk_size: int | None = None
    batch_size: int = 1000


class SimulationConfig(BaseModel):
    """Pipeline simulation options."""

    enabled: bool = False
    scenario: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    event_density: str = "medium"
    event_pattern: str = "steady"
    parallel_streams: int = 1
    late_arrival_ratio: float = 0.0
    replay_mode: str = "ordered"


class BenchmarkConfig(BaseModel):
    """Benchmark run options."""

    enabled: bool = False
    profile: str | None = None
    scale_preset: str | None = None
    parallel_tables: int = 1
    batch_size: int = 1000
    write_strategy: str = "auto"
    iterations: int = 3
    collect_stage_metrics: bool = True


class PrivacyConfig(BaseModel):
    """Privacy and PII handling."""

    mode: str = "warn"  # off | warn | strict
    redaction_enabled: bool = True


class ExportConfig(BaseModel):
    """Export and integration options."""

    format: str = "parquet"
    export_dbt: bool = False
    dbt_dir: str | None = None
    export_ge: bool = False
    ge_dir: str | None = None
    export_airflow: bool = False
    airflow_dir: str | None = None
    airflow_template: str = "generate_only"
    contracts: bool = False
    write_manifest: bool = False


class LoadConfig(BaseModel):
    """Database load and integration target."""

    load_target: str | None = None  # sqlite | duckdb | postgres | snowflake | bigquery
    db_uri: str | None = None
    load_params: dict[str, Any] = Field(default_factory=dict)


class RuntimeConfig(BaseModel):
    """Execution/runtime hints (for future use)."""

    timeout_seconds: int | None = None
    max_memory_mb: int | None = None


class RunConfig(BaseModel):
    """Top-level versioned run/scenario config."""

    schema_version: int = Field(default=CONFIG_SCHEMA_VERSION, alias="config_schema_version")
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    load: LoadConfig = Field(default_factory=LoadConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)

    model_config = {"populate_by_name": True}

    def to_flat_dict(self) -> dict[str, Any]:
        """Flatten to legacy dict for engine and API compatibility."""
        d: dict[str, Any] = {}
        g = self.generation
        d["pack"] = g.pack
        d["schema_path"] = g.schema_path
        d["rules_path"] = g.rules_path
        d["seed"] = g.seed
        d["scale"] = g.scale
        d["mode"] = g.mode
        d["layer"] = g.layer
        d["include_anomalies"] = g.include_anomalies
        d["anomaly_ratio"] = g.anomaly_ratio
        d["drift_profile"] = g.drift_profile
        d["messiness"] = g.messiness
        d["batch_id"] = g.batch_id
        d["change_ratio"] = g.change_ratio
        d["tables_filter"] = g.tables_filter
        d["locale"] = g.locale
        d["chunk_size"] = g.chunk_size
        d["batch_size"] = g.batch_size
        d["privacy_mode"] = self.privacy.mode
        d["export_format"] = self.export.format
        d["export_dbt"] = self.export.export_dbt
        d["dbt_dir"] = self.export.dbt_dir
        d["export_ge"] = self.export.export_ge
        d["ge_dir"] = self.export.ge_dir
        d["export_airflow"] = self.export.export_airflow
        d["airflow_dir"] = self.export.airflow_dir
        d["airflow_template"] = self.export.airflow_template
        d["contracts"] = self.export.contracts
        d["write_manifest"] = self.export.write_manifest
        d["load_target"] = self.load.load_target
        d["db_uri"] = self.load.db_uri
        d["load_params"] = self.load.load_params or {}
        d["pipeline_simulation"] = self.simulation.model_dump()
        d["benchmark"] = self.benchmark.model_dump()
        d["config_schema_version"] = self.schema_version
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_flat_dict(cls, raw: dict[str, Any] | None) -> "RunConfig":
        """Build RunConfig from flat or already-nested dict (legacy or new)."""
        if not raw:
            return cls()
        if "generation" in raw and isinstance(raw.get("generation"), dict):
            return cls(
                schema_version=int(raw.get("config_schema_version", CONFIG_SCHEMA_VERSION)),
                generation=GenerationConfig(**(raw.get("generation") or {})),
                simulation=SimulationConfig(**(raw.get("simulation") or {})),
                benchmark=BenchmarkConfig(**(raw.get("benchmark") or {})),
                privacy=PrivacyConfig(**(raw.get("privacy") or {})),
                export=ExportConfig(**(raw.get("export") or {})),
                load=LoadConfig(**(raw.get("load") or {})),
                runtime=RuntimeConfig(**(raw.get("runtime") or {})),
            )
        return normalize_legacy_config(raw)


def normalize_legacy_config(raw: dict[str, Any]) -> RunConfig:
    """
    Migrate legacy flat config to RunConfig.
    Old scenario JSONs and run configs remain loadable.
    """
    r = raw or {}
    # Nested blocks from legacy
    ps = r.get("pipeline_simulation")
    if isinstance(ps, dict):
        sim = SimulationConfig(**{k: v for k, v in ps.items() if k in SimulationConfig.model_fields})
    else:
        sim = SimulationConfig(enabled=bool(ps))

    bench = r.get("benchmark")
    if isinstance(bench, dict):
        bm = BenchmarkConfig(**{k: v for k, v in bench.items() if k in BenchmarkConfig.model_fields})
    else:
        bm = BenchmarkConfig(enabled=bool(bench))

    gen = GenerationConfig(
        pack=r.get("pack"),
        schema_path=r.get("schema_path"),
        rules_path=r.get("rules_path"),
        seed=int(r.get("seed", 42)),
        scale=int(r.get("scale", 1000)),
        mode=str(r.get("mode", "full_snapshot")),
        layer=str(r.get("layer", "bronze")),
        include_anomalies=bool(r.get("include_anomalies", False)),
        anomaly_ratio=float(r.get("anomaly_ratio", 0.02)),
        drift_profile=str(r.get("drift_profile", "none")),
        messiness=str(r.get("messiness", "clean")),
        batch_id=r.get("batch_id"),
        change_ratio=float(r.get("change_ratio", 0.1)),
        tables_filter=r.get("tables_filter"),
        locale=str(r.get("locale", "en_US")),
        chunk_size=r.get("chunk_size"),
        batch_size=int(r.get("batch_size", 1000)),
    )
    return RunConfig(
        schema_version=int(r.get("config_schema_version", CONFIG_SCHEMA_VERSION)),
        generation=gen,
        simulation=sim,
        benchmark=bm,
        privacy=PrivacyConfig(mode=str(r.get("privacy_mode", "warn"))),
        export=ExportConfig(
            format=str(r.get("export_format", "parquet")),
            export_dbt=bool(r.get("export_dbt", False)),
            dbt_dir=r.get("dbt_dir"),
            export_ge=bool(r.get("export_ge", False)),
            ge_dir=r.get("ge_dir"),
            export_airflow=bool(r.get("export_airflow", False)),
            airflow_dir=r.get("airflow_dir"),
            airflow_template=str(r.get("airflow_template", "generate_only")),
            contracts=bool(r.get("contracts", False)),
            write_manifest=bool(r.get("write_manifest", False)),
        ),
        load=LoadConfig(
            load_target=r.get("load_target"),
            db_uri=r.get("db_uri"),
            load_params=r.get("load_params") or {},
        ),
        runtime=RuntimeConfig(),
    )
