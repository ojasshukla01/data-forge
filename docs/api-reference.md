# API Reference

Key API endpoints for the Data Forge platform. Base URL is the API origin (e.g. `http://localhost:8000`).

**Interactive docs:** `GET /docs` (Swagger UI) and `GET /redoc` (ReDoc).

## Example: curl

```bash
# Health check
curl -s http://localhost:8000/health

# List domain packs
curl -s http://localhost:8000/api/domain-packs

# List runs (with filters and pagination)
curl -s "http://localhost:8000/api/runs?limit=10&offset=0&run_type=generate"

# Create custom schema
curl -X POST http://localhost:8000/api/custom-schemas \
  -H "Content-Type: application/json" \
  -d '{"name":"My Schema","schema":{"tables":[{"name":"users","columns":[{"name":"id","data_type":"integer"}],"primary_key":["id"]}],"relationships":[]}}'

# Start generation
curl -X POST http://localhost:8000/api/runs/generate \
  -H "Content-Type: application/json" \
  -d '{"pack":"saas_billing","scale":1000}'
```

## Health & Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics (when `prometheus-client` is installed via `pip install -e '.[metrics]'`) |

## Custom Schemas (`/api/custom-schemas`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/custom-schemas/validate` | Validate schema structure before save. Body: `{ schema }`. Response: `{ valid, errors, warnings? }` |
| GET | `/api/custom-schemas` | List custom schemas |
| POST | `/api/custom-schemas` | Create custom schema. Body: `{ name, description?, tags?, schema }` |
| GET | `/api/custom-schemas/{id}` | Get schema detail (latest version) |
| PUT | `/api/custom-schemas/{id}` | Update schema (creates new version) |
| DELETE | `/api/custom-schemas/{id}` | Delete schema |
| GET | `/api/custom-schemas/{id}/versions` | List versions |
| GET | `/api/custom-schemas/{id}/versions/{v}` | Get specific version |
| GET | `/api/custom-schemas/{id}/diff?left=1&right=2` | Diff between versions; returns tables_added, tables_removed, tables_modified |
| POST | `/api/custom-schemas/{id}/versions/{v}/restore` | Restore version as a **new** revision (non-destructive) |

## Schema Preview & Visualization

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/schema/preview` | Generate sample rows. Body: `{ schema, rows_per_table? }`. Uses column generation rules when present. |
| GET | `/api/schema/visualize?pack_id=` | Schema visualization for a domain pack |

## Generation & Preflight

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | Synchronous generation. Body: `{ pack?, custom_schema_id?, scale, ... }` |
| POST | `/api/preflight` | Validate run config. Body: `{ pack?, custom_schema_id?, scale, mode, layer, ... }`. Returns `{ valid, blockers, warnings, recommendations }` |
| POST | `/api/runs/generate` | Async generation; returns `{ run_id, status }` |
| POST | `/api/benchmark` | Sync benchmark; returns result |
| POST | `/api/runs/benchmark` | Async benchmark run; returns `{ run_id, status }` |

## Runs (`/api/runs`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/runs` | List runs (query: status, pack, mode, run_type, include_archived, limit, offset, cursor). Response includes `runs`, `limit`, `offset`, `cursor`, `next_cursor`, `has_more`. |
| GET | `/api/runs/{id}/stream` | SSE stream for run status (replaces polling when run is queued/running). |
| GET | `/api/runs/metrics` | Aggregate run metrics |
| GET | `/api/runs/storage/summary` | Storage usage summary |
| GET | `/api/runs/cleanup/preview` | Preview retention cleanup |
| POST | `/api/runs/cleanup/execute` | Execute retention cleanup |
| GET | `/api/runs/compare?left=&right=` | Compare two runs |
| GET | `/api/runs/{id}` | Run detail |
| GET | `/api/runs/{id}/status` | Run status |
| GET | `/api/runs/{id}/timeline` | Stage timeline |
| GET | `/api/runs/{id}/lineage` | Run lineage (scenario, pack, custom_schema_id, custom_schema_version, schema_source_type) |
| GET | `/api/runs/{id}/manifest` | Reproducibility manifest |
| GET | `/api/runs/{id}/logs` | Run events |
| POST | `/api/runs/{id}/rerun` | Rerun |
| POST | `/api/runs/{id}/clone` | Clone config; returns `{ config }` |
| POST | `/api/runs/{id}/archive` | Archive run |
| POST | `/api/runs/{id}/unarchive` | Unarchive run |
| POST | `/api/runs/{id}/delete` | Delete run. Body: `{ delete_artifacts?: boolean }` |
| POST | `/api/runs/{id}/pin` | Pin run |
| POST | `/api/runs/{id}/unpin` | Unpin run |

