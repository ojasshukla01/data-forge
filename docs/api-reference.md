# API reference

The Data Forge API is a REST API served by FastAPI. Base URL is typically `http://localhost:8000`.

## OpenAPI

- **JSON**: [GET /openapi.json](http://localhost:8000/openapi.json)
- **Swagger UI**: [GET /docs](http://localhost:8000/docs)
- **ReDoc**: [GET /redoc](http://localhost:8000/redoc)

## Endpoints overview

### Health

- `GET /health` — Status and version.

### Domain packs

- `GET /api/domain-packs` — List packs (id, description, metadata).
- `GET /api/domain-packs/{pack_id}` — Pack detail (tables, relationships).

### Generation and preflight

- `POST /api/generate` — Synchronous generation (body: config with pack, scale, etc.).
- `POST /api/preflight` — Validate config (body: config).
- `POST /api/runs/generate` — Start async generation (body: config). Returns `run_id`.
- `POST /api/runs/benchmark` — Start async benchmark (body: config).

### Runs

- `GET /api/runs` — List runs (query: status, run_type, pack, mode, layer, limit, include_archived).
- `GET /api/runs/metrics` — Aggregate metrics (total runs, by type/status, avg duration, etc.).
- `GET /api/runs/storage/summary` — Storage usage (runs, artifacts, size).
- `GET /api/runs/cleanup/preview` — Dry-run cleanup candidates.
- `POST /api/runs/cleanup/execute` — Run cleanup (body: delete_artifacts, retention_count, retention_days).
- `GET /api/runs/{run_id}` — Run detail.
- `GET /api/runs/{run_id}/status` — Lightweight status.
- `GET /api/runs/{run_id}/timeline` — Stage timeline and “why slow?” hint.
- `GET /api/runs/{run_id}/lineage` — Lineage (run → scenario → pack → artifacts).
- `GET /api/runs/{run_id}/manifest` — Reproducibility manifest.
- `GET /api/runs/{run_id}/logs` — Run events.
- `POST /api/runs/{run_id}/rerun` — Start a new run with same config.
- `POST /api/runs/{run_id}/clone` — Get config for cloning.
- `POST /api/runs/{run_id}/archive` — Archive run.
- `POST /api/runs/{run_id}/unarchive` — Unarchive.
- `POST /api/runs/{run_id}/pin` — Pin (exclude from cleanup).
- `POST /api/runs/{run_id}/unpin` — Unpin.
- `POST /api/runs/{run_id}/delete` — Delete run (body: delete_artifacts).
- `GET /api/runs/compare?left=&right=` — Compare two runs.

### Scenarios

- `GET /api/scenarios` — List scenarios (query: category, source_pack, tag, search, limit).
- `POST /api/scenarios` — Create scenario (body: name, description, category, tags, config).
- `GET /api/scenarios/{id}` — Scenario detail.
- `PUT /api/scenarios/{id}` — Update scenario.
- `DELETE /api/scenarios/{id}` — Delete scenario.
- `GET /api/scenarios/{id}/versions` — Version history.
- `GET /api/scenarios/{id}/versions/{version}` — Config for a version.
- `GET /api/scenarios/{id}/diff?left=&right=` — Diff two versions.
- `GET /api/scenarios/{id}/export` — Export as JSON (includes version).
- `POST /api/scenarios/import` — Import from JSON.
- `POST /api/scenarios/{id}/run` — Start run from scenario.

### Artifacts

- `GET /api/artifacts` — List artifacts (query: run_id, type_filter).
- `GET /api/artifacts/file?run_id=&path=` — Download artifact file.

### Schema and validation

- `GET /api/schema/visualize?pack_id=` — Schema graph (nodes, edges).
- `POST /api/validate` — Validate schema/data (body: schema_path, data_path, rules_path, privacy_mode).

## Config schema

Generation config supports flat or nested structure. Key fields (flat): `pack`, `scale`, `seed`, `mode`, `layer`, `export_format`, `pipeline_simulation`, `benchmark`, `config_schema_version`. See `/openapi.json` for full request/response schemas.
