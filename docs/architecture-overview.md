# Architecture overview

Data Forge is a **local-first** platform: a Python backend (CLI + FastAPI), a Next.js frontend, and local JSON persistence for runs, scenarios, and artifacts. No database required for core operation.

## High-level components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Product UI (Next.js)                       │
│  Wizard • Advanced config • Runs • Scenarios • Artifacts • Compare │
└───────────────────────────────────┬─────────────────────────────┘
                                    │ HTTP (localhost)
┌───────────────────────────────────▼─────────────────────────────┐
│                     FastAPI backend (Python)                     │
│  Runs API • Scenarios API • Benchmark • Preflight • Artifacts    │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────┐
│  Generation engine • Schema ingest • Rule engine • Exporters      │
│  Domain packs • Simulation (event streams) • Adapters (DB load)   │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────┐
│  Local persistence: runs/*.json, scenarios, artifact registry    │
└─────────────────────────────────────────────────────────────────┘
```

- **Frontend** talks to the API only. All run/scenario/artifact state is stored and served by the backend.
- **Backend** runs generation in a background task; run status and events are written to JSON files under a local data directory.
- **CLI** uses the same engine (schema ingest, rules, generators, exporters) without the API; output goes to a directory you specify.

## Generation pipeline flow

1. **Config** — Pack (or schema + rules), scale, mode (full_snapshot / incremental / cdc), layer (bronze/silver/gold), options (anomalies, privacy, simulation, etc.).
2. **Preflight** — Optional validation of config and schema before starting.
3. **Schema + rules load** — From domain pack or from files.
4. **Generation** — Tables in dependency order; FK resolution; optional drift, messiness, anomaly injection; simulation events if enabled.
5. **Export** — Parquet, CSV, JSON, JSONL, SQL to output directory.
6. **Optional** — Load to DB (SQLite, DuckDB, Postgres, etc.), export dbt/GE/Airflow, write manifest.

See [diagrams/generation-pipeline.md](diagrams/generation-pipeline.md) for a Mermaid flow.

## Run, scenario, and artifact relationships

- A **run** is one execution (generate or benchmark). It has a unique ID, config snapshot, status, timeline, result summary, and optional `source_scenario_id`.
- A **scenario** is a saved config (name, category, tags, full config blob). Runs can be started *from* a scenario; the run then stores `source_scenario_id`.
- **Artifacts** are output files (datasets, event streams, dbt, GE, etc.) registered per run. The artifact registry maps run ID → list of files with paths and types.

So: **Scenario → (optional) → Run → Artifacts**. You can also create a scenario *from* a run (clone config).

See [diagrams/run-scenario-artifact.md](diagrams/run-scenario-artifact.md) for a diagram.

## Pipeline simulation flow

When pipeline simulation is enabled:

1. Config specifies event density, pattern (steady/burst/seasonal/growth), replay mode (ordered/shuffled/windowed).
2. Generation produces both table data and event-stream data (e.g. order lifecycle, payment events).
3. Event streams are written as JSONL (or similar) alongside table exports.
4. Run summary includes event counts and simulation metadata.

See [diagrams/pipeline-simulation.md](diagrams/pipeline-simulation.md).

## Benchmark workflow

1. User triggers benchmark (UI or API) with pack, scale, iterations, optional load target.
2. Backend runs N iterations of generate + export (and optionally load).
3. Timings (generation, export, load) and row counts are collected.
4. Throughput (rows/s), duration, and memory estimate are computed and stored in the run result summary.

See [diagrams/benchmark-workflow.md](diagrams/benchmark-workflow.md).

## Frontend–backend–API interaction

- **Create (wizard or Advanced):** Frontend sends config to `POST /api/runs/generate` or `POST /api/benchmark`. Backend enqueues a task and returns run ID. Frontend redirects to run detail.
- **Run detail:** Frontend polls or fetches run by ID; displays status, timeline, logs, summary, links to artifacts.
- **Scenarios:** List via `GET /api/scenarios`; create/update via POST/PUT; run from scenario via `POST /api/scenarios/{id}/run`.
- **Compare:** Frontend sends left/right run IDs to `GET /api/runs/compare?left=...&right=...` and renders diff tables and raw JSON diff.
- **Artifacts:** Frontend fetches artifact list for a run (or global) and shows download/preview links; files are served from backend or local paths.

All APIs are REST-style; no WebSockets. Long-running runs are observed by polling run status.
