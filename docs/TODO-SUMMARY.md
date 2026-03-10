# Data Forge evolution — complete todo summary

This document summarizes **all 14 completed todo list items** implemented across the three phases (Foundation Hardening, Platform Scalability + Observability, Product Maturity + Experience), plus file lists, commands, assumptions, and optional next steps.

---

## All 14 completed tasks

### Task 1 — Artifact metadata, retention service, cleanup/archive/pin (Phase 1.1)
- **Artifact metadata & retention**: `models/artifact_metadata.py`, `services/retention_service.py` (preview/execute cleanup, archive/unarchive, delete, pin/unpin, storage usage).
- **Run store**: `pinned`, `archived_at`; `list_runs(include_archived)`; `delete_run`; cleanup skips pinned. Backends: `storage/file_backend.py`, `storage/sqlite_backend.py`.
- **Docs**: `docs/retention-and-cleanup.md`.

### Task 2 — Cleanup/archive/delete/pin API + CLI (Phase 1.1)
- **API**: Storage summary, cleanup preview/execute, archive/unarchive/delete/pin/unpin per run (`api/routers/runs.py`).
- **CLI**: `data-forge runs storage|cleanup-preview|cleanup-execute|archive|unarchive|delete|pin|unpin` (`cli.py`).

### Task 3 — Frontend retention/storage UI (Phase 1.1)
- **Frontend**: Storage + performance summary cards, cleanup modal, archive/pin/delete on runs, delete confirmation (`frontend/src/app/runs/page.tsx`, run detail).

### Task 4 — Config model refactor (Phase 1.2)
- **Versioned nested config**: `models/config_schema.py` — `RunConfig`, sections (generation, simulation, benchmark, privacy, export, load, runtime); `from_flat_dict` / `to_flat_dict` / `normalize_legacy_config`.
- **Usage**: `api/task_runner.py` normalizes with `RunConfig.from_flat_dict`; scenario create/update use `_normalize_scenario_config`; export includes `config_schema_version`.

### Task 5 — Frontend test expansion (Phase 1.3)
- **Vitest**: New `frontend/src/lib/utils.test.ts` (cn, API_BASE). Existing tests: runs, scenarios, artifacts, docs, about, compare, pipeline flow (16 tests total).
- **Backend API tests**: `tests/test_api.py` — scenario versions/diff, lineage/manifest (404 for missing run).
- **CI**: Frontend tests run in `.github/workflows/ci.yml`. No Playwright E2E yet (optional next step).

### Task 6 — CI & quality (Phase 1.4)
- **Workflow**: `.github/workflows/ci.yml` — backend (pytest, ruff, mypy), frontend (typecheck, test, build).
- **Makefile**: `backend-lint`, `backend-typecheck`.
- **Docs**: `CONTRIBUTING.md` updated; `pyproject.toml` ruff ignore `I001`.

### Task 7 — Storage abstraction / factory + config (Phase 2.5)
- **Interfaces**: `storage/base.py` — `RunStoreInterface`, `ScenarioStoreInterface`, `delete_run`, `include_archived`.
- **Backends**: `storage/file_backend.py`, `storage/sqlite_backend.py`; factory in `storage/__init__.py` (`get_run_store`, `get_scenario_store`).
- **Config**: `config.py` — `storage_backend`, `sqlite_uri`.

### Task 8 — Service layer (Phase 2.6)
- **Services**: `services/run_service.py`, `services/scenario_service.py`; retention and metrics in services.
- **Routers**: Use services and `get_run_store()`; no direct store access in routers.
- **Docs**: `docs/service-layer.md`.

### Task 9 — Observability + metrics (Phase 2.7)
- **Metrics**: `services/metrics_service.py` — `get_run_metrics_summary`, `get_run_timeline` (with why_slow_hint).
- **API**: `GET /api/runs/metrics`, `GET /api/runs/{id}/timeline`.
- **Frontend**: Performance summary on runs page; run detail “Why slow?” from stage_progress.
- **Docs**: `docs/observability-and-metrics.md`.

### Task 10 — OpenAPI / API reference (Phase 2.8)
- **Docs**: `docs/api-reference.md` — endpoint overview; pointers to `/openapi.json`, `/docs`, `/redoc`.
- **Frontend**: Docs page includes “API reference” section with links to Swagger UI and ReDoc (localhost:8000).

### Task 11 — Scenario versioning + diff (Phase 3.9)
- **Store**: On create, `version: 1`, `versions: [{ version, config, updated_at }]`; on update, append to `versions` (capped at 20), bump version.
- **Service**: `get_scenario_versions`, `get_scenario_version_config`, `diff_scenario_versions`.
- **API**: `GET /api/scenarios/{id}/versions`, `GET /api/scenarios/{id}/versions/{version}`, `GET /api/scenarios/{id}/diff?left=&right=`.
- **Docs**: `docs/scenario-versioning.md`.
- **Frontend**: Scenario detail exists (`app/scenarios/[id]/page.tsx`); History/Diff UI can be added later (API ready).

### Task 12 — Pack authoring scaffolding (Phase 3.10)
- **CLI**: `data-forge scaffold-pack <name>` — creates `schemas/<name>.sql`, `rules/<name>.yaml`, `examples/scenarios/<name>_quick_start.json`, `docs/pack_<name>.md`; prints registration instructions.
- **Docs**: `docs/pack-authoring.md`.

