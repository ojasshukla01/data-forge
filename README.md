<p align="center">
  <img src="docs/hero.png" alt="Data Forge — Time-Aware Synthetic Data Platform" width="800" />
</p>

<h1 align="center">Data Forge</h1>
<p align="center">
  <strong>Time-Aware Synthetic Data Platform</strong>
</p>
<p align="center">
  <em>Schema-aware synthetic data for databases, APIs, and pipelines. Realistic, relational, privacy-safe.</em>
</p>

<p align="center">
  <a href="#-quick-start"><strong>Quick Start</strong></a> •
  <a href="#-demo"><strong>Demo</strong></a> •
  <a href="#-scenarios--runs"><strong>Scenarios</strong></a> •
  <a href="#-core-workflows"><strong>Workflows</strong></a> •
  <a href="#-docs"><strong>Docs</strong></a> •
  <a href="docs/demo-walkthrough.md"><strong>Walkthrough</strong></a> •
  <a href="#-contributing"><strong>Contributing</strong></a>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-14b8a6?style=flat" alt="License" /></a>
  <img src="https://img.shields.io/badge/Python-3.10+-14b8a6?style=flat" alt="Python" />
  <img src="https://img.shields.io/badge/Node-18+-14b8a6?style=flat" alt="Node" />
  <img src="https://img.shields.io/badge/Next.js-16-14b8a6?style=flat" alt="Next.js" />
</p>

---

**Data Forge** generates business-valid, cross-table, time-consistent, privacy-safe synthetic data—not hand-written fixtures, but **test-ready data** that respects schemas, foreign keys, business rules, and optional anomaly injection. Built for demos, UAT, integration testing, and pipeline development.

> *Open-source • Python backend • Next.js frontend • Local-first • Made for data engineers*

---

## ✨ Why Data Forge is different

| Typical approach | Data Forge |
|-----------------|-----------|
| Hand-rolled CSV/JSON fixtures | **Schema-driven generation** — use your DDL, JSON Schema, or OpenAPI; FK and rules respected |
| One-off scripts per project | **Reusable scenarios** — save configs, run from wizard or Advanced, compare runs, version with scenarios |
| No pipeline realism | **ETL modes** — full snapshot, incremental, CDC; bronze/silver/gold; schema drift and messiness profiles |
| Guesswork on scale | **Benchmark mode** — scale presets, workload profiles, throughput and memory metrics |
| Isolated tables | **Domain packs** — 10+ packs (SaaS, e-commerce, fintech, healthcare, IoT, etc.) with event streams and benchmark relevance |

---

## 📋 Feature matrix

| Area | Capabilities |
|------|--------------|
| **Schema** | SQL DDL, JSON Schema, OpenAPI (table-like); YAML business rules; PK/FK resolution |
| **Generation** | Full snapshot, incremental, CDC; bronze/silver/gold; drift, messiness; anomaly injection |
| **Export** | CSV, JSON, JSONL, Parquet, SQL inserts |
| **Load** | SQLite, DuckDB, PostgreSQL, Snowflake, BigQuery |
| **Integrations** | dbt seeds, Great Expectations, Airflow DAGs, OpenAPI contract fixtures |
| **Simulation** | Event streams, time patterns (steady/burst/seasonal/growth), replay modes |
| **Benchmark** | Scale presets (small → xlarge), workload profiles, throughput/memory metrics |
| **Quality** | Schema validation, GE expectations, manifest reconciliation, privacy detection |

---

## 🚀 Quick Start

### Install

```bash
cd data-forge
uv sync
```

If `uv` is unavailable, use a standard virtual environment:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -e ".[dev]"
```

Optional extras:
- `uv sync --extra warehouse` or `.venv\Scripts\python -m pip install -e ".[warehouse]"`
- `uv sync --extra streamlit` or `.venv\Scripts\python -m pip install -e ".[streamlit]"`
- `uv sync --extra all` or `.venv\Scripts\python -m pip install -e ".[all]"`

### Generate from a domain pack

```bash
uv run data-forge generate --pack saas_billing --scale 1000 -o output -f parquet
uv run data-forge generate --pack ecommerce --scale 2000 -o output -f sql
```

### Run the Product UI

```bash
# Terminal 1: API
uv run uvicorn data_forge.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

