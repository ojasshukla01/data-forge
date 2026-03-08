<p align="center">
  <img src="docs/hero.png" alt="Data Forge — Time-Aware Synthetic Data Platform" width="800" />
</p>

<h1 align="center">Data Forge</h1>
<p align="center">
  <strong>Time-Aware Synthetic Data Platform</strong>
</p>
<p align="center">
  <em>Schema-aware synthetic data for databases, APIs, and pipelines</em>
</p>

<p align="center">
  <a href="#-quick-start"><strong>Quick Start</strong></a> •
  <a href="#-features">Features</a> •
  <a href="#-pipeline-simulation--warehouse-benchmark">Pipeline Simulation</a> •
  <a href="#-integrations">Integrations</a> •
  <a href="#-license">License</a>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-14b8a6?style=flat" alt="License" /></a>
  <img src="https://img.shields.io/badge/Python-3.10+-14b8a6?style=flat" alt="Python" />
  <img src="https://img.shields.io/badge/Next.js-16-14b8a6?style=flat" alt="Next.js" />
</p>

---

## ✨ Overview

**Data Forge** generates business-valid, cross-table, time-consistent, privacy-safe synthetic data—not just fake names and emails, but **test-ready data** that respects schemas, foreign keys, business rules, and optional anomaly injection. Built for demos, UAT, integration testing, and pipeline development.

> *An open-source, schema-aware synthetic data platform that generates realistic, relational, time-aware, edge-case-rich test data for databases, APIs, and pipelines.*

---

## 🚀 Quick Start

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

### Run the Product UI

```bash
# Terminal 1: Start the API
uv run uvicorn data_forge.api.main:app --reload --port 8000

# Terminal 2: Start the frontend
cd frontend && npm run dev
```

Open **http://localhost:3000** to use the web UI.

| Page | Description |
|------|-------------|
| **Home** | Hero, capabilities, domain pack showcase |
| **Create** | Guided wizard with domain packs, preflight validation |
| **Advanced** | Full config: schema, ETL, privacy, pipeline simulation, benchmark |
| **Templates** | Browse domain packs with event stream & benchmark metadata |
| **Scenarios** | Reusable configurations: save, load, import, export |
| **Runs** | Run history, stage timeline, logs, rerun, clone, compare |
| **Artifacts** | Browse datasets, event streams, snapshots, dbt, GE, DAGs |
| **Schema** | Interactive schema visualizer (React Flow) |

---

## 📦 Features

| Category | Capabilities |
|----------|--------------|
| **Schema import** | SQL DDL, JSON Schema, OpenAPI (table-like extraction) |
| **Rule engine** | YAML business rules (order, range, sum, equality) and distribution hints |
| **Relational integrity** | PK/FK resolution across tables in dependency order |
| **Export** | CSV, JSON, JSONL, Parquet, SQL inserts |
| **Anomaly injection** | Optional nulls, duplicates, invalid enums, malformed strings |
| **Domain packs** | 10+ packs: SaaS, e-commerce, fintech, healthcare, logistics, IoT, social, and more |
| **Integrations** | dbt seeds, Great Expectations, Airflow DAGs, OpenAPI contracts |

---

## ⚡ Pipeline Simulation & Warehouse Benchmark

### Pipeline simulation

Generate event-stream-style artifacts and pipeline snapshots:

- Event streams for e-commerce order lifecycles, fintech payments, logistics, IoT telemetry, social activity
- Time patterns: `steady`, `burst`, `seasonal`, `growth`
- Replay modes: `ordered`, `shuffled`, `windowed`
- Configure via Advanced Config or API with `pipeline_simulation.enabled`, `event_density`, `event_pattern`, `replay_mode`

### Warehouse benchmark mode

- Scale presets: `small` (~10k), `medium` (~100k), `large` (~1M), `xlarge` (~10M rows)
- Workload profiles: `wide_table`, `high_cardinality`, `event_stream`, `fact_table`
- Metrics: throughput (rows/s), generation/export duration, memory estimates

```bash
# Benchmark with scale preset
uv run data-forge benchmark --pack saas_billing --scale 5000 --iterations 3 --output-json bench.json
```

---

## 🗄️ Database loading

