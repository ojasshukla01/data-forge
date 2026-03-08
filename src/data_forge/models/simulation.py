"""Models for pipeline simulation and warehouse benchmark."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventDensity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EventPattern(str, Enum):
    STEADY = "steady"
    BURST = "burst"
    SEASONAL = "seasonal"
    GROWTH = "growth"


class ReplayMode(str, Enum):
    ORDERED = "ordered"
    SHUFFLED = "shuffled"
    WINDOWED = "windowed"


class BenchmarkProfile(str, Enum):
    WIDE_TABLE = "wide_table"
    HIGH_CARDINALITY = "high_cardinality"
    EVENT_STREAM = "event_stream"
    FACT_TABLE = "fact_table"


class ScalePreset(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"


class WriteStrategy(str, Enum):
    AUTO = "auto"
    BATCH_INSERT = "batch_insert"
    BULK_COPY = "bulk_copy"
    ROW_INSERT = "row_insert"


class PipelineSimulationConfig(BaseModel):
    """Configuration for pipeline simulation datasets."""

    enabled: bool = False
    scenario: str | None = None
    start_date: str | None = None  # ISO date
    end_date: str | None = None  # ISO date
    event_density: EventDensity = EventDensity.MEDIUM
    event_pattern: EventPattern = EventPattern.STEADY
    parallel_streams: int = Field(default=1, ge=1, le=10)
    late_arrival_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    replay_mode: ReplayMode = ReplayMode.ORDERED


class BenchmarkConfig(BaseModel):
    """Configuration for warehouse benchmark runs."""

    enabled: bool = False
    profile: BenchmarkProfile | None = None
    scale_preset: ScalePreset | None = None
    parallel_tables: int = Field(default=1, ge=1, le=20)
    batch_size: int = Field(default=1000, ge=100, le=100000)
    write_strategy: WriteStrategy = WriteStrategy.AUTO
    iterations: int = Field(default=3, ge=1, le=10)
    collect_stage_metrics: bool = True


# Scale preset -> approximate row count
SCALE_PRESET_ROWS: dict[str, int] = {
    "small": 10_000,
    "medium": 100_000,
    "large": 1_000_000,
    "xlarge": 10_000_000,
}


def scale_from_preset(preset: str | None) -> int:
    """Map scale preset to row count. Returns default if unknown."""
    if not preset:
        return 1000
    return SCALE_PRESET_ROWS.get(preset.lower(), 1000)
