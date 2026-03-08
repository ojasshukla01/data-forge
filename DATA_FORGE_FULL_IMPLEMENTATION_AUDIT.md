# Data Forge — Full Implementation Audit

**Audit date:** 2025-03-08  
**Repository:** data-forge (schema-aware synthetic data platform)  
**Scope:** Entire local repository (backend, frontend, API, domain packs, tests, docs)

---

## 1. Executive Summary

**What the project is:** Data Forge is a schema-aware synthetic data platform that generates relational, time-aware, business-rule-compliant test data. It supports SQL/JSON/OpenAPI schema import, YAML business rules, anomaly injection, ETL realism (full snapshot/incremental/CDC, bronze/silver/gold layers), privacy detection/redaction, warehouse loading (SQLite, DuckDB, Postgres, Snowflake, BigQuery), and exports (CSV, JSON, Parquet, SQL, dbt, GE, Airflow DAGs). The product consists of a Python backend (CLI + FastAPI), a legacy Streamlit UI, and a Next.js product UI.

**Overall maturity:** **Alpha (3/5)**. The backend engine is solid and feature-rich. The CLI is production-capable. The API and Next.js UI are functional but several integrations are CLI-only, not wired through the API. The async run model works but is local-first and not resilient. UI polish is MVP-level.

**Biggest strengths:**
- Rich generation pipeline (schema, rules, FKs, messiness, drift, CDC, anomaly injection, quality report)
- 10 domain packs with SQL schemas and YAML rules
- Five database adapters, dbt/GE/Airflow exports
- Privacy/PII detection and redaction
- Good backend test coverage (adapters, engine, validators, API, ETL, GE, reconciliation)

**Biggest gaps:**
- API generation path does NOT execute dbt export, GE export, Airflow export, contracts, or manifest — these exist only in CLI
- Clone flow: frontend redirects to advanced config with `?clone=` but the advanced page never reads it; prefill is broken
- Runs list has no filters UI (status, pack, run_type) despite API support
- Run logs/events endpoint exists but run detail page does not display them
- No run cancellation
- No run cleanup/retention

**Category:** **Generator + Platform shell**. It is a powerful synthetic data generator with a product shell around it. The shell is usable but undersells the backend.

**Readiness:**
- **Portfolio/demo:** Yes. Wizard, templates, schema visualizer, runs, async progress, and artifacts work.
- **Open-source release:** Partial. README is good; CONTRIBUTING, changelog, architecture docs are minimal or absent.
- **Real team usage:** Limited. UI checkboxes for dbt/GE/Airflow/contracts do nothing; clone prefill broken; no benchmark UI.
- **Production-adjacent experimentation:** Yes for CLI. API path is suitable for local/dev use; not hardened for multi-user production.

---

## 2. Repository Map

### Top-level structure

| Path | Purpose |
|------|---------|
| `src/data_forge/` | Core Python package |
| `schemas/` | SQL schema files for domain packs |
| `rules/` | YAML rule files for domain packs |
| `output/` | Generated data (gitignored) |
| `runs/` | Run metadata JSON (gitignored) |
| `frontend/` | Next.js product UI |
| `tests/` | Pytest tests |
| `pyproject.toml` | Python project config |
| `docker-compose.yml` | Postgres (and optional Redpanda) |

### Backend (`src/data_forge/`)

| Path | Purpose |
|------|---------|
| `engine.py` | Main pipeline: ingest → generate → FK resolution → messiness → drift → CDC → anomalies → validate → export |
| `cli.py` | Typer CLI: generate, packs, validate, benchmark, reconcile |
| `config.py` | Settings, env presets, OutputFormat |
| `models/` | Schema, rules, generation request/result |
| `schema_ingest/` | SQL DDL, JSON Schema, OpenAPI parsers |
| `rule_engine/` | Load and evaluate YAML rules |
| `generators/` | Primitives, table, distributions, relationship_builder, cdc_simulator, messiness, schema_drift, layers |
| `anomaly_injector/` | Nulls, duplicates, invalid enums, malformed strings |
| `validators/` | Quality report, referential integrity |
| `exporters/` | CSV, JSON, JSONL, Parquet, SQL |
| `adapters/` | SQLite, DuckDB, Postgres, Snowflake, BigQuery |
| `domain_packs/` | Pack loader and PACK_METADATA |
| `pii/` | Classifier and redaction |
| `contracts/` | OpenAPI fixture generation, validation |
| `warehouse_validation/` | Row count and load verification |
| `golden.py` | Manifest creation |
| `dbt_export.py`, `ge_export.py`, `ge_validation.py`, `airflow_export.py`, `reconciliation.py` | Integrations |
| `performance.py` | Timings, warnings, memory estimates |
| `api/` | FastAPI app, run_store, task_runner, services, schemas, routers |
| `ui/` | Streamlit legacy app |

### API (`src/data_forge/api/`)

| Path | Purpose |
|------|---------|
| `main.py` | FastAPI app, CORS, routers |
| `run_store.py` | JSON-based run persistence in `runs/` |
| `task_runner.py` | Background execution, stage tracking |
| `services.py` | run_generate: pack/schema load → run_generation → export_result |
| `schemas.py` | Pydantic request/response models |
| `routers/` | domain_packs, generate, preflight, validate, artifacts, schema_viz, runs |

### Frontend (`frontend/src/`)