## Scenarios (`/api/scenarios`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scenarios` | List scenarios (query: category, source_pack, search, limit, offset, cursor). Response includes `scenarios`, `limit`, `offset`, `cursor`, `next_cursor`, `has_more`. |
| POST | `/api/scenarios` | Create scenario |
| GET | `/api/scenarios/{id}` | Scenario detail |
| PUT | `/api/scenarios/{id}` | Update scenario |
| DELETE | `/api/scenarios/{id}` | Delete scenario |
| POST | `/api/scenarios/{id}/run` | Run from scenario |
| POST | `/api/scenarios/from-run/{run_id}` | Create scenario from run |
| POST | `/api/scenarios/import` | Import scenario |
| GET | `/api/scenarios/{id}/versions` | Version history |
| GET | `/api/scenarios/{id}/versions/{v}` | Version config |
| GET | `/api/scenarios/{id}/diff?left=&right=` | Diff two versions |
| GET | `/api/scenarios/{id}/export` | Export scenario |

## Domain Packs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/domain-packs` | List domain packs |
| GET | `/api/domain-packs/{id}` | Pack detail (tables, relationships) |

## Templates (user-managed)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/templates` | List templates (built-in not hidden + user templates) |
| POST | `/api/templates/from-pack/{pack_id}` | Clone pack to custom schema and add as user template |
| POST | `/api/templates/from-schema/{schema_id}` | Add custom schema as user template |
| DELETE | `/api/templates/{id}` | Hide built-in or remove user template |
| POST | `/api/templates/{id}/unhide` | Unhide a previously hidden built-in pack |
| GET | `/api/templates/hidden` | List hidden built-in pack IDs |

## Artifacts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/artifacts` | List artifacts (query: run_id, type) |
| GET | `/api/artifacts/file?run_id=&path=` | Download artifact file |

## Lineage & Manifest

| Endpoint | Description |
|----------|-------------|
| GET `/api/runs/{id}/lineage` | run_id, run_type, scenario_id, pack, custom_schema_id, custom_schema_version, custom_schema_name?, schema_source_type (pack \| custom_schema), artifact_run_id, output_dir. When run used a custom schema: **schema_missing** (true if schema was deleted), **schema_missing_message** (human-readable note), **custom_schema_snapshot_hash**, **custom_schema_table_names** (preserved for provenance). |
| GET `/api/runs/{id}/manifest` | From output manifest or built from run record: run_id, seed, pack, custom_schema_id, custom_schema_version, custom_schema_name?, schema_source_type, scale, total_rows_generated, duration_seconds, created_at, manifest_version. When schema was deleted: **schema_missing**, **custom_schema_snapshot_hash**, **custom_schema_table_names** may be present. |

## Validation and Errors

### Custom schema validate (POST /api/custom-schemas/validate)

- **Request:** `{ "schema": { "tables": [...], "relationships": [...] } }`
- **Response:** `{ "valid": boolean, "errors": string[], "warnings": string[] }` — structural errors and optional warnings (e.g. missing generation rules). Use `valid` and `errors` to block save; show `warnings` in UI.

### Preflight (POST /api/preflight)

- **Response:** `{ "valid": boolean, "blockers": string[], "warnings": string[], "recommendations": string[] }` — blockers prevent run; warnings and recommendations are advisory.

### Global error responses (middleware)

- **413 Payload Too Large** — Request body > 2MB. Body: `{ "detail": "Request body too large", "code": "payload_too_large", "max_size_bytes": 2097152 }`. Use `code` for programmatic handling.
- **429 Too Many Requests** — Rate limit exceeded (GET 300/min, mutate 60/min per IP). Body: `{ "detail": "Rate limit exceeded", "code": "rate_limit_exceeded", "retry_after_seconds": 60 }`.

### Schema create/update errors

- **400** — Validation failure: `detail` may be a string or `{ "schema_errors": string[] }`. Schema body size over 512KB returns 400 with message describing the limit. See [security.md](security.md) for limits.

---

## See also

- [testing.md](testing.md) — How to run and extend tests
- [ci-cd.md](ci-cd.md) — CI workflow and local parity
- [security.md](security.md) — Schema size limits, rate limiting, path safety
- [README](../README.md) — Setup and quick start
- [CONTRIBUTING](../CONTRIBUTING.md) — Contribution and validation commands