Open **http://localhost:3000**. See [docs/demo-walkthrough.md](docs/demo-walkthrough.md) for a step-by-step walkthrough.

---

## 🎬 Demo

One-command demo (no cloud credentials):

```bash
make demo-data
# or: ./scripts/run_demo.ps1  (Windows)  /  ./scripts/run_demo.sh  (Linux/macOS)
```

Outputs go to `demo_output/`. Start the API and frontend to inspect runs and artifacts in the UI.

---

## 📋 Scenarios & runs

- **Scenarios** — Save configs from Advanced or the Create Wizard; load in wizard or Advanced; update or save-as-new; edit metadata on the scenario detail page. Import from `examples/scenarios/`.
- **Runs** — Every generation or benchmark creates a run (history, timeline, logs, artifacts). Compare two runs side-by-side (config, summary, benchmark, raw diff).
- **Artifacts** — Datasets, event streams, dbt seeds, GE suites, DAGs; filter by run or type.

---

## 🔄 Core workflows

1. **Generate a dataset** — Wizard or Advanced → pick pack or custom schema (Schema Studio) → set scale/options → run. Output in Runs and Artifacts.
2. **Run simulation** — Advanced → Pipeline Simulation → enable event streams, set density/pattern/replay → run.
3. **Benchmark warehouse load** — Advanced → Benchmark → profile and scale preset → run. View throughput and duration on run detail.
4. **Compare runs** — Runs → open a run → “Compare with another run”, or `/runs/compare`. Use raw JSON diff for debugging.
5. **Save scenario** — After configuring, “Save as scenario” (or “Update scenario” if loaded). Reuse from Scenarios or wizard.

---

## 📁 Project structure at a glance

```
data-forge/
├── src/data_forge/          # Backend
│   ├── api/                 # FastAPI app, routers, stores, middleware
│   ├── models/              # Schema, config, generation, manifest
│   ├── engine.py            # Core run_generation, export_result
│   ├── schema_ingest/       # SQL, JSON Schema, OpenAPI parsers
│   ├── rule_engine/         # YAML business rules
│   ├── generators/          # Primitives, distributions, FK resolution
│   ├── adapters/            # SQLite, DuckDB, Postgres, Snowflake, BigQuery
│   ├── exporters/           # CSV, JSON, Parquet, SQL
│   ├── domain_packs/        # Pre-built schemas and rules
│   ├── simulation/          # Event streams, time patterns
│   └── services/            # Run, scenario, lineage, retention, metrics
├── frontend/                # Next.js product UI (wizard, runs, Schema Studio)
├── tests/                   # Pytest backend tests
├── frontend/e2e/            # Playwright E2E tests
├── examples/scenarios/      # Example scenario JSONs
├── scripts/                 # validate_all.*, run_demo.*
├── docs/                    # Architecture, API reference, testing, CI, security
└── .github/workflows/       # CI (backend, frontend, E2E)
```

---

## 🛠 Developer platform capabilities

- **CLI** — `data-forge generate`, `benchmark`, `validate`, `reconcile`, `packs`; full control from the shell.
- **API** — Start runs, list runs/artifacts/scenarios, compare runs, preflight, benchmark. Local JSON persistence.
- **UI** — Wizard and Advanced config, run history and detail, scenario library, artifact browser, Schema Studio (custom schemas, validation, version diff), validation center, run comparison.
- **CI** — GitHub Actions: backend ruff, mypy, pytest; frontend type-check, tests, build; Playwright E2E. Local: `make validate-all`. See [docs/ci-cd.md](docs/ci-cd.md).
- **API** — `POST /api/runs/generate`, `GET /api/runs`, `GET /api/runs/compare`, `POST /api/benchmark`, `GET /api/scenarios`, `GET /api/artifacts`, `POST /api/preflight`.

---

## ⚡ Pipeline simulation & benchmark

- **Simulation:** Event streams (e.g. order lifecycle, payments), time patterns, replay modes. Packs: ecommerce, fintech, logistics, IoT, social, saas_billing.
- **Benchmark:** Scale presets (small ~10k → xlarge ~10M), workload profiles, throughput (rows/s), duration, memory estimates.

```bash
uv run data-forge benchmark --pack saas_billing --scale 5000 --iterations 3 --output-json bench.json
```

---

## 🗄 Database loading