| Path | Purpose |
|------|---------|
| `app/` | Next.js App Router pages |
| `components/` | AppShell, TopNav, ui (Button, Card) |
| `lib/` | api.ts, utils.ts |
| `stores/` | wizardStore (Zustand) |

### Tests

| Path | Purpose |
|------|---------|
| `test_api.py` | Health, domain packs, generate, preflight, schema viz, artifacts, runs |
| `test_engine.py` | run_generation, export_result |
| `test_schema_ingest.py` | DDL parse, load |
| `test_rule_engine.py` | Rule evaluation |
| `test_validators.py` | Quality report, referential integrity |
| `test_exporters.py` | CSV, JSON, Parquet, SQL |
| `test_anomaly_injector.py` | Anomaly injection |
| `test_adapters.py` | SQLite, DuckDB, Postgres, warehouse load |
| `test_etl_milestone.py` | CDC, incremental, layers, drift, messiness |
| `test_ge_airflow_milestone.py` | GE export/validation, Airflow, reconciliation |
| `test_cloud_dbt_milestone.py` | Snowflake/BigQuery adapters, dbt, warehouse validation |
| `test_privacy_contract_milestone.py` | PII, redaction, contracts |
| `test_performance_milestone.py` | Chunking, benchmark, timings |
| `test_path_security.py` | Path traversal protection |
| `test_cli.py` | CLI generate, packs, validate |

---

## 3. Backend Feature Audit

### Schema ingest

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| SQL DDL | Complete | `schema_ingest/sql_ddl.py`, `load_schema()` | Parses CREATE TABLE, PKs, FKs, types |
| JSON Schema | Complete | `schema_ingest/json_schema.py` | Extracts tables from definitions |
| OpenAPI | Complete | `schema_ingest/__init__.py` _parse_openapi | Extracts schemas from components/schemas |
| YAML schemas | Supported | `load_schema()` | Via yaml.safe_load |
| Path security | Complete | `config.ensure_path_allowed`, `test_path_security.py` | Blocks traversal outside project root |

### Rule engine

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| Load YAML rules | Complete | `rule_engine/__init__.py` load_rule_set | business_rules, distribution_rules |
| Order rules | Complete | `evaluate_rule`, order type | started_at <= ended_at style |
| Range rules | Complete | `evaluate_rule`, range type | min/max bounds |
| Sum rules | Complete | rule_type: sum | amount_cents = quantity * unit_price_cents |
| Distribution rules | Complete | `generators/distributions.py` | categorical, skewed, seasonal |
| Rule violations in quality report | Complete | `validators/quality.py` | Samples, by_rule counts |

### Generators

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| PrimitiveGenerator | Complete | `generators/primitives.py` | Faker/Mimesis, type mapping |
| Table generation | Complete | `generators/table.py` | Row count, distributions, parent_key_supplier |
| RelationshipBuilder | Complete | `generators/relationship_builder.py` | assign_foreign_keys |
| Row count logic | Partial | `engine.py` L91–99 | Hardcoded table names (users, orders, invoice_line_items); new packs may not scale well |
| Chunked generation | Complete | `engine.py` L99–114 | chunk_size support |
| CDC simulator | Complete | `generators/cdc_simulator.py` | op_type, change_ratio |
| Incremental mode | Complete | batch_id, timestamps |
| Messiness | Complete | `generators/messiness.py` | CLEAN, REALISTIC, CHAOTIC |
| Schema drift | Complete | `generators/schema_drift.py` | MILD, MODERATE, AGGRESSIVE |
| Bronze/silver/gold | Complete | `generators/layers.py` | transform_to_layer |

### Anomaly injection

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| Null injection | Complete | `anomaly_injector/__init__.py` | ratio-based |
| Duplicate injection | Complete | Duplicates rows |
| Invalid enum | Complete | Bad values for categorical |
| Malformed strings | Complete | Truncation, bad encoding |
| Ratio control | Complete | anomaly_ratio, messiness affects it |

### Validators / quality report

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| Referential integrity | Complete | `validators/quality.py` _ref_integrity | FK checks |
| Rule violations | Complete | _collect_rule_violations | Samples, by_rule |
| Privacy audit | Complete | PII detection, redaction in report |
| Performance warnings | Complete | collect_performance_warnings |
| Warehouse validation | Complete | run_warehouse_validation | Row count match |

### Privacy / PII

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| PII classifier | Complete | `pii/classifier.py` | email, phone, dob, etc. |
| Redaction | Complete | `pii/redaction.py` | RedactConfig, redact_samples |
| Privacy modes | Complete | off, warn, strict |
| Quality report integration | Complete | compute_quality_report |

### Contracts

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| OpenAPI fixtures | Complete | `contracts/fixtures.py` | CLI only |
| Contract validation | Complete | `contracts/validate.py` | JSON Schema |
| API path | Missing | services.py | No contracts generation in API |

### Exporters

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| CSV, JSON, JSONL, Parquet, SQL | Complete | `exporters/__init__.py` | All used in API |
| dbt export | Complete | `dbt_export.py` | CLI only, not API |
| GE export | Complete | `ge_export.py` | CLI only, not API |
| Airflow export | Complete | `airflow_export.py` | CLI only, not API |

### Database adapters

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| SQLite | Complete | `adapters/sqlite_adapter.py` | Used in API |
| DuckDB | Complete | `adapters/duckdb_adapter.py` | Used in API |
| Postgres | Complete | `adapters/postgres_adapter.py` | Used in API |
| Snowflake | Complete | `adapters/snowflake_adapter.py` | Env vars |
| BigQuery | Complete | `adapters/bigquery_adapter.py` | Env vars |

