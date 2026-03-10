"""Tests for saved scenarios and run comparison milestone."""

import json

import pytest
from httpx import ASGITransport, AsyncClient

from data_forge.api.main import app
from data_forge.api.scenario_store import create_scenario, get_scenario, delete_scenario


@pytest.fixture
def sample_config():
    return {
        "pack": "saas_billing",
        "scale": 1000,
        "seed": 42,
        "mode": "full_snapshot",
        "layer": "bronze",
        "pipeline_simulation": {"enabled": False},
        "benchmark": {"enabled": False},
    }


@pytest.mark.asyncio
async def test_create_scenario(sample_config):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/scenarios",
            json={"name": "Test scenario", "description": "A test", "category": "testing", "config": sample_config},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Test scenario"
        assert data["category"] == "testing"
        assert "id" in data
        assert data["config"]["pack"] == "saas_billing"
        # Cleanup
        delete_scenario(data["id"])


@pytest.mark.asyncio
async def test_list_scenarios(sample_config):
    s = create_scenario("List test", sample_config, category="custom")
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/api/scenarios")
            assert r.status_code == 200
            data = r.json()
            assert "scenarios" in data
            ids = [x["id"] for x in data["scenarios"]]
            assert s["id"] in ids
    finally:
        delete_scenario(s["id"])


@pytest.mark.asyncio
async def test_get_scenario(sample_config):
    s = create_scenario("Get test", sample_config)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(f"/api/scenarios/{s['id']}")
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == s["id"]
            assert data["name"] == "Get test"
    finally:
        delete_scenario(s["id"])


@pytest.mark.asyncio
async def test_delete_scenario(sample_config):
    s = create_scenario("Delete test", sample_config)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.delete(f"/api/scenarios/{s['id']}")
        assert r.status_code == 200
        assert get_scenario(s["id"]) is None


@pytest.mark.asyncio
async def test_create_scenario_from_run(sample_config):
    from data_forge.api.run_store import create_run, _runs_dir

    run_id = "run_testscenario123"
    create_run(run_id, "generate", sample_config, selected_pack="saas_billing")
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                f"/api/scenarios/from-run/{run_id}",
                json={"name": "From run test"},
            )
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == "From run test"
            assert data["created_from_run_id"] == run_id
            delete_scenario(data["id"])
    finally:
        p = _runs_dir() / f"{run_id}.json"
        if p.exists():
            p.unlink()


@pytest.mark.asyncio
async def test_run_from_scenario(sample_config):
    s = create_scenario("Run from scenario test", sample_config)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(f"/api/scenarios/{s['id']}/run")
            assert r.status_code == 200
            data = r.json()
            assert "run_id" in data
            assert data["status"] == "queued"
    finally:
        delete_scenario(s["id"])


@pytest.mark.asyncio
async def test_import_export_scenario(sample_config):
    s = create_scenario("Import export test", sample_config)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            exp = await client.get(f"/api/scenarios/{s['id']}/export")
            assert exp.status_code == 200
            exported = exp.json()
            assert exported["name"] == "Import export test"
            assert "config" in exported

            imp = await client.post("/api/scenarios/import", json=exported)
            assert imp.status_code == 200
            imported = imp.json()
            assert imported["name"] == "Import export test"
            assert imported["id"] != s["id"]
            delete_scenario(imported["id"])
    finally:
        delete_scenario(s["id"])


@pytest.mark.asyncio
async def test_compare_runs():
    from data_forge.api.run_store import create_run, _runs_dir

    cfg1 = {"pack": "saas_billing", "scale": 100}
    cfg2 = {"pack": "ecommerce", "scale": 200}
    create_run("run_compareleft123", "generate", cfg1)
    create_run("run_compareright456", "generate", cfg2)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/api/runs/compare?left=run_compareleft123&right=run_compareright456")
            assert r.status_code == 200
            data = r.json()
            assert "left_run" in data
            assert "right_run" in data
            assert "config_diff" in data
            assert data["config_diff"]["pack"]["left"] == "saas_billing"
            assert data["config_diff"]["pack"]["right"] == "ecommerce"
            assert data["config_diff"]["pack"]["changed"] is True
    finally:
        for run_id in ("run_compareleft123", "run_compareright456"):
            p = _runs_dir() / f"{run_id}.json"
            if p.exists():
                p.unlink()


