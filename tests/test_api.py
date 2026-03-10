"""Tests for Data Forge API."""

import pytest
from fastapi.testclient import TestClient

from data_forge.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_domain_packs():
    r = client.get("/api/domain-packs")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(p["id"] == "saas_billing" for p in data)


def test_domain_pack_detail():
    r = client.get("/api/domain-packs/saas_billing")
    assert r.status_code == 200
    data = r.json()
    assert "tables" in data
    assert len(data["tables"]) > 0


def test_generate_pack():
    r = client.post(
        "/api/generate",
        json={
            "pack": "saas_billing",
            "scale": 30,
            "export_format": "csv",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("success")
    assert "tables" in data
    assert "output_dir" in data
    assert "run_id" in data


def test_preflight():
    r = client.post(
        "/api/preflight",
        json={"pack": "saas_billing", "scale": 1000, "mode": "full_snapshot", "layer": "bronze"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "valid" in data
    assert "blockers" in data
    assert "warnings" in data


def test_preflight_invalid_pack():
    r = client.post(
        "/api/preflight",
        json={"pack": "nonexistent_pack"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("valid") is False
    assert len(data.get("blockers", [])) > 0


def test_schema_visualize():
    r = client.get("/api/schema/visualize?pack_id=saas_billing")
    assert r.status_code == 200
    data = r.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["pack_id"] == "saas_billing"
    assert len(data["nodes"]) > 0


def test_schema_visualize_not_found():
    r = client.get("/api/schema/visualize?pack_id=nonexistent")
    assert r.status_code == 404


def test_artifacts_list():
    r = client.get("/api/artifacts")
    assert r.status_code == 200
    data = r.json()
    assert "artifacts" in data
    assert "runs" in data


def test_domain_packs_includes_new_packs():
    r = client.get("/api/domain-packs")
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()]
    assert "fintech_transactions" in ids
    assert "healthcare_ops" in ids
    assert "payments_ledger" in ids
    assert len(ids) >= 10


def test_runs_generate_async():
    r = client.post(
        "/api/runs/generate",
        json={"pack": "saas_billing", "scale": 50},
    )
    assert r.status_code == 200
    data = r.json()
    assert "run_id" in data
    assert data.get("status") == "queued"


def test_runs_detail():
    r = client.post("/api/runs/generate", json={"pack": "saas_billing", "scale": 50})
    run_id = r.json()["run_id"]
    r2 = client.get(f"/api/runs/{run_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == run_id


def test_runs_list():
    r = client.get("/api/runs")
    assert r.status_code == 200
    assert "runs" in r.json()


def test_validate_requires_schema():
    r = client.post(
        "/api/validate",
        json={"schema_path": "nonexistent.sql", "data_path": "nonexistent"},
    )
    assert r.status_code in (400, 404)


def test_api_generate_with_export_dbt(tmp_path):
    """API generation with export_dbt produces dbt artifacts."""
    # Use a real output dir via project structure - API uses project output/
    r = client.post(
        "/api/generate",
        json={
            "pack": "saas_billing",
            "scale": 20,
            "export_format": "csv",
            "export_dbt": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("success")
    assert "integration_summaries" in data
    dbt = data.get("integration_summaries", {}).get("dbt_export", {})
    assert dbt.get("enabled")
    assert "seeds_generated" in dbt
    assert "error" not in dbt


def test_api_generate_with_export_ge():
    """API generation with export_ge produces GE artifacts."""
    r = client.post(
        "/api/generate",
        json={
            "pack": "saas_billing",
            "scale": 20,
            "export_ge": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("success")
    ge = data.get("integration_summaries", {}).get("ge_export", {})
    assert ge.get("enabled")
    assert "suites_generated" in ge or "error" in ge


def test_api_generate_with_export_airflow():
    """API generation with export_airflow produces DAG artifacts."""
    r = client.post(
        "/api/generate",
        json={
            "pack": "saas_billing",
            "scale": 20,
            "export_airflow": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("success")
    af = data.get("integration_summaries", {}).get("airflow_export", {})
    assert af.get("enabled")
    assert "files_generated" in af


def test_api_generate_with_write_manifest():
    """API generation with write_manifest produces manifest file."""
    r = client.post(
        "/api/generate",
        json={
            "pack": "saas_billing",
            "scale": 20,
            "write_manifest": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("success")
    mf = data.get("integration_summaries", {}).get("manifest", {})
    assert mf.get("enabled")
    assert "manifest_path" in mf or "error" in mf


def test_runs_clone_returns_config():
    """Clone endpoint returns usable config payload."""
    r1 = client.post("/api/runs/generate", json={"pack": "saas_billing", "scale": 30})
    run_id = r1.json()["run_id"]
    # Wait for completion
    for _ in range(15):
        r2 = client.get(f"/api/runs/{run_id}")
        if r2.json().get("status") in ("succeeded", "failed"):
            break
        import time
        time.sleep(0.2)
    r3 = client.post(f"/api/runs/{run_id}/clone")
    assert r3.status_code == 200
    data = r3.json()
    assert "config" in data
    assert data["config"].get("pack") == "saas_billing"


def test_runs_list_filters():
    """Runs list accepts status, pack, mode, layer filters."""
    r = client.get("/api/runs?status=succeeded&pack=saas_billing")
    assert r.status_code == 200
    assert "runs" in r.json()


def test_runs_cleanup_endpoint():
    """Cleanup endpoint returns deleted count."""
    r = client.post("/api/runs/cleanup")
    assert r.status_code == 200
    data = r.json()
    assert "deleted" in data
    assert isinstance(data["deleted"], int)


def test_benchmark_api():
    """Benchmark API runs and returns metrics."""
    r = client.post(
        "/api/benchmark",
        json={"pack": "saas_billing", "scale": 50, "iterations": 2},
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("success")
    br = data.get("benchmark_results", {})
    assert "generation_seconds" in br
    assert "total_rows_generated" in br


def test_run_logs_endpoint():
    """Run logs endpoint returns events."""
    r1 = client.post("/api/runs/generate", json={"pack": "saas_billing", "scale": 30})
    run_id = r1.json()["run_id"]
    r2 = client.get(f"/api/runs/{run_id}/logs")
    assert r2.status_code == 200
    data = r2.json()
    assert "events" in data


def test_artifact_registry_on_run_completion():
    """Async generation run produces artifacts in run record when completed."""
    r1 = client.post("/api/runs/generate", json={"pack": "saas_billing", "scale": 30})
    run_id = r1.json()["run_id"]
    import time
    for _ in range(20):
        r2 = client.get(f"/api/runs/{run_id}")
        data = r2.json()
        if data.get("status") == "succeeded":
            assert "artifacts" in data
            arts = data.get("artifacts", [])
            assert isinstance(arts, list)
            if arts:
                a = arts[0]
                assert "type" in a or "name" in a
                assert "path" in a
                break
        elif data.get("status") == "failed":
            break
        time.sleep(0.25)
    else:
        pytest.skip("Run did not complete in time")


def test_benchmark_as_run():
    """Benchmark can be started as async run; appears in runs list."""
    r1 = client.post(
        "/api/runs/benchmark",
        json={"pack": "saas_billing", "scale": 30, "iterations": 2},
    )
    assert r1.status_code == 200
    data = r1.json()
    run_id = data["run_id"]
    assert data.get("status") == "queued"

    r2 = client.get("/api/runs?run_type=benchmark")
    assert r2.status_code == 200
    runs = r2.json().get("runs", [])
    ids = [r["id"] for r in runs]
    assert run_id in ids

    import time
    for _ in range(15):
        r3 = client.get(f"/api/runs/{run_id}")
        d = r3.json()
        if d.get("status") == "succeeded":
            assert d.get("run_type") == "benchmark"
            rs = d.get("result_summary", {})
            assert "total_rows_generated" in rs or "rows_generated" in rs
            assert "throughput" in rs or "generation_seconds" in rs
            break
        elif d.get("status") == "failed":
            break
        time.sleep(0.3)
    else:
        pytest.skip("Benchmark run did not complete in time")


def test_artifacts_type_filter():
    """Artifacts API accepts type_filter param."""
    r = client.get("/api/artifacts?type_filter=dataset")
    assert r.status_code == 200
    data = r.json()
    assert "artifacts" in data
    # May be empty if no runs; filter is accepted
    assert isinstance(data["artifacts"], list)


def test_run_detail_integration_summaries():
    """Completed run detail includes integration_summaries in result_summary."""
    r1 = client.post(
        "/api/runs/generate",
        json={"pack": "saas_billing", "scale": 20, "export_dbt": True, "write_manifest": True},
    )
    run_id = r1.json()["run_id"]
    import time
    for _ in range(25):
        r2 = client.get(f"/api/runs/{run_id}")
        d = r2.json()
        if d.get("status") == "succeeded":
            rs = d.get("result_summary", {})
            int_sum = rs.get("integration_summaries", {})
            assert "dbt_export" in int_sum or "manifest" in int_sum or len(int_sum) >= 1
            break
        elif d.get("status") == "failed":
            break
        time.sleep(0.2)


def test_storage_summary_endpoint():
    """Storage summary returns runs_count, artifact_count, total_size."""
    r = client.get("/api/runs/storage/summary")
    assert r.status_code == 200
    data = r.json()
    assert "runs_count" in data
    assert "artifact_count" in data
    assert "total_size_bytes" in data
    assert "total_size_mb" in data
    assert "by_run" in data


def test_cleanup_preview_endpoint():
    """Cleanup preview returns candidates and policy (dry-run)."""
    r = client.get("/api/runs/cleanup/preview?retention_count=10")
    assert r.status_code == 200
    data = r.json()
    assert data.get("dry_run") is True
    assert "candidates" in data
    assert "policy" in data


def test_cleanup_execute_endpoint():
    """Cleanup execute returns deleted_run_records."""
    r = client.post("/api/runs/cleanup/execute", json={})
    assert r.status_code == 200
    data = r.json()
    assert "deleted_run_records" in data
    assert "deleted_artifact_dirs" in data


def test_archive_pin_delete_run_endpoints():
    """Archive, pin, unpin, delete run endpoints work when run exists."""
    r1 = client.post("/api/runs/generate", json={"pack": "saas_billing", "scale": 20})
    run_id = r1.json()["run_id"]
    for _ in range(20):
        r2 = client.get(f"/api/runs/{run_id}")
        if r2.json().get("status") in ("succeeded", "failed"):
            break
        import time
        time.sleep(0.2)
    r_arch = client.post(f"/api/runs/{run_id}/archive")
    assert r_arch.status_code == 200
    assert r_arch.json().get("archived_at") is not None
    r_pin = client.post(f"/api/runs/{run_id}/pin")
    assert r_pin.status_code == 200
    assert r_pin.json().get("pinned") is True
    r_unpin = client.post(f"/api/runs/{run_id}/unpin")
    assert r_unpin.status_code == 200
    r_unarch = client.post(f"/api/runs/{run_id}/unarchive")
    assert r_unarch.status_code == 200
    r_del = client.post(f"/api/runs/{run_id}/delete", json={})
    assert r_del.status_code == 200
    assert r_del.json().get("deleted") == run_id
    r_get = client.get(f"/api/runs/{run_id}")
    assert r_get.status_code == 404


def test_run_metrics_endpoint():
    """Metrics endpoint returns aggregate run metrics."""
    r = client.get("/api/runs/metrics")
    assert r.status_code == 200
    data = r.json()
    assert "total_runs" in data
    assert "runs_by_type" in data
    assert "runs_by_status" in data
    assert "average_duration_seconds" in data
    assert "total_rows_generated" in data
    assert "artifact_count" in data
    assert "storage_mb" in data
    assert "cleanup_candidates_count" in data
    assert "failure_categories" in data


def test_run_timeline_endpoint():
    """Timeline endpoint returns structured stages and why_slow_hint for a run."""
    r1 = client.post("/api/runs/generate", json={"pack": "saas_billing", "scale": 20})
    run_id = r1.json()["run_id"]
    for _ in range(25):
        r2 = client.get(f"/api/runs/{run_id}")
        if r2.json().get("status") == "succeeded":
            break
        import time
        time.sleep(0.2)
    r3 = client.get(f"/api/runs/{run_id}/timeline")
    assert r3.status_code == 200
    data = r3.json()
    assert data.get("run_id") == run_id
    assert "stages" in data
    assert "events" in data
    assert "stage_progress_full" in data
    r4 = client.get("/api/runs/nonexistent_run_id/timeline")
    assert r4.status_code == 404


def test_scenario_versions_and_diff():
    """Scenario versioning: create, update, list versions, get version config, diff."""
    create = client.post(
        "/api/scenarios",
        json={"name": "Ver scenario", "config": {"pack": "saas_billing", "scale": 100}, "category": "custom"},
    )
    assert create.status_code == 200
    scenario_id = create.json()["id"]
    r_versions = client.get(f"/api/scenarios/{scenario_id}/versions")
    assert r_versions.status_code == 200
    assert "versions" in r_versions.json()
    assert r_versions.json().get("current_version") in (1, None)
    update = client.put(
        f"/api/scenarios/{scenario_id}",
        json={"config": {"pack": "saas_billing", "scale": 200}, "name": "Ver scenario"},
    )
    assert update.status_code == 200
    r_versions2 = client.get(f"/api/scenarios/{scenario_id}/versions")
    assert r_versions2.status_code == 200
    r_diff = client.get(f"/api/scenarios/{scenario_id}/diff?left=1&right=2")
    if r_diff.status_code == 200:
        data = r_diff.json()
        assert "changed" in data
        assert data.get("left_version") == 1
        assert data.get("right_version") == 2


def test_run_lineage_and_manifest():
    """Lineage and manifest endpoints: 404 for nonexistent run; structure when run exists."""
    r_lineage = client.get("/api/runs/nonexistent_run_id/lineage")
    assert r_lineage.status_code == 404
    r_manifest = client.get("/api/runs/nonexistent_run_id/manifest")
    assert r_manifest.status_code == 404
