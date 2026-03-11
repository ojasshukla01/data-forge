# API Reference

Key API endpoints for the Data Forge platform.

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

## Runs & Scenarios

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/runs` | List runs |
| GET | `/api/runs/{id}` | Run detail |
| GET | `/api/scenarios` | List scenarios |
| POST | `/api/scenarios` | Create scenario |
| GET | `/api/domain-packs` | List domain packs |
