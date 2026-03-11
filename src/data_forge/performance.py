"""Performance timing, memory estimates, and structured logging."""

import sys
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any


@contextmanager
def timed(
    stage: str,
    timings: dict[str, float],
    verbose: bool = False,
    log_fn: Callable[..., None] | None = None,
) -> Generator[None, None, None]:
    """Context manager that records elapsed seconds into timings[stage]."""
    t0 = time.perf_counter()
    if verbose and log_fn:
        log_fn("stage_start", stage=stage)
    try:
        yield
    finally:
        elapsed = time.perf_counter() - t0
        timings[f"{stage}_seconds"] = round(elapsed, 4)
        if verbose and log_fn:
            log_fn("stage_end", stage=stage, seconds=elapsed)


def estimate_peak_memory_mb(approx_rows: int, approx_cols: int = 15, bytes_per_cell: int = 50) -> float:
    """Rough estimate of peak memory (MB) for generated data. Not exact."""
    cells = approx_rows * approx_cols
    bytes_est = cells * bytes_per_cell * 2  # dict overhead, copies
    return round(bytes_est / (1024 * 1024), 1)


SCALE_WARN = 50_000  # Threshold above which chunk_size is recommended


def collect_performance_warnings(
    scale: int,
    chunk_size: int | None,
    fmt: str,
) -> list[str]:
    """Collect advisory performance warnings."""
    warnings: list[str] = []
    if scale >= SCALE_WARN and chunk_size is None:
        warnings.append(
            f"Scale {scale} requested without chunk_size; memory usage may increase. "
            "Consider --chunk-size 10000 for large runs."
        )
    if fmt.lower() in ("json",):
        warnings.append("JSON export may use more memory than CSV/JSONL for large datasets.")
    return warnings


def verbose_log(verbose: bool, event: str, **kwargs: Any) -> None:
    """Structured log when verbose. Never log secrets."""
    if not verbose:
        return
    safe = {k: v for k, v in kwargs.items() if k not in ("password", "secret", "token")}
    parts = [f"[data-forge] {event}"]
    for k, v in safe.items():
        parts.append(f" {k}={v}")
    print(" ".join(parts), file=sys.stderr, flush=True)
