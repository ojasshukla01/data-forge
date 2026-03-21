# Database Adapter Maturity Audit

This document audits the maturity of each database load adapter: supported features, known limitations, and recommended usage.

## Overview

| Adapter | Maturity | Extra | Retry | Streaming Load |
|---------|----------|-------|-------|----------------|
| SQLite | **Mature** | core | ✓ | ✓ |
| DuckDB | **Mature** | core | ✓ | ✓ |
| PostgreSQL | **Mature** | core | ✓ | ✓ |
| Snowflake | **Partial** | warehouse | ✓ | ✓ |
| BigQuery | **Partial** | warehouse | ✓ | ✓ |

All adapters support `load_table_from_iter` for streaming/batched load from spill-backed table stores (reduced memory mode).

## SQLite

- **Status:** Mature, well-tested
- **Connection:** `sqlite3` stdlib
- **Use case:** Local testing, demos, CI
- **Limitations:**
  - No schema/namespace (create_schema is no-op)
  - Single-file; not suitable for high concurrency
  - DROP TABLE before create; overwrites existing data
- **Credentials:** File path as URI

## DuckDB

- **Status:** Mature, optimized for analytics
- **Connection:** `duckdb` package
- **Use case:** Local analytics, Parquet-heavy workloads
- **Strengths:**
  - PyArrow path for bulk insert when available; fallback to row-by-row
  - Fast for analytical queries
- **Limitations:**
  - No schema/namespace (create_schema is no-op)
  - DROP TABLE via CREATE OR REPLACE; overwrites existing data
- **Credentials:** File path or `:memory:`

## PostgreSQL

- **Status:** Mature
- **Connection:** `psycopg`
- **Use case:** Integration testing, staging, production-like environments
- **Strengths:**
  - Schema support (create_schema creates namespace)
  - Batch inserts via executemany
- **Limitations:**
  - DROP TABLE CASCADE; overwrites existing data
  - Requires `psycopg[binary]` or `psycopg` for connection
- **Credentials:** `postgresql://user:pass@host/db` or connection string

## Snowflake

- **Status:** Partial — requires warehouse extra and structured config
- **Connection:** `snowflake-connector-python` (optional `[warehouse]`)
- **Use case:** Cloud data warehouse load
- **Limitations:**
  - Requires account, user, password, warehouse (env vars or load_params)
  - No URI-based connection; use `snowflake_account`, `snowflake_user`, etc.
  - Credentials must be provided explicitly (no URI parse)
- **Credentials:** `DATA_FORGE_SNOWFLAKE_*` env vars or `load_params`

## BigQuery

- **Status:** Partial — requires warehouse extra and project/dataset
- **Connection:** `google-cloud-bigquery` (optional `[warehouse]`)
- **Use case:** GCP data warehouse load
- **Limitations:**
  - Requires project and dataset (env vars or load_params)
  - Uses `insert_rows_json`; streaming insert API not used
  - Delete + create table on each run; overwrites existing data
- **Credentials:** Application Default Credentials or `GOOGLE_APPLICATION_CREDENTIALS`

## Store-Native and Streaming

When `reduced_memory_mode` or spill backend is used, warehouse load uses `load_table_from_iter` to stream rows from the table store without full materialization. This:

- Reduces peak memory when loading to DB
- Works with all adapters (base class implements batching)
- Ensures full data is loaded (not truncated snapshots)

## Retry and Resilience

All load operations (connect, create_schema, create_tables, load_tables) use exponential backoff (3 attempts, 1–10s delay) on `ConnectionError`, `OSError`, `TimeoutError`.

## Recommendations

1. **Local/dev:** SQLite or DuckDB
2. **Staging/CI:** PostgreSQL
3. **Cloud warehouse:** Snowflake or BigQuery with `[warehouse]` extra; ensure credentials and config are set
4. **Large datasets:** Use `reduced_memory_mode` and spill backend; load will stream from store to DB

## See Also

- [performance-tuning.md](performance-tuning.md) — Lower-memory execution
- [deployment.md](deployment.md) — Environment and config
