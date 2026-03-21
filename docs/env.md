# Environment Variables

## Backend

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATA_FORGE_PROJECT_ROOT` | No | Base project root for schema/rule discovery. |
| `DATA_FORGE_OUTPUT_DIR` | No | Default output directory for generated artifacts. |
| `DATA_FORGE_STORAGE_BACKEND` | No | Run storage backend (`file`, `sqlite`). |
| `DATA_FORGE_SQLITE_URI` | No | SQLite path/URI when storage backend is sqlite. |
| `DATA_FORGE_CORS_ALLOW_ORIGINS` | No | Comma-separated allowed origins for frontend. |
| `DATA_FORGE_STRUCTURED_LOGS` | No | Set to `1`, `true`, or `yes` to emit JSON-structured logs (method, path, status_code, duration_ms). |

## Frontend

| Variable | Required | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Yes (non-proxy setups) | Public browser-side API base URL. |
| `DATA_FORGE_API_INTERNAL_URL` | No | Internal API base for server-side rendering/container networking. |

## Optional warehouse adapters

| Variable | Required | Purpose |
| --- | --- | --- |
| `SNOWFLAKE_ACCOUNT` | Optional | Snowflake account identifier. |
| `SNOWFLAKE_USER` | Optional | Snowflake user. |
| `SNOWFLAKE_PASSWORD` | Optional | Snowflake password. |
| `BIGQUERY_PROJECT` | Optional | GCP project for BigQuery. |
| `BIGQUERY_DATASET` | Optional | BigQuery dataset default. |

Use `.env.example` at repo root and `frontend/.env.example` as starting points for local setup.