### Warehouse validation

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| Row count check | Complete | `warehouse_validation/` | After load |
| Load report | Complete | quality_report["warehouse_load"] | In engine and API |

### Reconciliation

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| Manifest vs data | Complete | `reconciliation.py` | Via /api/reconcile |
| Missing tables, row diffs | Complete | run_reconciliation | Tested |

### Benchmark / performance

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| Benchmark CLI | Complete | `cli.py` benchmark command | Iterations, JSON output |
| Chunk size | Complete | engine, services | Memory-safe |
| Performance warnings | Complete | collect_performance_warnings | Scale >= 50k |
| API benchmark | Missing | No POST /api/benchmark | CLI only |

### Async run execution

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| Run model | Complete | run_store.py | id, status, stages, config, result_summary |
| Background task | Complete | task_runner.py, FastAPI BackgroundTasks | execute_generation_async |
| Stage tracking | Partial | STAGES list; schema_load, rule_load, generation, export, complete marked | Anomaly, ETL, contract, warehouse stages are in STAGES but not actually updated per-phase |
| Event logs | Complete | append_event, get_run with events | Events stored; UI does not show them |
| Rerun | Complete | POST /api/runs/{id}/rerun | Uses stored config |
| Clone | Complete | POST /api/runs/{id}/clone | Returns config; frontend prefill broken |
| Cancel | Missing | Not implemented | Optional per spec |
| Run cleanup | Missing | No retention/rotation | runs/ grows indefinitely |

### Config / settings

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| Settings | Complete | `config.py` | project_root, output_dir, locale |
| Env presets | Complete | UNIT_TEST, INTEGRATION_TEST, etc. | DATA_FORGE_ENVIRONMENT |
| SecurityError | Complete | Path validation | Blocks escape |

### Domain pack system

| Aspect | Status | Evidence | Notes |
|--------|--------|----------|-------|
| list_packs | Complete | domain_packs/__init__.py | 10 packs |
| get_pack | Complete | Loads schema + rules from schemas/, rules/ |
| PACK_METADATA | Complete | name, category, key_entities, recommended_use_cases, supported_features | Used by API |
| API PackInfo | Complete | domain_packs router | Rich metadata |

---

## 4. Domain Pack Audit

### Pack summary

| Pack ID | Tables | Business rules | Distribution rules | Category | Schema richness | Rule richness | UI exposure |
|---------|--------|----------------|-------------------|----------|-----------------|---------------|-------------|
| saas_billing | 7 | 3 | 4 | SaaS/CRM | High | High | Full |
| ecommerce | 6 | 3 | 3 | Retail | High | High | Full |
| fintech_transactions | 7 | 3 | 3 | Fintech | High | High | Full |
| healthcare_ops | 7 | 2 | 3 | Healthcare | High | Medium | Full |
| logistics_supply_chain | 9 | 4 | 3 | Logistics | High | High | Full |
| adtech_analytics | 8 | 3 | 2 | AdTech | High | Medium | Full |
| hr_workforce | 6 | 4 | 2 | HR | High | High | Full |
| iot_telemetry | 6 | 2 | 3 | IoT | High | Medium | Full |
| social_platform | 8 | 1 | 2 | Social | High | Low | Full |
| payments_ledger | 7 | 3 | 3 | Payments | High | High | Full |

### Strongest packs

- **logistics_supply_chain**: 9 tables, 7 rules, rich FK graph
- **saas_billing**: Well-tested, clear entities, strong rules
- **fintech_transactions**: Solid transaction/settlement semantics

### Weakest packs

- **social_platform**: Only 1 business rule; could use more (e.g. follows user_id != followed_user_id)
- **healthcare_ops**, **iot_telemetry**: Fewer business rules

### Pack metadata for UI

- PackInfo includes: id, name, description, category, tables_count, relationships_count, key_entities, recommended_use_cases, supported_features
- Templates list uses id and description; template detail uses tables, relationships, key_entities
- Wizard shows pack cards with description and tables_count

### Gaps

- No pack-level row_estimate hints used in generation (engine uses hardcoded table-name logic)
- key_entities and recommended_use_cases are static; no dynamic derivation from schema

---

## 5. API Layer Audit

### Routers and endpoints

| Method | Route | Purpose | Used by frontend |
|--------|-------|---------|------------------|
| GET | /health | Health check | Implicit |
| GET | /api/domain-packs | List packs | Wizard, Templates, Schema |
| GET | /api/domain-packs/{id} | Pack detail | Template detail |
| POST | /api/generate | Sync generation | No (legacy) |
| POST | /api/runs/generate | Async generation | Wizard, Advanced |
| GET | /api/runs | List runs | Runs list |
| GET | /api/runs/{id} | Run detail | Run detail |
| GET | /api/runs/{id}/status | Status for polling | Run detail |
| GET | /api/runs/{id}/logs | Run events | No |
| POST | /api/runs/{id}/rerun | Rerun | Run detail |
| POST | /api/runs/{id}/clone | Clone config | Run detail |
| POST | /api/preflight | Preflight validation | Wizard, Advanced |
| GET | /api/schema/visualize | Schema nodes/edges | Schema page |
| GET | /api/artifacts | List artifacts | Artifacts page |
| GET | /api/artifacts/file | Download artifact | Artifacts page |
| POST | /api/validate | Schema+rules validation | Validate page |
| POST | /api/validate/ge | GE validation | Validate page |
| POST | /api/reconcile | Manifest reconciliation | Validate page |

