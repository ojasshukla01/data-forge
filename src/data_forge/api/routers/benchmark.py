"""Benchmark API router."""

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Body

from data_forge.domain_packs import get_pack
from data_forge.engine import run_generation, export_result
from data_forge.models.generation import GenerationRequest, GenerationMode, DataLayer
from data_forge.models.simulation import scale_from_preset
from data_forge.config import OutputFormat, Settings
from data_forge.performance import estimate_peak_memory_mb
from data_forge.services import get_run, update_run, append_event

router = APIRouter(prefix="/api", tags=["benchmark"])


def _execute_benchmark_sync(pack: str, scale: int, fmt: str, iterations: int, config: dict | None = None) -> dict:
    """Run benchmark synchronously. Returns benchmark_results dict."""
    domain = get_pack(pack)
    if not domain:
        raise ValueError(f"Unknown pack: {pack}")
    settings = Settings()
    output_dir = Path(tempfile.mkdtemp(prefix="data-forge-bench-"))
    try:
        req = GenerationRequest(
            schema_name=pack,
            seed=42,
            scale=scale,
            include_anomalies=False,
            anomaly_ratio=0.0,
            locale=settings.locale,
            mode=GenerationMode.FULL_SNAPSHOT,
            layer=DataLayer.BRONZE,
            change_ratio=0.1,
            privacy_mode="off",
        )
        try:
            fmt_enum = OutputFormat(fmt)
        except ValueError:
            fmt_enum = OutputFormat.PARQUET

        gen_secs: list[float] = []
        exp_secs: list[float] = []
        total_rows = 0

        for i in range(iterations):
            timings: dict[str, float] = {}
            result = run_generation(
                request=req,
                schema=domain.schema,
                rule_set=domain.rule_set,
                timings_out=timings,
            )
            if not result.success:
                raise ValueError(f"Generation failed: {result.errors}")
            total_rows = sum(t.row_count for t in result.tables)
            gen_secs.append(timings.get("generation_seconds", 0))
            export_result(result, output_dir / str(i), fmt=fmt_enum, timings_out=timings)
            exp_secs.append(timings.get("export_seconds", 0))

        gen_avg = sum(gen_secs) / len(gen_secs)
        exp_avg = sum(exp_secs) / len(exp_secs)

        throughput = round(total_rows / (gen_avg + exp_avg), 2) if (gen_avg + exp_avg) > 0 else 0
        cfg = config or {}
        profile = cfg.get("profile") or (cfg.get("benchmark") or {}).get("profile")
        scale_preset = cfg.get("scale_preset") or (cfg.get("benchmark") or {}).get("scale_preset")
        return {
            "iterations": iterations,
            "pack": pack,
            "scale": scale,
            "format": fmt,
            "profile_used": profile,
            "scale_preset_used": scale_preset,
            "total_rows_generated": total_rows,
            "rows_generated": total_rows,
            "generation_seconds": round(gen_avg, 2),
            "export_seconds": round(exp_avg, 2),
            "duration": round(gen_avg + exp_avg, 2),
            "rows_per_second_generation": round(total_rows / gen_avg, 2) if gen_avg > 0 else 0,
            "rows_per_second_export": round(total_rows / exp_avg, 2) if exp_avg > 0 else 0,
            "throughput": throughput,
            "throughput_rows_per_second": throughput,
            "peak_memory_mb_estimate": round(estimate_peak_memory_mb(total_rows), 1),
            "memory_estimate": round(estimate_peak_memory_mb(total_rows), 1),
        }
    finally:
        try:
            shutil.rmtree(output_dir, ignore_errors=True)
        except Exception:
            pass


def execute_benchmark_async(run_id: str, config: dict) -> None:
    """Execute benchmark in background and update run record."""
    import time

    append_event(run_id, "info", "Starting benchmark")
    update_run(run_id, status="running", started_at=time.time())

    pack = config.get("pack") or "saas_billing"
    scale_preset = config.get("scale_preset") or config.get("benchmark", {}).get("scale_preset")
    scale = int(config.get("scale") or scale_from_preset(scale_preset) or 1000)
    fmt = config.get("format") or "parquet"
    iterations = int(config.get("iterations") or 3)
    if iterations < 1 or iterations > 10:
        iterations = 3

    try:
        results = _execute_benchmark_sync(pack, scale, fmt, iterations)
        finished = time.time()
        record = get_run(run_id)
        started = record.get("started_at") or finished
        duration = round(finished - started, 2)

        update_run(
            run_id,
            status="succeeded",
            finished_at=finished,
            duration_seconds=duration,
            result_summary={
                **results,
                "selected_pack": pack,
            },
        )
        append_event(
            run_id,
            "info",
            f"Completed: {results.get('total_rows_generated', 0)} rows, "
            f"{results.get('throughput', 0)} rows/s",
        )
    except Exception as e:
        err_msg = str(e)
        update_run(run_id, status="failed", finished_at=time.time(), error_message=err_msg)
        append_event(run_id, "error", err_msg)


@router.post("/benchmark")
def api_benchmark_sync(params: dict | None = Body(default=None)) -> dict:
    """
    Run benchmark synchronously. Returns results inline.
    Body: { pack?, scale?, scale_preset?, profile?, format?, iterations? }
    """
    p = params or {}
    pack = p.get("pack") or "saas_billing"
    scale_preset = p.get("scale_preset") or (p.get("benchmark") or {}).get("scale_preset")
    scale = int(p.get("scale") or scale_from_preset(scale_preset) or 1000)
    fmt = p.get("format") or "parquet"
    iterations = int(p.get("iterations") or 3)
    if iterations < 1 or iterations > 10:
        iterations = 3
    try:
        results = _execute_benchmark_sync(pack, scale, fmt, iterations, p)
        return {"benchmark_results": results, "success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
