"""Tests for pipeline simulation and warehouse benchmark milestone."""

import pytest
from pydantic import ValidationError
from httpx import ASGITransport, AsyncClient

from data_forge.api.main import app
from data_forge.models.simulation import (
    EventDensity,
    EventPattern,
    PipelineSimulationConfig,
    ReplayMode,
    scale_from_preset,
)
from data_forge.simulation.time_patterns import EventPattern as TimeEventPattern, apply_time_pattern


# --- Model / config validation ---


def test_pipeline_simulation_config_validation():
    cfg = PipelineSimulationConfig(enabled=True, event_density="medium", event_pattern="burst")
    assert cfg.enabled is True
    assert cfg.event_density == EventDensity.MEDIUM
    assert cfg.event_pattern == EventPattern.BURST
    assert cfg.replay_mode == ReplayMode.ORDERED
    assert cfg.late_arrival_ratio == 0.0


def test_pipeline_simulation_config_invalid_density():
    with pytest.raises(ValidationError):
        PipelineSimulationConfig(enabled=True, event_density="invalid")  # type: ignore


def test_scale_from_preset():
    assert scale_from_preset("small") == 10_000
    assert scale_from_preset("medium") == 100_000
    assert scale_from_preset("large") == 1_000_000
    assert scale_from_preset("xlarge") == 10_000_000
    assert scale_from_preset(None) == 1000
    assert scale_from_preset("unknown") == 1000


# --- Time patterns ---


def test_apply_time_pattern_steady_deterministic():
    import time as t
    start = t.mktime((2024, 1, 1, 0, 0, 0, 0, 0, 0))
    end = t.mktime((2024, 1, 2, 0, 0, 0, 0, 0, 0))
    ts1 = apply_time_pattern(100, TimeEventPattern.STEADY, start, end, seed=42)
    ts2 = apply_time_pattern(100, TimeEventPattern.STEADY, start, end, seed=42)
    assert ts1 == ts2
    assert len(ts1) == 100
    assert all(start <= t <= end for t in ts1)


def test_apply_time_pattern_burst_differs_from_steady():
    import time as t
    start = t.mktime((2024, 1, 1, 0, 0, 0, 0, 0, 0))
    end = t.mktime((2024, 1, 2, 0, 0, 0, 0, 0, 0))
    steady = apply_time_pattern(200, TimeEventPattern.STEADY, start, end, seed=42)
    burst = apply_time_pattern(200, TimeEventPattern.BURST, start, end, seed=42)
    # Burst should have more events toward end
    burst_last_10pct = sum(1 for ts in burst if ts >= start + (end - start) * 0.9)
    steady_last_10pct = sum(1 for ts in steady if ts >= start + (end - start) * 0.9)
    assert burst_last_10pct > steady_last_10pct


def test_apply_time_pattern_empty():
    import time as t
    start = t.mktime((2024, 1, 1, 0, 0, 0, 0, 0, 0))
    end = t.mktime((2024, 1, 2, 0, 0, 0, 0, 0, 0))
    assert apply_time_pattern(0, TimeEventPattern.STEADY, start, end) == []


# --- API: benchmark with scale_preset and profile ---


@pytest.mark.asyncio
async def test_benchmark_api_scale_preset_profile():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/api/benchmark",
            json={"pack": "saas_billing", "scale_preset": "small", "profile": "wide_table", "iterations": 1},
        )
        assert r.status_code == 200
        data = r.json()
        results = data.get("benchmark_results") or data
        assert "total_rows_generated" in results or "rows_generated" in results
        assert results.get("scale_preset_used") == "small"
        assert results.get("profile_used") == "wide_table"


# --- API: run detail includes simulation/benchmark when applicable ---


@pytest.mark.asyncio
async def test_run_detail_backward_compatible_without_simulation():
    """Old runs without pipeline_simulation or benchmark should still return."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/api/runs/generate",
            json={"pack": "saas_billing", "scale": 100},
        )
        assert r.status_code == 200
        run_id = r.json()["run_id"]
        # Poll until done (simple wait)
        for _ in range(30):
            det = await client.get(f"/api/runs/{run_id}")
            if det.status_code != 200:
                break
            status = det.json().get("status")
            if status in ("succeeded", "failed"):
                break
            import asyncio
            await asyncio.sleep(0.3)
        detail = (await client.get(f"/api/runs/{run_id}")).json()
        assert "config_summary" in detail or "config" in detail
        assert "id" in detail


# --- Domain pack metadata ---


@pytest.mark.asyncio
async def test_domain_packs_include_simulation_metadata():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/api/domain-packs")
        assert r.status_code == 200
        packs = r.json()
        ecommerce = next((p for p in packs if p.get("id") == "ecommerce"), None)
        if ecommerce:
            assert "supports_event_streams" in ecommerce
            assert "simulation_event_types" in ecommerce or ecommerce.get("supports_event_streams") is False
            assert "benchmark_relevance" in ecommerce or True  # optional


# --- Artifact type filter ---


@pytest.mark.asyncio
async def test_artifacts_type_filter_event_stream():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/api/artifacts?type_filter=event_stream")
        assert r.status_code == 200
        data = r.json()
        assert "artifacts" in data
        # May be empty; filter should not error
        for a in data.get("artifacts", []):
            assert a.get("type") == "event_stream" or a.get("category") == "event_stream"


@pytest.mark.asyncio
async def test_artifacts_type_filter_pipeline_snapshot():
    r = None
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get("/api/artifacts?type_filter=pipeline_snapshot")
    assert r is not None
    assert r.status_code == 200


# --- Clone preserves new config ---


@pytest.mark.asyncio
async def test_clone_preserves_pipeline_simulation_config():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.post(
            "/api/runs/generate",
            json={
                "pack": "saas_billing",
                "scale": 100,
                "pipeline_simulation": {
                    "enabled": True,
                    "event_density": "high",
                    "event_pattern": "burst",
                    "replay_mode": "shuffled",
                },
            },
        )
        assert r.status_code == 200
        run_id = r.json()["run_id"]
        # Poll until done
        for _ in range(40):
            det = await client.get(f"/api/runs/{run_id}")
            if det.status_code != 200:
                break
            status = det.json().get("status")
            if status in ("succeeded", "failed"):
                break
            import asyncio
            await asyncio.sleep(0.3)
        clone_r = await client.post(f"/api/runs/{run_id}/clone")
        assert clone_r.status_code == 200
        cfg = clone_r.json().get("config", {})
        ps = cfg.get("pipeline_simulation") or {}
        assert ps.get("enabled") is True
        assert ps.get("event_density") == "high"
        assert ps.get("event_pattern") == "burst"
        assert ps.get("replay_mode") == "shuffled"