### Unused or partial

- **GET /api/runs/{id}/logs** — Implemented but run detail page does not display logs
- **POST /api/generate** — Sync endpoint; frontend uses async only
- **Runs list filters** — API supports status, run_type, pack; frontend does not expose them

### Request/response consistency

- GenerateRequest has many fields; API services uses only a subset (no export_dbt, export_ge, export_airflow, contracts, write_manifest in pipeline)
- Clone returns `{ config }`; rerun returns `{ run_id, status }`; consistent
- Preflight returns valid, blockers, warnings, recommendations, estimated_rows, estimated_memory_mb

### Service separation

- `services.run_generate` handles pack/schema load, GenerationRequest build, run_generation, export_result
- Does NOT call: dbt_export, ge_export, airflow_export, contracts, write_manifest

### Missing APIs for UX

- POST /api/benchmark — Benchmark mode is CLI-only
- Runs list date-range filter — API list_runs has no date_from/date_to
- Run cancellation — No POST /api/runs/{id}/cancel

---

## 6. Async Runs / Execution Model Audit

### Run persistence

- **Mechanism:** JSON files in `runs/` directory, one file per run: `runs/{run_id}.json`
- **Evidence:** `run_store.py` create_run, get_run, update_run, list_runs
- **Redaction:** _redact_config redacts password, secret, token, credential in config_summary

### Run status model

- id, status (queued, running, succeeded, failed)
- created_at, started_at, finished_at, duration_seconds
- run_type, config, config_summary, selected_pack
- stage_progress (list of { name, status, started_at, finished_at, duration_seconds, message, metrics })
- warnings, error_message, result_summary, artifact_paths
- output_dir, output_run_id (output folder name)
- events (log entries: level, message, ts; capped at 200)

### Stage tracking

- STAGES: preflight, schema_load, rule_load, generation, anomaly_injection, etl_transforms, export, contract_generation, warehouse_load, validation, manifest, complete
- **Actual updates:** schema_load, rule_load, generation, export, complete are updated; others remain pending
- No granular updates for anomaly_injection, etl_transforms, contract_generation, warehouse_load, validation, manifest

### Event / log model

- append_event(level, message) adds to events list
- Level: info, error
- Capped at 200 events

### Rerun

- Reads config from record; creates new run; starts background task with same config
- Works; uses full config (including redacted fields — redacted values may break Snowflake/BigQuery if passed)

### Clone

- Returns config from record (or config_summary if config missing)
- config_summary is redacted; clone may return `***` for db_uri — prefill would have masked values

### Result summary structure

- selected_pack, total_tables, total_rows, duration_seconds, warnings, quality_summary
- output_dir, export_paths, artifact_run_id (output folder name)

### Artifact linkage

- artifact_run_id = output_dir folder name (e.g. run_abc123...)
- Run record id (e.g. run_xyz789...) is different; artifacts live in output/run_abc123/
- Run detail page links to artifacts using artifact_run_id correctly

### Failure handling

- On exception, status=failed, error_message set, stage_progress updated
- append_event(error, message)

### Background task behavior

- FastAPI BackgroundTasks; process runs in same process
- Server restart kills in-flight runs; no resume
- No queue; truly local-first

### Resilience limitations

- No persistence of in-flight state; restart = lost run
- No run cleanup; runs/ grows
- Clone returns redacted config when config_summary used as fallback

---

## 7. Frontend Architecture Audit

### App routes

| Route | Purpose | Depth |
|-------|---------|-------|
| / | Landing | Medium — capabilities, features, how it works |
| /create/wizard | Guided create | High — 5 steps, preflight, Run |
| /create/advanced | Expert config | High — 11 sections, export/import, Run |
| /validate | Validation center | High — schema, GE, reconcile tabs |
| /templates | Pack list | Medium — cards, API-driven |
| /templates/[id] | Pack detail | Medium — tables, relationships, CTAs |
| /schema | Schema visualizer | High — React Flow, pack selector |
| /runs | Run list | Medium — status badges, no filters |
| /runs/[id] | Run detail | High — status, stages, config, rerun/clone |
| /artifacts | Artifact explorer | High — filter, preview, download |
| /integrations | Integrations list | Low — static cards |
| /docs | Glossary, quick start | Low — static |

### Shared layout

- `AppShell` wraps all pages: TopNav + main content
- TopNav: Home, Create, Advanced, Validate, Templates, Schema, Runs, Artifacts, Integrations, Docs
- No sidebar; flat navigation

### Components

- `AppShell`, `TopNav`
- `ui/Button`, `ui/Card` (simple, no shadcn/ui beyond basics)
- Schema page: custom TableNode for React Flow

### State management

- `wizardStore` (Zustand): config, setConfig, reset
- No runsStore; run pages use local state and API calls
- Wizard and Advanced both call startRunGenerate directly

### API integration

- `lib/api.ts`: fetchPacks, fetchPack, runGenerate, runPreflight, startRunGenerate, fetchRuns, fetchRunDetail, fetchRunStatus, rerunRun, cloneRunConfig, runValidate, runValidateGe, runReconcile, fetchArtifacts, fetchSchemaVisualization
- API_BASE from NEXT_PUBLIC_API_URL or localhost:8000

### Page-by-page assessment

