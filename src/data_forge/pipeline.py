"""
Pipeline stage constants and timing helpers for the generation pipeline.
Stages: plan, generate, resolve_fk, drift, cdc, messiness, anomalies, layers, quality, export.
"""

import time
from contextlib import contextmanager
from collections.abc import Generator

# Stage keys for timings dict (suffix _seconds is added by timed_stage)
STAGE_SCHEMA_LOAD = "schema_load"
STAGE_RULE_LOAD = "rule_load"
STAGE_GENERATE = "generation"
STAGE_RESOLVE_FK = "resolve_fk"
STAGE_DRIFT = "drift"
STAGE_CDC = "cdc"
STAGE_MESSINESS = "messiness"
STAGE_ANOMALIES = "anomalies"
STAGE_LAYERS = "layers"
STAGE_QUALITY = "quality"
STAGE_EXPORT = "export"
STAGE_WAREHOUSE_LOAD = "warehouse_load"


@contextmanager
def timed_stage(
    stage: str,
    timings: dict[str, float],
) -> Generator[None, None, None]:
    """Record elapsed seconds for a pipeline stage into timings[stage + '_seconds']."""
    t0 = time.perf_counter()
    try:
        yield
    finally:
        key = f"{stage}_seconds" if not stage.endswith("_seconds") else stage
        timings[key] = round(time.perf_counter() - t0, 4)
