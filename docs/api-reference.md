# API Reference

Key API endpoints for the Data Forge platform.

## Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## Schema

### Custom Schemas (`/api/custom-schemas`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/validate` | Validate schema structure before save. Body: `{ schema }`. Response: `{ valid, errors }` |
| GET | `` | List custom schemas |
| POST | `` | Create custom schema. Body: `{ name, description?, tags?, schema }` |
| GET | `/{id}` | Get schema detail (latest version) |
| PUT | `/{id}` | Update schema (appends new version) |
| DELETE | `/{id}` | Delete schema |
| GET | `/{id}/versions` | List versions |
| GET | `/{id}/versions/{v}` | Get specific version |
| GET | `/{id}/diff?left=1&right=2` | Diff between versions; returns tables_added, tables_removed, tables_modified |

### Schema Preview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/schema/preview` | Generate sample rows. Body: `{ schema, rows_per_table }`. Uses column generation rules when present. |

## Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | Synchronous generation. Body: `{ pack?, custom_schema_id?, scale, ... }` |
| POST | `/api/preflight` | Validate run config. Body: `{ pack?, custom_schema_id?, scale, mode, layer, ... }` |
| POST | `/api/runs/generate` | Async generation; returns `run_id` |
| POST | `/api/benchmark` | Sync benchmark; returns result |

## Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/runs` | List runs (filters supported) |
| GET | `/api/runs/{id}` | Run detail |
| GET | `/api/runs/{id}/status` | Run status |
| GET | `/api/runs/{id}/timeline` | Stage timeline |
| GET | `/api/runs/{id}/lineage` | Run lineage (scenario, pack, custom_schema) |
| GET | `/api/runs/{id}/manifest` | Reproducibility manifest |
| GET | `/api/runs/{id}/logs` | Run events |
| GET | `/api/runs/compare?left=&right=` | Compare two runs |
| POST | `/api/runs/{id}/rerun` | Rerun |
| POST | `/api/runs/{id}/clone` | Clone config |

## Scenarios

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scenarios` | List scenarios |
| POST | `/api/scenarios` | Create scenario |
| GET | `/api/scenarios/{id}` | Scenario detail |
| PUT | `/api/scenarios/{id}` | Update scenario |
| DELETE | `/api/scenarios/{id}` | Delete scenario |
| POST | `/api/scenarios/{id}/run` | Run from scenario |
| POST | `/api/scenarios/from-run/{run_id}` | Create scenario from run |
| GET | `/api/domain-packs` | List domain packs |
| GET | `/api/domain-packs/{id}` | Pack detail |

## Lineage & Manifest

| Endpoint | Description |
|--------|-------------|
| GET `/api/runs/{id}/lineage` | run_id, run_type, scenario_id, pack, custom_schema_id, custom_schema_version, schema_source_type (pack \| custom_schema), artifact_run_id, output_dir |
| GET `/api/runs/{id}/manifest` | Loaded from output_dir/manifest.json: run_id, config_schema_version, seed, pack, custom_schema_id, custom_schema_version, scale, total_rows_generated, duration_seconds, git_commit_sha, created_at |