| Page | Implemented | Shallow / placeholder | Gaps |
|------|-------------|------------------------|------|
| Home | Capabilities, features, CTAs | Static content | No live stats |
| Wizard | Pack choice, use case, realism, export, preflight, Run | Use case presets are fixed | No schema upload path |
| Advanced | Full config, preflight, Run, export/import | Clone prefill not implemented | No ?clone= handling |
| Validate | 3 tabs, path inputs, Run, JSON result | Paths are manual | No run selector for paths |
| Templates | Pack list from API | Cards are simple | Pack metadata underused |
| Template detail | Tables, relationships, CTAs | "All Data Forge features" is generic | Use pack-specific supported_features |
| Schema | React Flow, pack select, search | Good | Minor polish |
| Runs list | Status badges, links | No filters | Add status, pack, run_type filters |
| Run detail | Status, stages, config, rerun, clone, artifacts link | Logs not shown | Add events/logs section |
| Artifacts | Run filter, category, search, preview, download | Good | Link to run uses artifact_run_id correctly |
| Integrations | Static cards | No links to docs | Shallow |
| Docs | Glossary, quick start | No search | Shallow |

---

## 8. UI/UX / Design / Styling Audit

### Visual quality

- **Framework:** Tailwind; `cn()` for class merging
- **Font:** Inter via Next.js
- **Palette:** Slate grays, green/red/amber for status
- **Consistency:** Card, Button reused; layout is consistent
- **Polish:** MVP; no animations, no loading skeletons beyond animate-pulse

### Spacing and hierarchy

- Adequate padding; section spacing clear
- Headings: text-2xl for page titles; text-sm for labels

### Usability

- **Non-technical:** Wizard is approachable; use case presets help
- **Technical:** Advanced config and Validate require path knowledge
- **Discoverability:** Nav is clear; no onboarding

### Wizard quality

- 5 steps, linear; Back/Next/Run
- Preflight on Review step; blockers block Run
- Pack selection shows tables_count
- Export step has dbt/GE/Airflow/contracts checkboxes — these are sent to API but API does not execute them

### Results / run detail

- Status, tables, rows, duration in cards
- Stage progress list
- Config summary, output dir
- Rerun, Clone, Artifacts buttons
- No logs/events display

### Schema visualizer

- React Flow with custom nodes
- Pack dropdown, search
- Side panel for column details
- Good for exploring schema

### Empty / loading / error states

- Loading: animate-pulse, "Loading…"
- Empty: "No runs yet", "No artifacts"
- Error: Red message, Retry where applicable

### Responsiveness

- Grid layouts use sm:grid-cols-2, lg:grid-cols-3/4
- Nav hidden on mobile (hidden md:flex)
- No dedicated mobile UX

### Accessibility

- Semantic HTML
- No explicit aria-* or keyboard handling documented

### Design debt

- Integrations and Docs are static; could be driven by API or config
- Template detail "All Data Forge features" ignores pack-specific supported_features
- Run logs exist in API but are not shown

---

## 9. Frontend/Backend Alignment Audit

### Backend features exposed well in UI

- Domain packs (list, detail, schema viz)
- Async run start, status polling, run detail
- Preflight
- Validation (schema, GE, reconcile)
- Artifacts (list, filter, preview, download)
- Export format, load target, mode, layer, messiness

### Backend features partially exposed

- **dbt/GE/Airflow/contracts:** Checkboxes in wizard/advanced; API ignores them — **misalignment**
- **Run logs:** API has /logs; UI does not show
- **Run filters:** API supports status, pack, run_type; UI has none

### Backend features not exposed

- Benchmark mode
- write_manifest
- Chunk size, batch size (in advanced but not wizard)

### UI features shallow vs backend

- Template detail shows generic "All Data Forge features" instead of pack supported_features
- Validation paths: user must type paths; no dropdown of runs/output dirs

### Mismatches

- **Critical:** export_dbt, export_ge, export_airflow, contracts sent in config but services.run_generate never calls them
- Clone prefill: redirects to /create/advanced?clone=... but advanced page does not read it

### Duplication / drift risks

- Wizard and Advanced both build config and call startRunGenerate; possible drift if one adds a field and the other does not
- Pack metadata in API vs static CAPABILITIES in template detail

---

## 10. Test Coverage Audit

### Backend tests

| Area | Tests | Coverage |
|------|-------|----------|
| API | 14 tests | Health, packs, generate, preflight, schema viz, artifacts, runs (async, detail, list), validate |
| Engine | 2 | run_generation, export_result |
| Schema ingest | 3+ | DDL parse, load |
| Rule engine | 4 | Order, range, table filter |
| Validators | 4 | Ref integrity, rule violations, load_dataset |
| Exporters | 5 | CSV, JSON, JSONL, Parquet, SQL |
| Anomaly | 4 | Null, malformed, empty |
| Adapters | 10+ | SQLite, DuckDB, Postgres, warehouse load |
| ETL | 15+ | CDC, incremental, layers, drift, messiness |
| GE/Airflow | 15+ | GE export/validation, Airflow, reconciliation |
| Cloud/dbt | 12+ | Snowflake/BigQuery, dbt, warehouse validation |
| Privacy/contracts | 10+ | PII, redaction, contract fixtures |
| Performance | 14+ | Chunking, benchmark, timings |
| Path security | 2 | ensure_path_allowed |

### Integration-style tests

- test_runs_generate_async, test_runs_detail: create run, fetch detail
- test_cli_generate_load_sqlite, test_cli_generate_with_export_ge: full CLI flows

### Missing tests