| Adapter | Usage |
|---------|-------|
| **SQLite** | `--load sqlite --db-uri ./data.db` |
| **DuckDB** | `--load duckdb --db-uri ./data.duckdb` |
| **PostgreSQL** | `--load postgres --db-uri postgresql://user:pass@host/db` |
| **Snowflake** | `--load snowflake` (env vars for credentials) |
| **BigQuery** | `--load bigquery` (Google ADC) |

---

## 📋 Saved scenarios & run comparison

### Scenarios

Save configurations as reusable scenarios. Load them in the Create wizard, Advanced config, or run directly.

- **Start from scenario** in Create wizard (`/create/wizard?scenario=<id>`) or use the "Use a saved scenario" entry point
- **Save scenario** from Advanced config (name, category, description)
- **Create from run** on run detail page
- **Scenario library** at `/scenarios` — run, edit, export, import
- **Import/export** as JSON
- **Example scenarios** in `examples/scenarios/` (ecommerce, fintech, logistics, IoT, warehouse benchmark)

### Compare runs

Compare two runs side-by-side: config, summary, benchmark, simulation, and artifact diffs. Includes a collapsible raw JSON diff for developer workflows.

- From run detail: "Compare with another run"
- Or go to `/runs/compare` and select left/right runs

---

## 📚 Integrations

<details>
<summary><b>dbt export</b></summary>

```bash
uv run data-forge generate --pack ecommerce --export-dbt --dbt-dir ./dbt_project -o output
```

Seeds, `sources.yml`, and schema test templates.
</details>

<details>
<summary><b>Great Expectations</b></summary>

```bash
uv run data-forge generate --pack saas_billing --export-ge --ge-dir ./great_expectations -o output
uv run data-forge validate-ge --expectations ./great_expectations --data ./output
```

Expectation suites and checkpoints; validation without GE runtime.
</details>

<details>
<summary><b>Airflow DAGs</b></summary>

```bash
uv run data-forge generate --pack saas_billing --export-airflow --airflow-dir ./airflow -o output
```

Templates: `generate_only`, `generate_and_load`, `generate_validate_and_load`, `benchmark_pipeline`.
</details>

<details>
<summary><b>Reconciliation</b></summary>

```bash
uv run data-forge reconcile --manifest manifest.json --data ./output --schema schemas/saas_billing.sql
```

Compare manifest expected row counts vs actual data.
</details>

---

## 📁 Project layout

```
data-forge/
├── src/data_forge/
│   ├── models/          # Schema, rules, generation request/result
│   ├── schema_ingest/   # SQL DDL, JSON Schema, OpenAPI parsers
│   ├── rule_engine/     # YAML business rules
│   ├── generators/      # Primitives, distributions, FK resolution
│   ├── adapters/        # SQLite, DuckDB, Postgres, Snowflake, BigQuery
│   ├── exporters/       # CSV, JSON, Parquet, SQL
│   ├── domain_packs/    # Pre-built schemas and rules
│   ├── simulation/      # Event streams, time patterns
│   └── api/             # FastAPI backend
├── frontend/            # Next.js product UI
├── schemas/             # .sql and .json schemas
├── rules/               # .yaml rule sets
└── docs/                # Hero image, additional docs
```

---

## 🔧 CLI reference

```bash
# Generation
uv run data-forge generate -s schemas/my.sql -r rules/my.yaml --scale 5000 -o output -f csv

# Validation
uv run data-forge validate schemas/saas_billing.sql
uv run data-forge validate-ge --expectations ./ge --data ./output

# Reconciliation
uv run data-forge reconcile --manifest manifest.json --data ./output --schema schemas/saas_billing.sql

# Domain packs
uv run data-forge packs
```

---

## 🌐 API

- `POST /api/runs/generate` — Start async generation
- `GET /api/runs/compare?left=&right=` — Compare two runs
- `POST /api/benchmark` — Run performance benchmark
- `GET /api/domain-packs` — List domain packs
- `GET /api/artifacts` — List generated artifacts
- `POST /api/preflight` — Validate config before run
- `GET /api/scenarios` — List scenarios
- `POST /api/scenarios` — Create scenario
- `POST /api/scenarios/from-run/{run_id}` — Create scenario from run

See the [Product UI section](#run-the-product-ui) for the full API surface.

## 🧪 Testing

- **Backend:** `uv run pytest -q`
- **Frontend:** `cd frontend && npm test`
- **Frontend build:** `cd frontend && npm run build`

See [CONTRIBUTING.md](./CONTRIBUTING.md) for more details.

---

## 📄 License

MIT.