| Adapter | Usage |
|---------|-------|
| SQLite | `--load sqlite --db-uri ./data.db` |
| DuckDB | `--load duckdb --db-uri ./data.duckdb` |
| PostgreSQL | `--load postgres --db-uri postgresql://user:pass@host/db` |
| Snowflake / BigQuery | Env vars or flags (see CLI help) |

---

## 📚 Integrations

<details>
<summary><b>dbt, Great Expectations, Airflow, Reconciliation</b></summary>

- **dbt:** `--export-dbt --dbt-dir ./dbt_project` — seeds, sources, schema tests.
- **GE:** `--export-ge --ge-dir ./great_expectations`; validate with `data-forge validate-ge`.
- **Airflow:** `--export-airflow --airflow-dir ./airflow` — DAG templates.
- **Reconciliation:** `data-forge reconcile --manifest manifest.json --data ./output --schema schemas/...`
</details>

---

## 📋 Example commands

| Goal | Command |
|------|---------|
| Sample generation | `uv run data-forge generate --pack saas_billing --scale 1000 -o output -f parquet` |
| Benchmark | `uv run data-forge benchmark --pack saas_billing --scale 5000 --iterations 3 --output-json bench.json` |
| List packs | `uv run data-forge packs` |
| Load scenario (UI) | Scenarios → Import scenario → choose from `examples/scenarios/` |
| Compare runs (UI) | Runs → “Compare with another run” or `/runs/compare` |

---

## 🧪 Testing and validation

```bash
make validate-all
# or: scripts/validate_all.ps1 | scripts/validate_all.sh
```

Steps: backend **ruff**, **mypy**, pytest; frontend typecheck, unit tests, build. E2E: `make e2e` or `cd frontend && npm run e2e`. See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/testing.md](docs/testing.md).

---

## 📖 Docs (canonical)

| Doc | Description |
|-----|-------------|
| [Architecture](docs/architecture-current-state.md) | Repository structure, API surface, schema system, frontend routes, CI/E2E |
| [API Reference](docs/api-reference.md) | REST endpoints, request/response shapes, errors (413/429), lineage & manifest |
| [Testing](docs/testing.md) | Backend (ruff, mypy, pytest), frontend (Vitest), E2E (Playwright), validation checklist |
| [CI/CD](docs/ci-cd.md) | GitHub Actions pipeline, strict gates, local parity, troubleshooting |
| [Security](docs/security.md) | Schema limits, rate limiting, path safety, preview safety |
| [Schema Studio](docs/schema-studio.md) | Custom schemas: form/JSON, validation, preview, version history, restore |
| [Lineage & reproducibility](docs/lineage-and-reproducibility.md) | Run lineage, manifest, custom schema provenance |
| [Demo walkthrough](docs/demo-walkthrough.md) | Step-by-step UI walkthrough |

For the full docs index, versioning, and release checklist: [docs/INDEX.md](docs/INDEX.md), [docs/versioning.md](docs/versioning.md), [docs/release-checklist.md](docs/release-checklist.md). See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## 📸 Screenshots and assets

UI screenshots and demo assets: [docs/screenshots/](docs/screenshots/). Target filenames and checklist: [docs/screenshots/SCREENSHOT-CHECKLIST.md](docs/screenshots/SCREENSHOT-CHECKLIST.md).

---

## 🤝 Contributing

We welcome contributions. [CONTRIBUTING.md](CONTRIBUTING.md) covers setup, full validation (`make validate-all`, E2E), and adding scenarios/packs/tests. [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [SECURITY.md](SECURITY.md) for community and security.

## ⚠️ Known limitations

- **Local-first:** No cloud deployment; run API and frontend locally or in CI. Storage is file-based (or optional SQLite) for runs and scenarios.
- **E2E:** Playwright requires the API and frontend to be running; start both before `make e2e`. See [docs/testing.md](docs/testing.md).
- **Build:** On some environments (e.g. OneDrive-synced folders), `npm run build` may fail with EPERM; run from a non-synced path or close other tools. Type-check and unit tests still validate the codebase.
- **Maturity:** Data Forge is open-source and actively developed; some integrations and adapters are evolving. Check [docs/architecture-current-state.md](docs/architecture-current-state.md) and [docs/INDEX.md](docs/INDEX.md) for current scope.

---

## 📄 License

MIT.