- Run store: no direct unit tests (tested indirectly via API)
- Task runner: no isolated tests
- Clone config: no test that clone returns usable config
- Frontend: no Jest/Vitest/Playwright tests
- API run cancellation: N/A (not implemented)

### Critical flows coverage

- Async run: create → poll → complete: covered by test_runs_detail
- Preflight → Run: covered by wizard flow (no automated E2E)
- Rerun: no dedicated test

---

## 11. Documentation / OSS Readiness Audit

### README

- **Quality:** Good. One-line pitch, features, quick start, CLI examples, db load, benchmark, dbt, GE, Airflow, reconcile, UI overview
- **API endpoints:** Listed
- **Project layout:** Diagram
- **Roadmap:** Phases 1–3

### docs/

- No `docs/` directory in repo (Docs page is in-app static content)

### CHANGELOG, CONTRIBUTING

- Not present

### Issue/PR templates

- Not present

### Architecture docs

- README project layout; no dedicated architecture doc

### Setup/run

- uv sync, uvicorn, npm run dev — clear
- Env vars for Snowflake/BigQuery documented

### OSS readiness

- README sufficient for first-time users
- Missing: CONTRIBUTING, changelog, code-of-conduct, issue templates

---

## 12. Code Quality / Maintainability Audit

### Strengths

- Clear separation: engine, services, routers
- Pydantic for request/response
- Typing used in Python
- Domain packs loaded from files; no hardcoding in UI

### Duplication

- Config building in wizard vs advanced; some overlap
- DEFAULT_CONFIG in advanced mirrors WizardConfig fields

### Dead code

- Sync POST /api/generate still present; frontend uses async only
- runsStore was removed; wizard/advanced use direct API

### Large files

- cli.py ~750 lines; many options
- engine.py ~270 lines; manageable

### Weak abstractions

- Row count logic in engine.py (L91–99) is table-name-based; brittle for new packs

### Naming

- Consistent: run_store, task_runner, run_generate

### TODOs

- None prominently left in critical paths

### Conventions

- Python: ruff, mypy in pyproject
- Frontend: TypeScript; no strict lint config visible

---

## 13. Security / Safety / Privacy Audit

### Secret handling

- run_store: _redact_config redacts password, secret, token, credential in config_summary
- services: _serialize_result redacts similar keys in result
- Clone uses config or config_summary; config_summary is redacted — clone may return masked values

### Logs/events

- append_event stores level, message, ts
- No automatic redaction of message content; callers should avoid logging secrets

### Path safety

- ensure_path_allowed blocks traversal
- Artifacts router resolves path and checks it is under output/run_id

### Privacy mode

- off, warn, strict
- Strict blocks if sensitive columns lack redaction
- PII detection in quality report

### Clone/config exposure

- config_summary is redacted; full config is stored for rerun
- Clone returns config (preferred) or config_summary; if only config_summary available, db_uri etc. are masked

---

## 14. Performance / Scalability Audit

### Chunking

- chunk_size in GenerationRequest; engine generates in chunks
- Preserves row counts; tested

### Benchmark mode

- CLI benchmark with iterations, JSON output
- No API equivalent

### Memory

- estimate_peak_memory_mb in preflight
- Chunking reduces peak for large scale

### Async model

- Single process; BackgroundTasks
- No horizontal scaling

### Warehouse

- Batch inserts (batch_size)
- Warehouse validation after load

---

## 15. What Is Fully Implemented

- Schema ingest (SQL, JSON, OpenAPI)
- Rule engine (order, range, sum, distributions)
- Table generation with FKs
- CDC, incremental, full snapshot
- Bronze/silver/gold layers
- Messiness, schema drift
- Anomaly injection
- Quality report (ref integrity, rules, privacy)
- Privacy/PII detection and redaction
- Export: CSV, JSON, JSONL, Parquet, SQL
- Database load: SQLite, DuckDB, Postgres, Snowflake, BigQuery
- Warehouse validation
- dbt export (CLI)
- GE export and validation (CLI)
- Airflow export (CLI)
- Reconciliation
- Benchmark (CLI)
- Contracts (CLI)
- 10 domain packs with schemas and rules
- API: domain packs, preflight, schema viz, validate, reconcile, artifacts
- Async runs: create, status, detail, rerun, clone
- Run persistence (JSON)
- Frontend: wizard, advanced, templates, schema, runs, run detail, artifacts, validate

---

## 16. What Is Partial / Thin / Placeholder

- **API generation path:** No dbt, GE, Airflow, contracts, manifest — only core generation + export
- **Stage tracking:** Only some stages updated (schema_load, rule_load, generation, export, complete)
- **Run detail:** No logs/events display
- **Runs list:** No filters
- **Clone prefill:** Redirect works; advanced page does not read ?clone=
- **Template detail:** Generic "All Data Forge features" instead of pack metadata
- **Integrations/Docs pages:** Static; not driven by backend
- **Row count logic:** Hardcoded table names; new packs may not scale correctly

---

## 17. What Is Missing

- API execution of dbt, GE, Airflow, contracts, manifest
- Run cancellation
- Run cleanup/retention
- Clone prefill on advanced config page
- Runs list filters (status, pack, run_type)
- Logs/events display on run detail
- Benchmark API/UI
- Run selector in Validation for paths
- CONTRIBUTING, CHANGELOG, issue templates
- Frontend tests
- Architecture doc

---

## 18. Highest-Priority Gaps

### P0

