# Data Forge

**Schema-aware synthetic data platform for realistic, relational, time-aware test data.**

Data Forge generates business-valid, cross-table, time-consistent, privacy-safe dummy data for databases, APIs, files, and pipelines—not just fake names and emails, but **test-ready data** that respects schemas, foreign keys, business rules, and optional anomaly injection.

## One-line pitch

*An open-source, schema-aware synthetic data platform that generates realistic, relational, time-aware, edge-case-rich test data for databases, APIs, and pipelines.*

## Features

- **Schema import**: SQL DDL, JSON Schema, OpenAPI (table-like extraction)
- **Rule engine**: YAML business rules (order, range, sum, equality) and distribution hints (categorical, skewed, seasonal)
- **Relational integrity**: PK/FK resolution across tables in dependency order
- **Generators**: Faker + Mimesis for primitives; distribution-aware and time-aware hints
- **Anomaly injection**: Optional nulls, duplicates, invalid enums, malformed strings for resilience testing
- **Export**: CSV, JSON, JSONL, Parquet, SQL inserts
- **Quality report**: Referential integrity, null ratios, row counts
- **Domain packs**: SaaS billing (organizations, users, plans, subscriptions, invoices, support tickets) and e-commerce (customers, products, orders, payments, refunds, shipments, inventory)
- **CLI + Streamlit UI**: Reproducible generation with seed and scale

## Quick start

### Install (uv)

```bash
cd data-forge
uv sync
```

### Generate from a domain pack

```bash
# SaaS billing: 1000 base rows, Parquet output
uv run data-forge generate --pack saas_billing --scale 1000 -o output -f parquet

# E-commerce, with anomalies, SQL inserts
uv run data-forge generate --pack ecommerce --scale 2000 --anomalies --anomaly-ratio 0.03 -o output -f sql

# Reproducible: same seed → same data
uv run data-forge generate --pack saas_billing --seed 42 -o output
```

### Custom schema + rules

```bash
uv run data-forge generate -s schemas/my.sql -r rules/my.yaml --scale 5000 -o output -f csv
```

### List domain packs

```bash
uv run data-forge packs
```

### Validate a schema file

```bash
uv run data-forge validate schemas/saas_billing.sql
```

### Database loading

Load generated data directly into a database with the `--load` and `--db-uri` options:

```bash
# SQLite (file path; defaults to output/data.db if --db-uri omitted)
uv run data-forge generate --pack ecommerce --load sqlite --db-uri ./test.db -o output

# DuckDB (file path)
uv run data-forge generate --pack saas_billing --load duckdb --db-uri ./data.duckdb -o output

# PostgreSQL (connection string)
uv run data-forge generate --pack ecommerce --load postgres --db-uri postgresql://user:pass@localhost:5432/mydb -o output

# Snowflake (use env vars or --sf-* options; prefer env for secrets)
uv run data-forge generate --pack saas_billing --load snowflake --sf-database MYDB --sf-schema RAW -o output

# BigQuery (use env vars or --bq-project, --bq-dataset)
uv run data-forge generate --pack ecommerce --load bigquery --bq-project my-project --bq-dataset test_data -o output
```

Supported adapters: SQLite, DuckDB, PostgreSQL, Snowflake, BigQuery.

### Large-scale runs (chunk-size, batch-size)

For large datasets, use `--chunk-size` to generate tables in chunks and `--batch-size` to control DB insert batches:

```bash
# Generate 100k rows in 10k chunks (memory-safe)
uv run data-forge generate --pack saas_billing --scale 50000 --chunk-size 10000 -o output

# Load with custom batch size (default 1000)
uv run data-forge generate --pack saas_billing --load sqlite --batch-size 2000 -o output
```

Without `chunk-size`, scale ≥ 50,000 triggers an advisory performance warning.

### Benchmark mode

Run performance benchmarks and capture metrics:

```bash
# Basic benchmark (pack, scale, format)
uv run data-forge benchmark --pack saas_billing --scale 1000 --format csv

# With iterations and JSON output
uv run data-forge benchmark --pack saas_billing --scale 5000 --iterations 3 --output-json bench.json

# With load target and verbose logging
uv run data-forge benchmark --pack saas_billing --scale 2000 --load sqlite --verbose
```

Output includes `generation_seconds`, `export_seconds`, `load_seconds`, rows/sec, and peak memory estimate.