@pytest.mark.asyncio
async def test_compare_runs_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/runs/compare?left=nonexistent&right=alsononexistent")
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_scenario_masked_fields(sample_config):
    sample_config["db_uri"] = "***"
    s = create_scenario("Masked test", sample_config)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(f"/api/scenarios/{s['id']}")
            assert r.status_code == 200
            data = r.json()
            assert data["has_masked_sensitive_fields"] is True
            assert "masked_fields" in data
            assert "db_uri" in data["masked_fields"]
    finally:
        delete_scenario(s["id"])


@pytest.mark.asyncio
async def test_compare_runs_raw_diff_and_summary():
    from data_forge.api.run_store import create_run, _runs_dir

    create_run("run_rawleft789", "generate", {"pack": "saas_billing", "scale": 100})
    create_run("run_rawright012", "generate", {"pack": "ecommerce", "scale": 200})
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/api/runs/compare?left=run_rawleft789&right=run_rawright012")
            assert r.status_code == 200
            data = r.json()
            assert "raw_diff" in data
            assert "summary" in data
            assert "total_changed_fields" in data["summary"]
            assert "left_run" in json.loads(data["raw_diff"])
    finally:
        for run_id in ("run_rawleft789", "run_rawright012"):
            p = _runs_dir() / f"{run_id}.json"
            if p.exists():
                p.unlink()


@pytest.mark.asyncio
async def test_run_from_scenario_sets_source_scenario_id(sample_config):
    from data_forge.api.run_store import get_run, _runs_dir

    s = create_scenario("Source scenario test", sample_config)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(f"/api/scenarios/{s['id']}/run")
            assert r.status_code == 200
            run_id = r.json()["run_id"]
            rec = get_run(run_id)
            assert rec is not None
            assert rec.get("source_scenario_id") == s["id"]
            p = _runs_dir() / f"{run_id}.json"
            if p.exists():
                p.unlink()
    finally:
        delete_scenario(s["id"])


@pytest.mark.asyncio
async def test_update_scenario_metadata(sample_config):
    s = create_scenario("Update meta test", sample_config, description="Old", category="testing")
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.put(
                f"/api/scenarios/{s['id']}",
                json={"name": "Updated name", "description": "New desc", "category": "custom", "tags": ["a", "b"]},
            )
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == "Updated name"
            assert data["description"] == "New desc"
            assert data["category"] == "custom"
            assert data["tags"] == ["a", "b"]
            assert data["updated_at"] >= s["updated_at"]
    finally:
        delete_scenario(s["id"])


@pytest.mark.asyncio
async def test_update_scenario_rejects_empty_name(sample_config):
    s = create_scenario("Empty name test", sample_config)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.put(f"/api/scenarios/{s['id']}", json={"name": "   "})
            assert r.status_code == 400
    finally:
        delete_scenario(s["id"])


@pytest.mark.asyncio
async def test_create_scenario_with_created_from_scenario_id(sample_config):
    parent = create_scenario("Parent scenario", sample_config)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/api/scenarios",
                json={
                    "name": "Child scenario",
                    "category": "custom",
                    "config": sample_config,
                    "created_from_scenario_id": parent["id"],
                },
            )
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == "Child scenario"
            assert data["id"] != parent["id"]
            assert data.get("created_from_scenario_id") == parent["id"]
            delete_scenario(data["id"])
    finally:
        delete_scenario(parent["id"])


@pytest.mark.asyncio
async def test_list_runs_filter_by_source_scenario_id(sample_config):
    from data_forge.api.run_store import create_run, _runs_dir

    s = create_scenario("Filter scenario", sample_config)
    run_id = "run_filterscen123"
    create_run(run_id, "generate", sample_config, source_scenario_id=s["id"])
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get(f"/api/runs?source_scenario_id={s['id']}")
            assert r.status_code == 200
            runs = r.json().get("runs") or []
            ids = [x["id"] for x in runs]
            assert run_id in ids
            for x in runs:
                if x["id"] == run_id:
                    assert x.get("source_scenario_id") == s["id"]
                    break
    finally:
        p = _runs_dir() / f"{run_id}.json"
        if p.exists():
            p.unlink()
        delete_scenario(s["id"])
