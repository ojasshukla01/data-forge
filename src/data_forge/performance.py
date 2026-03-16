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
LARGE_RUN_ROW_THRESHOLD = 200_000
LARGE_RUN_CELL_THRESHOLD = 3_000_000


def collect_performance_warnings(
    scale: int,
    chunk_size: int | None,
    fmt: str,
) -> list[str]:
    """Collect advisory performance warnings. Chunking reduces per-chunk peak but full table is still held in memory until export."""
    warnings: list[str] = []
    if scale >= SCALE_WARN and chunk_size is None:
        warnings.append(
            f"Scale {scale} requested without chunk_size; memory usage may increase. "
            "Consider --chunk-size 10000 for large runs."
        )
    if scale >= SCALE_WARN and chunk_size and scale > chunk_size:
        warnings.append(
            "Chunking is enabled; rows are still accumulated in memory per table before export. "
            "For very large runs, monitor memory usage."
        )
    if fmt.lower() in ("json",):
        warnings.append("JSON export may use more memory than CSV/JSONL for large datasets.")
    return warnings


def build_materialization_diagnostics(
    row_counts: dict[str, int],
    approx_cols_by_table: dict[str, int],
    layer: str,
) -> dict[str, Any]:
    """
    Build a lightweight diagnostic for memory/materialization risk before export.
    This does not guarantee memory usage; it provides practical local-run guidance.
    """
    total_rows = sum(max(v, 0) for v in row_counts.values())
    total_cells = 0
    for table_name, rows in row_counts.items():
        cols = max(approx_cols_by_table.get(table_name, 15), 1)
        total_cells += max(rows, 0) * cols

    # Approximate average columns across requested tables for coarse memory estimation.
    avg_cols = max(round(total_cells / total_rows), 1) if total_rows else 1
    estimated_peak_mb = estimate_peak_memory_mb(total_rows, approx_cols=avg_cols, bytes_per_cell=50)

    warnings: list[str] = []
    if total_rows >= LARGE_RUN_ROW_THRESHOLD:
        warnings.append(
            f"Planned generation includes {total_rows:,} rows. Consider smaller scale, table filters, "
            "or chunk_size for safer local runs."
        )
    if total_cells >= LARGE_RUN_CELL_THRESHOLD:
        warnings.append(
            f"Planned materialization includes about {total_cells:,} cells. "
            "This may stress memory on local machines."
        )
    if layer == "all":
        warnings.append(
            "Layer mode is 'all'; bronze/silver/gold outputs increase processing and memory pressure."
        )

    return {
        "layer": layer,
        "tables": len(row_counts),
        "planned_rows": total_rows,
        "planned_cells_estimate": total_cells,
        "estimated_peak_memory_mb": estimated_peak_mb,
        "warnings": warnings,
    }


def verbose_log(verbose: bool, event: str, **kwargs: Any) -> None:
    """Structured log when verbose. Never log secrets."""
    if not verbose:
        return
    safe = {k: v for k, v in kwargs.items() if k not in ("password", "secret", "token")}
    parts = [f"[data-forge] {event}"]
    for k, v in safe.items():
        parts.append(f" {k}={v}")
    print(" ".join(parts), file=sys.stderr, flush=True)
