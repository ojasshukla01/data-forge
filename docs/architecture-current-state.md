# Data Forge — Architecture Current State

This document summarizes the current repository structure, backend architecture, API surface, schema system, Custom Schema Studio, frontend routes, create flows, run lifecycle, testing, and CI workflow.

---

## Repository Structure

```text
data-forge/
├── src/data_forge/           # Python backend
├── frontend/                 # Next.js 16 + React 19 + TypeScript
├── tests/                    # Pytest backend tests
├── frontend/e2e/             # Playwright E2E tests
├── docs/                     # Documentation
├── custom_schemas/           # User-defined schemas (JSON files)
├── scenarios/                # Scenario JSON files (file backend)
├── output/                   # Run artifacts
├── schemas/                  # Domain pack schemas
├── rules/                    # Domain pack rules
├── pyproject.toml
├── frontend/package.json
└── .github/workflows/ci.yml
```

---

## Backend Architecture

### Modules Under `src/data_forge/`

| Module   | Purpose   |
| -------- | --------- |
| **api/** | FastAPI app, routers, services, task_runner, custom_schema_store |
| **models/** | SchemaModel, config_schema (RunConfig), generation, run_manifest, rules |
| **engine/** | `run_generation`, `export_result` — core synthetic data generation |
| **schema_ingest/** | Load schema from SQL DDL, JSON Schema, OpenAPI; `load_schema()` |
| **rule_engine/** | YAML/JSON rule sets; `load_rule_set()` |
| **domain_packs/** | Pre-built packs (saas_billing, ecommerce, fintech_transactions, etc.); `get_pack()`, `list_packs()` |
| **storage/** | RunStoreInterface, ScenarioStoreInterface; file_backend, sqlite_backend |
| **services/** | `run_generate`, retention_service, metrics_service, lineage_service; orchestration layer |
| **simulation/** | Event streams, time patterns, pipeline simulation |
| **config.py** | Settings (pydantic-settings), path validation (`ensure_path_allowed`) |
| **cli.py** | Typer CLI: generate, benchmark, validate, runs, scaffold-pack |

### Storage Abstraction

- **Factory**: `get_run_store()`, `get_scenario_store()` in `storage/__init__.py`
- **Backends**: `file` (default) or `sqlite` via `DATA_FORGE_STORAGE_BACKEND`
- **File backend**: delegates to `data_forge.api.run_store` and `scenario_store` (JSON in `runs/`, `scenarios/`)
- **SQLite backend**: `sqlite_backend.py` with `runs` and `scenarios` tables

---

## API Surface

### Routers

| Prefix             | Module        | Key Endpoints |
| ------------------ | ------------- | ------------- |
| `/api/domain-packs` | domain_packs | `GET ""`, `GET /{pack_id}` |
| `/api` | generate | `POST /generate` (sync) |
| `/api` | preflight | `POST /preflight` |
| `/api` | validate | `POST /validate`, `POST /validate/ge` |
| `/api` | artifacts | `GET /artifacts` |
| `/api/schema` | schema_viz | `GET /visualize`, `POST /parse`, `POST /preview` |
| `/api/runs` | runs | `POST /generate`, `POST /benchmark`, `GET ""`, `GET /{id}`, `GET /{id}/logs`, `GET /{id}/timeline`, `GET /{id}/lineage`, `GET /{id}/manifest`, `POST /{id}/rerun`, `POST /{id}/clone`, storage/cleanup/archive/pin/delete |
| `/api/benchmark` | benchmark | `POST` (sync benchmark) |
| `/api/scenarios` | scenarios | `GET`, `POST`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `POST /{id}/run`, `GET /{id}/versions`, `GET /{id}/versions/{v}`, `GET /{id}/diff`, `POST /import`, `GET /{id}/export` |
| `/api/custom-schemas` | custom_schemas | `POST /validate`, `GET`, `POST`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `GET /{id}/versions`, `GET /{id}/versions/{v}`, `GET /{id}/diff` |
| `/health` | main | `GET` |

### CORS

- Allows `http://localhost:3000`, `http://127.0.0.1:3000`

---

## Schema System

### SchemaModel (`models/schema.py`)

- **DataType**: string, text, integer, bigint, float, decimal, boolean, date, datetime, timestamp, uuid, email, phone, url, json, enum, currency, percent
- **ColumnDef**: name, data_type, nullable, unique, primary_key, default, min/max_length, min/max_value, enum_values, pattern, check, generator_hint, generation_rule (rule_type, params), description, display_name
- **TableDef**: name, columns, primary_key, unique_constraints, description, row_estimate, order, tags
- **RelationshipDef**: name, from_table, from_columns, to_table, to_columns, cardinality, optional, on_delete
- **SchemaModel**: name, description, tables, relationships, source, source_type
- **Schema validation**: `SchemaModel.validate_schema()` returns list of structural errors (duplicate names, invalid refs)
- **Helpers**: `get_table()`, `get_relationships_from/to()`, `dependency_order()` (topological sort for generation)

### Schema Ingest

- **load_schema(path)**: Supports .sql (DDL), .json (JSON Schema/OpenAPI), .yaml/.yml
- **Path safety**: `ensure_path_allowed()` restricts to project_root, schemas, rules, output
- **Parsers**: `parse_sql_ddl`, `parse_json_schema`, OpenAPI extraction

### Config Schema (`models/config_schema.py`)

- **RunConfig** (versioned): generation, simulation, benchmark, privacy, export, load, runtime
- **Flattening**: `to_flat_dict()`, `from_flat_dict()` for engine/API compatibility
- **Legacy**: `normalize_legacy_config()` for flat configs

---

## Custom Schema Registry

### Store (`api/custom_schema_store.py`)

- **Location**: `custom_schemas/schema_<id>.json`
- **Operations**: create, get, update (versioned), delete, list
- **Versioning**: MAX_VERSIONS=50; each update appends to `versions[]`
- **Validation**: All schema bodies validated via `SchemaModel.model_validate()`

### API (`routers/custom_schemas.py`)

- CRUD and version/diff endpoints as listed above
- Request body: `{ name, description?, tags?, schema }` (schema = SchemaModel-compatible dict)
- Response models: CustomSchemaSummary, CustomSchemaDetail, CustomSchemaVersionsResponse

### Integration

- Advanced Config: Schema & Input section has Custom schema dropdown
- Wizard: config supports custom_schema_id; passed to runs
- Generate API: accepts custom_schema_id
- See `docs/schema-studio.md` for full documentation

---

## Frontend Routes

| Route           | Purpose            |
| --------------- | ------------------ |
| `/` | Home; first-run onboarding or recent activity |
| `/create/wizard` | Create Wizard (5 steps) |
| `/create/advanced` | Advanced Config (tabs for all sections) |
| `/scenarios` | Scenario list |
| `/scenarios/[id]` | Scenario detail; version history & diff |
| `/runs` | Run list with badges, storage, cleanup |
| `/runs/[id]` | Run detail; lineage, manifest, timeline, artifacts |
| `/artifacts` | Artifact browser |
| `/templates` | Domain packs list |
| `/templates/[id]` | Pack detail; "Use This Template" → wizard |
| `/schema` | Schema Visualizer (React Flow, pack-based) |
| `/schema/studio` | Custom Schema Studio (JSON editor) |
| `/docs` | In-app docs with TOC |
| `/about` | About page |
| `/validate` | Validation center |
| `/integrations` | Integrations |

### Navigation

- **Main nav**: Home, Create, Scenarios, Runs, Artifacts, Docs, About
- **More dropdown**: Advanced config, Templates, Schema Studio, Schema, Validate, Integrations

---

## Create Wizard Flow

1. **Choose Input**: Domain Pack or Custom Schema (or saved scenario list)
2. **Use Case**: Presets (Demo, Unit Test, Integration Test, ETL, Load)
3. **Realism**: Scale, messiness, mode, layer
4. **Export**: Format, dbt/GE/Airflow/contracts
5. **Review & Run**: Summary, preflight (auto), Run, Save as scenario

- Uses `wizardStore` (Zustand); `customSchemaId` or `pack` in config
- Maps to flat config for `/api/runs/generate` (includes `custom_schema_id`)
- Preflight runs automatically on Review step

---

## Advanced Config Flow

- Tabbed sections: Schema & Input, Rules, Generation, ETL Realism, Pipeline Simulation, Privacy, Contracts, Exports, Load, Validation, dbt/GE/Airflow, Benchmark, Raw Config
- Prefill from `?scenario=<id>` or `?clone=<json>`
- Preflight & Run panel; Save/Update/Save-as scenario; Import/Export JSON
- Full nested config editing (pipeline_simulation, benchmark, etc.)

---

## Run Generation Lifecycle

1. **Start**: `POST /api/runs/generate` → create run record, queue `execute_generation_async`
2. **Task runner** (`task_runner.py`): Normalizes config via `RunConfig.from_flat_dict()`; loads schema/rules; runs engine `run_generation`; exports; optionally pipeline simulation, benchmark, load, dbt/GE/Airflow; writes manifest
3. **Stages**: preflight → schema_load → rule_load → generation → anomaly_injection → etl_transforms → export → contract_generation → warehouse_load → validation → manifest → complete
4. **Output**: `output/<run_id>/` with datasets, manifest.json, manifest.md
5. **Polling**: Frontend polls `GET /api/runs/{id}` for status

### Manifest + Lineage

- **Manifest**: Built by `build_run_manifest`; written to `manifest.json` and `manifest.md` in output dir. Includes pack, seed, scale, mode, layer; custom_schema_id, custom_schema_version, schema_source_type (pack | custom_schema) when schema-driven.
- **Lineage**: `get_run_lineage()` → run → scenario → version → pack (or custom_schema_id/custom_schema_version) → artifact_run_id. Includes schema_source_type.
- **Manifest API**: `get_run_manifest_from_disk()` reads manifest.json from output dir
- **Run detail UI**: Config card (pack), Lineage card (pack, scenario), Reproducibility manifest card

---

## Testing Architecture

### Backend (pytest)

- **Location**: `tests/`
- **Examples**: `test_api.py`, `test_custom_schemas.py`
- **Client**: FastAPI TestClient against `data_forge.api.main:app`
- **Coverage**: API endpoints, custom schema CRUD/versions/diff

### Frontend (Vitest)

- **Location**: `frontend/src/**/*.test.tsx`
- **Stack**: Vitest, React Testing Library, jsdom
- **Pattern**: Mock `fetch`, `next/navigation` where needed
- **Coverage**: Pages (wizard, advanced, templates, schema studio), lib/utils

### E2E (Playwright)

- **Config**: `frontend/playwright.config.ts`; `testDir: ./e2e`
- **CI**: E2E job starts API + frontend, runs `npm run e2e` (continue-on-error: true)
- **Web server**: Starts `npm run dev` on port 3000 (reuse locally, fresh in CI)
- **Note**: CI in current state may not include Playwright (see CI section)

---

## CI Workflow

**File**: `.github/workflows/ci.yml`

### Backend Job

- Python 3.12
- `pip install -e ".[dev]"`
- `ruff check src tests`
- `mypy src` (continue-on-error)
- `pytest tests -v --tb=short`

### Frontend Job (if `frontend/package.json` exists)

- Node 20, npm cache
- `cd frontend && npm install`
- `npx tsc --noEmit`
- `npm test` (Vitest)
- `npm run build`

### E2E Job

- Starts API (uvicorn) and frontend (`npm run start`)
- `npx playwright test` (chromium)
- continue-on-error: true

---

## Environment and Config

- **Backend**: `DATA_FORGE_*` env vars; `.env` optional
- **Frontend**: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`)
- **`.env.example`**: Template for env vars; copy to `.env`
- **Secrets**: Snowflake, BigQuery credentials via env; sensitive config fields redacted in scenario store

---

## Dependencies

### Backend (pyproject.toml)

- Core: fastapi, uvicorn, pydantic, pydantic-settings, typer
- Data: polars, pyarrow, duckdb, faker, mimesis
- Integrations: great-expectations, psycopg, snowflake-connector-python, google-cloud-bigquery
- Dev: pytest, ruff, mypy, pre-commit

### Frontend (package.json)

- Next 16, React 19, TypeScript
- UI: tailwindcss, clsx, tailwind-merge, lucide-react, reactflow, recharts
- State: zustand
- Testing: vitest, @testing-library/react, @playwright/test