### dbt export

Export generated tables as dbt seeds and generate `sources.yml` and schema test templates:

```bash
uv run data-forge generate --pack ecommerce --export-dbt --dbt-dir ./dbt_project -o output
```

Output structure:
```
dbt_project/
├── seeds/
│   ├── customers.csv
│   ├── orders.csv
│   └── ...
└── models/
    ├── sources.yml
    └── schema_tests.yml
```

### Great Expectations export

Export GE-compatible expectation suites and checkpoints:

```bash
uv run data-forge generate --pack saas_billing --export-ge --ge-dir ./great_expectations -o output
```

Validate data against exported expectations (no GE runtime required):

```bash
uv run data-forge validate-ge --expectations ./great_expectations --data ./output
```

### Airflow DAG export

Export Airflow DAG templates for common workflows:

```bash
uv run data-forge generate --pack saas_billing --export-airflow --airflow-dir ./airflow -o output
uv run data-forge generate --export-airflow --airflow-template generate_validate_and_load -o output
```

Templates: `generate_only`, `generate_and_load`, `generate_validate_and_load`, `benchmark_pipeline`.

### Reconcile

Compare manifest expected row counts vs actual data:

```bash
uv run data-forge reconcile --manifest manifest.json --data ./output --schema schemas/saas_billing.sql
```

### Cloud configuration

Use environment variables for sensitive credentials. Do not pass secrets in shell history.

- **Snowflake**: `DATA_FORGE_SNOWFLAKE_ACCOUNT`, `DATA_FORGE_SNOWFLAKE_USER`, `DATA_FORGE_SNOWFLAKE_PASSWORD`, `DATA_FORGE_SNOWFLAKE_WAREHOUSE`, `DATA_FORGE_SNOWFLAKE_DATABASE`, `DATA_FORGE_SNOWFLAKE_SCHEMA`
- **BigQuery**: `DATA_FORGE_BIGQUERY_PROJECT`, `DATA_FORGE_BIGQUERY_DATASET`; uses standard Google Application Default Credentials

### Product UI (Next.js)

The flagship UI is a Next.js web app. Run the backend API and frontend:

```bash
# Terminal 1: Start the API
uv run uvicorn data_forge.api.main:app --reload --port 8000

# Terminal 2: Start the frontend
cd frontend && npm run dev
```

Open http://localhost:3000. The UI includes:

- **Home**: Landing page with hero, capabilities, domain pack showcase, integrations, and CTAs
- **About**: Creator info (Ojas Shukla, Senior Data Engineer), project rationale, open-source notes
- **Create**: Guided wizard with API-driven domain packs, use case presets, realism, export options, and preflight validation before run
- **Advanced**: Expert configuration workspace with categorized sections (Schema, ETL, Privacy, Contracts, Exports, Load, dbt/GE/Airflow, Benchmark with Run benchmark button), config import/export, clone prefill, and Run Preflight
- **Templates**: Domain pack explorer with category, table/relationship counts, key entities, recommended use cases, schema diagram link, and Use This Template CTA
- **Schema**: Interactive schema visualizer (React Flow) showing tables, columns, PK/FK relationships
- **Validate**: Validation center for schema+rules, Great Expectations, and manifest reconciliation; "Load from run" populates paths from completed runs
- **Artifacts**: Browse generated datasets, contracts, manifests, dbt, GE suites, DAGs; filter by run, preview, download
- **Runs**: Run history with filters (status, pack, mode); async runs with live progress, logs panel, stage timeline, rerun, clone
- **Integrations**: Database adapters, dbt, GE, Airflow
- **Docs**: Quick start, glossary, run results guide, links to About and GitHub
- **Footer**: Creator link, GitHub, quick links

Branding uses teal/cyan/deep blue accents and a logo mark. Nav: Home, Create, Advanced, Templates, Runs, Artifacts, Validate, Schema, Integrations, Docs, About.

API base URL defaults to `http://localhost:8000`. Set `NEXT_PUBLIC_API_URL` to override.

**API endpoints** (used by the frontend):