| Title | Why it matters | Where | Difficulty | Value |
|-------|----------------|-------|------------|-------|
| API generation ignores dbt/GE/Airflow/contracts | Users check these in wizard/advanced but nothing happens | services.py, task_runner | Medium | High — core promise broken |
| Clone prefill broken | Clone → advanced shows empty form | frontend create/advanced | Low | High — expected flow fails |

### P1

| Title | Why it matters | Where | Difficulty | Value |
|-------|----------------|-------|------------|-------|
| Run logs not shown | Events exist in API but user cannot see them | runs/[id]/page.tsx | Low | Medium |
| Runs list no filters | Hard to find specific runs | runs/page.tsx | Low | Medium |
| Template detail ignores pack metadata | supported_features, recommended_use_cases unused | templates/[id]/page.tsx | Low | Low–medium |

### P2

| Title | Why it matters | Where | Difficulty | Value |
|-------|----------------|-------|------------|-------|
| Run cancellation | Long runs cannot be stopped | task_runner, runs router | Medium | Medium |
| Run cleanup | runs/ grows indefinitely | run_store | Low | Low |
| Benchmark UI | Power users want benchmarks from UI | API + frontend | Medium | Low |
| Validation path picker | Manual paths are error-prone | validate page | Medium | Medium |

---

## 19. Recommended Next Milestones

### Milestone A: Fix API/UI integration gaps (P0)

**Scope:** Wire dbt/GE/Airflow/contracts into API services; fix clone prefill.

**Why now:** Highest user-visible breakage.

**Files:** `api/services.py`, `api/task_runner.py`, `frontend/src/app/create/advanced/page.tsx`

**Outcome:** Wizard/advanced dbt/GE/Airflow/contracts actually run; clone prefill works.

---

### Milestone B: Run UX improvements (P1)

**Scope:** Show run logs on run detail; add runs list filters.

**Why now:** Quick wins, high impact.

**Files:** `frontend/src/app/runs/[id]/page.tsx`, `frontend/src/app/runs/page.tsx`

**Outcome:** Users see events; can filter by status, pack.

---

### Milestone C: Template detail enrichment

**Scope:** Use pack key_entities, recommended_use_cases, supported_features in template detail.

**Why now:** Packs have metadata; UI should use it.

**Files:** `frontend/src/app/templates/[id]/page.tsx`

**Outcome:** Template pages reflect each pack’s strengths.

---

### Milestone D: Run cancellation + cleanup

**Scope:** Cancel endpoint (best-effort); optional run retention/cleanup.

**Why now:** Production hygiene.

**Files:** `api/task_runner.py`, `api/routers/runs.py`, `api/run_store.py`

**Outcome:** Users can cancel; old runs can be pruned.

---

### Milestone E: OSS polish

**Scope:** CONTRIBUTING.md, CHANGELOG.md, issue templates, docs/domain-packs.md.

**Why now:** Enables external contributors.

**Files:** New docs, .github/

**Outcome:** Repo ready for open-source release.

---

## 20. Brutally Honest Verdict

**What this repo is today:** A strong synthetic data engine with a functional but incomplete product layer. The backend can do almost everything; the API does a subset; the UI advertises more than it delivers (dbt/GE/Airflow/contracts). Async runs work and feel modern, but clone prefill is broken and run logs are hidden. The 10 domain packs are a real asset.

**How impressive it is:** The engine and CLI are genuinely impressive. The API and Next.js app are adequate for demos and internal use but not yet "production-grade" in the sense of full feature parity and polish.

**What prevents it from feeling complete:** (1) UI checkboxes that do nothing, (2) clone prefill broken, (3) no run logs in UI, (4) no run filters. Fixing these would close the largest gaps quickly.

**What would make it exceptional:** Full API support for dbt/GE/Airflow/contracts, run cancellation, validation path picker (run selector), benchmark UI, CONTRIBUTING/changelog, and frontend tests. That would make it a complete, credible platform.

---

## Appendices

### A. Machine-readable JSON summary

```json
{
  "backend_status": {
    "schema_ingest": "complete",
    "rule_engine": "complete",
    "generators": "complete",
    "anomaly_injection": "complete",
    "etl_realism": "complete",
    "validators": "complete",
    "privacy": "complete",
    "contracts": "complete_cli_only",
    "exporters": "complete",
    "dbt_export": "complete_cli_only",
    "ge_export": "complete_cli_only",
    "airflow_export": "complete_cli_only",
    "db_adapters": "complete",
    "warehouse_validation": "complete",
    "reconciliation": "complete",
    "benchmark": "complete_cli_only",
    "async_runs": "complete",
    "run_persistence": "complete"
  },
  "frontend_status": {
    "wizard": "complete",
    "advanced": "complete_partial_clone",
    "templates": "complete",
    "template_detail": "partial_metadata",
    "schema": "complete",
    "runs_list": "complete_no_filters",
    "run_detail": "complete_no_logs",
    "artifacts": "complete",
    "validate": "complete",
    "integrations": "placeholder",
    "docs": "placeholder"
  },
  "ui_ux_status": {
    "visual_quality": "mvp",
    "wizard": "good",
    "run_detail": "good",
    "schema_viz": "good",
    "empty_states": "present",
    "loading_states": "basic",
    "responsiveness": "partial"
  },
  "domain_packs": [
    "saas_billing",
    "ecommerce",
    "fintech_transactions",
    "healthcare_ops",
    "logistics_supply_chain",
    "adtech_analytics",
    "hr_workforce",
    "iot_telemetry",
    "social_platform",
    "payments_ledger"
  ],
  "api_status": {
    "domain_packs": "complete",
    "generate_sync": "legacy_unused",
    "runs_async": "complete",
    "preflight": "complete",
    "validate": "complete",
    "artifacts": "complete",
    "schema_viz": "complete",
    "run_logs": "implemented_unused"
  },
  "tests_status": {
    "backend": "good",
    "api": "good",
    "frontend": "none",
    "integration": "partial"
  },
  "docs_status": {
    "readme": "good",
    "contributing": "missing",
    "changelog": "missing",
    "architecture": "minimal"
  },
  "strengths": [
    "Rich generation pipeline",
    "10 domain packs",
    "Five database adapters",
    "Privacy/PII support",
    "Async run model",
    "Schema visualizer"
  ],
  "weaknesses": [
    "API ignores dbt/GE/Airflow/contracts",
    "Clone prefill broken",
    "Run logs not shown",
    "No run filters"
  ],
  "next_milestones": [
    "Wire dbt/GE/Airflow/contracts into API",
    "Fix clone prefill",
    "Show run logs",
    "Add runs list filters",
    "Run cancellation"
  ]
}
```

