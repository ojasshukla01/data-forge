# Testing

This document describes the test architecture, commands, and coverage for Data Forge.

---

## Overview

| Layer | Framework | Location | Command |
|-------|-----------|----------|---------|
| Backend | pytest | `tests/` | `uv run pytest tests -v` |
| Frontend | Vitest | `frontend/src/**/*.test.tsx` | `cd frontend && npm test` |
| E2E | Playwright | `frontend/e2e/` | `cd frontend && npm run e2e` |

---

## Backend Tests (pytest)

### Structure

```
tests/
├── test_api.py                    # API endpoints
├── test_custom_schemas.py         # Custom schema CRUD, validate, diff
├── test_run_manifest_lineage.py   # Manifest, lineage, provenance
├── test_custom_schema_generation_rules.py  # Column generation rules
├── test_generation_rule_execution.py
├── test_security.py               # Schema ID, path, body size
├── test_path_security.py
├── test_engine.py
├── test_schema_ingest.py
├── test_rule_engine.py
├── test_exporters.py
├── test_adapters.py
├── test_validators.py
├── test_anomaly_injector.py
├── test_cli.py
└── test_*_milestone.py            # Feature milestones
```

### Running

```bash
# Quick
uv run pytest -q

# Verbose
uv run pytest -v

# With coverage
uv run pytest --cov=src/data_forge --cov-report=term-missing
```

### Patterns

- **TestClient**: FastAPI TestClient against `data_forge.api.main:app`
- **Fixtures**: Temp dirs, mock data
- **Async**: `pytest-asyncio` with `asyncio_mode = "auto"`

---

## Frontend Tests (Vitest)

### Structure

- **Page tests**: `page.test.tsx` for routes (home, wizard, advanced, templates, schema/studio, docs, about, artifacts)
- **Component tests**: e.g. `PipelineFlowGraph.test.tsx`

### Running

```bash
cd frontend
npm test           # Run once
npm run test:watch # Watch mode
```

### Stack

- Vitest
- React Testing Library
- jsdom
- Mocking: `fetch`, `next/navigation`

---

## E2E Tests (Playwright)

### Structure

```
frontend/e2e/
└── smoke.spec.ts  # Homepage load, Create wizard load
```

### Running

```bash
cd frontend
npx playwright install --with-deps    # First time: install browsers
npm run e2e
```

### Config

- **File**: `frontend/playwright.config.ts`
- **Test dir**: `./e2e`
- **Browser**: Chromium
- **baseURL**: `http://127.0.0.1:3000`
- **CI**: No webServer (API and frontend started separately); retries: 2

### Golden Path

`frontend/e2e/golden-path.spec.ts` covers the full custom-schema flow:

- Open Schema Studio → New schema
- Add table, Validate, Save
- Create Wizard → Custom Schema → select schema
- Navigate to Review → Run
- Run detail: verify custom schema provenance

---

## Full Validation

```bash
make validate-all
```

Or:

```bash
ruff check src tests
uv run pytest tests -v
cd frontend && npx tsc --noEmit && npm test && npm run build
```

E2E is separate (requires running servers):

```bash
# Terminal 1
uv run uvicorn data_forge.api.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev

# Terminal 3
cd frontend && npm run e2e
```

---

## Test Counts (Approximate)

| Layer | Count |
|-------|-------|
| Backend (pytest) | ~222 |
| Frontend (Vitest) | ~25 |
| E2E (Playwright) | 2 smoke + 2 golden path (custom schema, pack) |