- `GET /api/domain-packs` – List domain packs (10 packs) with category, key entities, table/relationship counts, supported features
- `GET /api/domain-packs/{id}` – Pack detail (tables, relationships, recommended use cases)
- `POST /api/generate` – Run generation synchronously (legacy)
- `POST /api/runs/generate` – Start async generation (returns `run_id` immediately)
- `GET /api/runs` – List runs (filters: status, run_type, pack, mode, layer)
- `GET /api/runs/{id}` – Run detail with events/logs and stage timeline
- `GET /api/runs/{id}/logs` – Run logs/events (also included in run detail)
- `GET /api/runs/{id}/status` – Poll run status
- `POST /api/runs/{id}/rerun` – Rerun with same config (skips if secrets are masked)
- `POST /api/runs/{id}/clone` – Clone config for Advanced Config prefill
- `POST /api/runs/cleanup` – Run retention cleanup (prune old run records)
- `POST /api/benchmark` – Run performance benchmark (pack, scale, format, iterations)
- `POST /api/preflight` – Validate config before run
- `GET /api/schema/visualize?pack_id=` – Schema nodes/edges
- `GET /api/artifacts` – List artifacts (includes dbt, GE, Airflow, contracts, manifests)
- `POST /api/validate` – Schema + rules validation
- `POST /api/validate/ge` – Great Expectations validation
- `POST /api/reconcile` – Manifest reconciliation

**API generation parity**: When you request dbt export, GE export, Airflow export, contracts, or manifest via the API/UI, these integrations are now executed during generation. Result summary includes integration statuses (dbt seeds, GE suites, DAG files, contract fixtures, manifest path). Artifacts are registered for artifact listing.

**Async runs**: The UI uses `POST /api/runs/generate` to start generation. Run records are persisted in `runs/` as JSON. Poll `GET /api/runs/{id}` for progress, events, and stage timeline. Run logs appear on the run detail page.

**Clone & rerun**: Clone returns a full config payload; the Advanced Config page prefills from it. Sensitive fields (e.g. DB credentials) are redacted—you must re-enter them. Rerun reuses stored config when safe; it fails with guidance if credentials are masked.

**Run retention**: Set `runs_retention_count` (default 100) and optionally `runs_retention_days` in config. Cleanup prunes old run metadata; call `POST /api/runs/cleanup` or let it run after creation.

### Streamlit UI (legacy)

```bash
uv run streamlit run src/data_forge/ui/app.py
```

Then open the app, pick a domain pack or upload schema/rules, set seed and scale, and generate.

## Project layout

```
data-forge/
├── src/data_forge/
│   ├── models/           # Schema, rules, generation request/result
│   ├── schema_ingest/     # SQL DDL, JSON Schema, OpenAPI parsers
│   ├── rule_engine/       # Load and evaluate YAML rules
│   ├── generators/        # Primitives, table, distributions, relationship_builder
│   ├── anomaly_injector/  # Nulls, duplicates, bad data
│   ├── validators/        # Quality report, referential integrity
│   ├── adapters/         # Database adapters (SQLite, DuckDB, Postgres, Snowflake, BigQuery)
│   ├── exporters/        # CSV, JSON, Parquet, SQL
│   ├── domain_packs/     # SaaS + e-commerce pack loader
│   ├── api/              # FastAPI backend for product UI
│   ├── ui/               # Streamlit app (legacy)
│   ├── cli.py             # Typer CLI
│   └── engine.py          # Main pipeline
├── schemas/               # .sql and .json schemas
├── rules/                 # .yaml rule sets
├── output/                # Generated data (gitignored)
├── runs/                  # Run records (JSON, gitignored)
├── frontend/              # Next.js product UI
├── docker-compose.yml     # Postgres (and optional Redpanda)
├── pyproject.toml
└── README.md
```

## Environment presets (config)

- `UNIT_TEST`: minimal, fast, deterministic  
- `INTEGRATION_TEST`: realistic relations, medium volume  
- `LOAD_TEST`: high volume  
- `DEMO_DATA` / `UAT`: demo- and UAT-style  

Set `DATA_FORGE_ENVIRONMENT` or use defaults in `data_forge.config.Settings`.

## Roadmap

- **Phase 1** (current): Rules engine, schema import, relational generator, exporters, quality report, CLI + Streamlit, domain packs (SaaS, e-commerce).
- **Phase 2**: OpenAPI payload generation, event stream simulator, CI deterministic mode, bad-data mode presets.
- **Phase 3**: SDV-backed learned realism, privacy similarity/leakage metrics, dbt + Kafka integration.

## License

MIT.