### B. Feature matrix

| Capability | Status |
|------------|--------|
| Schema ingest (SQL/JSON/OpenAPI) | Complete |
| Rule engine | Complete |
| Table generation + FKs | Complete |
| CDC/Incremental | Complete |
| Bronze/silver/gold | Complete |
| Messiness | Complete |
| Schema drift | Complete |
| Anomaly injection | Complete |
| Quality report | Complete |
| Privacy/PII | Complete |
| Export (CSV/JSON/Parquet/SQL) | Complete |
| dbt export | CLI only |
| GE export | CLI only |
| Airflow export | CLI only |
| Contracts | CLI only |
| Database load | Complete |
| Warehouse validation | Complete |
| Reconciliation | Complete |
| Benchmark | CLI only |
| Async runs | Complete |
| Run persistence | Complete |
| Run cancellation | Missing |
| Clone prefill | Placeholder (broken) |

### C. Route and endpoint inventory

| Route/Endpoint | Connected | Used | Notes |
|----------------|-----------|------|-------|
| GET / | — | Yes | Landing |
| GET /create/wizard | Yes | Yes | Wizard |
| GET /create/advanced | Yes | Yes | Advanced; clone param unused |
| GET /validate | Yes | Yes | Validate |
| GET /templates | Yes | Yes | Templates |
| GET /templates/[id] | Yes | Yes | Template detail |
| GET /schema | Yes | Yes | Schema viz |
| GET /runs | Yes | Yes | Runs list |
| GET /runs/[id] | Yes | Yes | Run detail |
| GET /artifacts | Yes | Yes | Artifacts |
| GET /integrations | — | Yes | Static |
| GET /docs | — | Yes | Static |
| GET /api/domain-packs | Yes | Yes | |
| GET /api/domain-packs/{id} | Yes | Yes | |
| POST /api/generate | Yes | No | Legacy sync |
| POST /api/runs/generate | Yes | Yes | |
| GET /api/runs | Yes | Yes | Filters unused in UI |
| GET /api/runs/{id} | Yes | Yes | |
| GET /api/runs/{id}/status | Yes | Yes | |
| GET /api/runs/{id}/logs | Yes | No | Not displayed |
| POST /api/runs/{id}/rerun | Yes | Yes | |
| POST /api/runs/{id}/clone | Yes | Yes | Prefill broken |
| POST /api/preflight | Yes | Yes | |
| GET /api/schema/visualize | Yes | Yes | |
| GET /api/artifacts | Yes | Yes | |
| GET /api/artifacts/file | Yes | Yes | |
| POST /api/validate | Yes | Yes | |
| POST /api/validate/ge | Yes | Yes | |
| POST /api/reconcile | Yes | Yes | |

### D. Screens/pages maturity

| Route | Maturity | Strengths | Gaps |
|-------|----------|-----------|------|
| / | Medium | Clear pitch, CTAs | Static |
| /create/wizard | High | Steps, preflight, Run | dbt/GE/contracts do nothing |
| /create/advanced | High | Full config, export/import | Clone prefill broken |
| /validate | High | 3 tabs, JSON result | Manual paths |
| /templates | Medium | API-driven cards | Simple layout |
| /templates/[id] | Medium | Tables, CTAs | Generic supported features |
| /schema | High | React Flow, search | — |
| /runs | Medium | Status, links | No filters |
| /runs/[id] | High | Stages, rerun, clone | No logs |
| /artifacts | High | Filter, preview, download | — |
| /integrations | Low | Static list | No depth |
| /docs | Low | Glossary | No search |

### E. Domain pack maturity

| Pack ID | Industry | Schema richness | Rule richness | UI exposure | Maturity |
|---------|----------|-----------------|---------------|-------------|----------|
| saas_billing | SaaS | High | High | Full | High |
| ecommerce | Retail | High | High | Full | High |
| fintech_transactions | Fintech | High | High | Full | High |
| healthcare_ops | Healthcare | High | Medium | Full | High |
| logistics_supply_chain | Logistics | High | High | Full | High |
| adtech_analytics | AdTech | High | Medium | Full | High |
| hr_workforce | HR | High | High | Full | High |
| iot_telemetry | IoT | High | Medium | Full | High |
| social_platform | Social | High | Low | Full | Medium |
| payments_ledger | Payments | High | High | Full | High |