### Task 13 — Reproducibility manifest + lineage (Phase 3.11)
- **Manifest**: `models/run_manifest.py` — `build_run_manifest`, `write_manifest_json`, `write_manifest_markdown`; task_runner writes `manifest.json` and `manifest.md` to run output dir.
- **Lineage**: `services/lineage_service.py` — `get_run_lineage`, `get_run_manifest_from_disk`.
- **API**: `GET /api/runs/{id}/lineage`, `GET /api/runs/{id}/manifest`.
- **Docs**: `docs/lineage-and-reproducibility.md`.

### Task 14 — Onboarding + UX polish (Phase 3.12)
- **About page**: `frontend/src/app/about/page.tsx` — mission, concepts (Run, Scenario, Artifact, Pack, Benchmark, Simulation), local-first, extensibility, how it works, creator card, open source links.
- **Docs page**: API reference section with Swagger UI and ReDoc links; pointer to `docs/api-reference.md`.
- Empty states, run-type visuals, and full first-run onboarding flow are optional enhancements.

---

## File list by area

**Backend — config & models**
- `src/data_forge/config.py`
- `src/data_forge/models/config_schema.py`
- `src/data_forge/models/artifact_metadata.py`
- `src/data_forge/models/run_manifest.py`

**Backend — storage**
- `src/data_forge/storage/base.py`
- `src/data_forge/storage/file_backend.py`
- `src/data_forge/storage/sqlite_backend.py`
- `src/data_forge/storage/__init__.py`

**Backend — services**
- `src/data_forge/services/run_service.py`
- `src/data_forge/services/scenario_service.py`
- `src/data_forge/services/retention_service.py`
- `src/data_forge/services/metrics_service.py`
- `src/data_forge/services/lineage_service.py`

**Backend — API**
- `src/data_forge/api/main.py`
- `src/data_forge/api/task_runner.py`
- `src/data_forge/api/routers/runs.py`
- `src/data_forge/api/routers/scenarios.py`
- `src/data_forge/cli.py`

**Frontend**
- `frontend/src/app/page.tsx` (home)
- `frontend/src/app/runs/page.tsx`
- `frontend/src/app/runs/[id]/page.tsx`
- `frontend/src/app/docs/page.tsx`
- `frontend/src/app/about/page.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/utils.ts`
- `frontend/src/lib/utils.test.ts`

**Docs**
- `docs/retention-and-cleanup.md`
- `docs/service-layer.md`
- `docs/observability-and-metrics.md`
- `docs/scenario-versioning.md`
- `docs/pack-authoring.md`
- `docs/api-reference.md`
- `docs/lineage-and-reproducibility.md`
- `docs/TODO-SUMMARY.md` (this file)

**CI & config**
- `.github/workflows/ci.yml`
- `Makefile`
- `CONTRIBUTING.md`
- `pyproject.toml`

**Tests**
- `tests/test_api.py` (includes scenario versions, diff, lineage, manifest)

---

## Commands to run

- **Backend tests**: `python -m pytest tests -v --tb=short`
- **Backend lint**: `uv run ruff check src tests` or `make backend-lint`
- **Backend typecheck**: `uv run python -m mypy src` or `make backend-typecheck`
- **Frontend**: `cd frontend && npm install && npm test && npx tsc --noEmit && npm run build`
- **CLI (no install)**: `python -m data_forge.cli runs storage`
- **CLI (with install)**: `data-forge runs storage`, `data-forge scaffold-pack my_pack`

---

## Assumptions

- Storage backend is file or sqlite via config; project root and output dir are set in settings.
- Scenario version history is capped at 20 entries per scenario.
- Manifest is written only on successful run completion to `output/<run_id>/manifest.json` and `manifest.md`.
- Frontend expects API at `NEXT_PUBLIC_API_URL` or `http://localhost:8000`.
- CI runs on push/PR; frontend tests include Vitest and Playwright E2E.

---

## Optional next steps

1. **Scenario restore UX**: Add “restore version” / “duplicate from version” from the scenario history & diff UI.
2. **Deeper schema studio**: ERD-style editor, DDL export, and preview rows powered by the generation engine.
3. **Broader Vitest coverage**: More interactions across wizard, advanced config, schema visualizer, and cleanup flows.
4. **UX**: Additional accessibility polish, keyboard shortcuts, and more granular empty states.
5. **Docs**: Expand architecture diagrams to cover Custom Schema Studio and advanced onboarding flows.

---

---

## Quick reference: 14 tasks by phase

| # | Task | Phase |
|---|------|--------|
| 1 | Artifact metadata, retention service, cleanup/archive/pin | 1.1 |
| 2 | Cleanup/archive/delete/pin API + CLI | 1.1 |
| 3 | Frontend retention/storage UI | 1.1 |
| 4 | Config model refactor | 1.2 |
| 5 | Frontend test expansion | 1.3 |
| 6 | CI & quality | 1.4 |
| 7 | Storage abstraction / factory + config | 2.5 |
| 8 | Service layer | 2.6 |
| 9 | Observability + metrics | 2.7 |
| 10 | OpenAPI / API reference | 2.8 |
| 11 | Scenario versioning + diff | 3.9 |
| 12 | Pack authoring scaffolding | 3.10 |
| 13 | Reproducibility manifest + lineage | 3.11 |
| 14 | Onboarding + UX polish | 3.12 |

*Summary generated after completing all 14 items on the Data Forge evolution todo list.*
