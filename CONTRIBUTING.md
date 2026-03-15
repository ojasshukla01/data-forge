# Contributing to Data Forge

Thank you for your interest in contributing to Data Forge. This document covers how to run the project, run tests, and add new capabilities.

## Project structure

- **`src/data_forge/`** — Backend: models, schema ingest, rule engine, generators, adapters, exporters, domain packs, simulation, API (FastAPI).
- **`frontend/`** — Next.js product UI (Create wizard, Advanced config, Runs, Scenarios, Artifacts, etc.).
- **`schemas/`**, **`rules/`** — Optional local schema and rule files.
- **`examples/scenarios/`** — Example scenario JSON files for import.
- **`scripts/`** — `validate_all.ps1` / `validate_all.sh`, `run_demo.ps1` / `run_demo.sh`.
- **`.github/workflows/`** — CI (backend tests, frontend tests, type-check, build).

## Prerequisites

- **Python 3.10+** (uv recommended)
- **Node.js 18+** (for frontend)
- **npm** or **pnpm**

## Development setup

### Backend

```bash
# Install dependencies with uv
uv sync

# Run the API server
uv run uvicorn data_forge.api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Running tests

### Backend tests

```bash
uv run pytest -q
```

For verbose output:

```bash
uv run pytest -v
```

### Frontend tests

```bash
cd frontend
npm test
```

### Frontend E2E (Playwright)

```bash
cd frontend
npx playwright install --with-deps    # first time only
npm run e2e
```

### Frontend type-check

```bash
cd frontend
npx tsc --noEmit
```

### Frontend build

```bash
cd frontend
npm run build
```

### Frontend lint (optional)

```bash
cd frontend
npm run lint
```

**Build reliability (EPERM / file lock):** On some environments (e.g. OneDrive-synced folders or when another process holds files), the production build may fail with `EPERM` or "operation not permitted" when writing under `.next/`. That is usually an environment or file-lock issue, not a code bug. Run `npx tsc --noEmit` and `npm test` to verify code; if those pass, the codebase is valid. Retry build from a non-synced directory or after closing other tools that might lock the project folder.

## Code style and pre-commit (optional)

Install [pre-commit](https://pre-commit.com/) and run `pre-commit install`. On each commit, hooks run: **trailing-whitespace**, **end-of-file-fixer**, **ruff** (check + fix on `src` and `tests`), **mypy** (on `src`). This matches the CI backend checks. To run manually: `pre-commit run --all-files`. See [testing.md](docs/testing.md), [ci-cd.md](docs/ci-cd.md), and [versioning.md](docs/versioning.md) for full validation and release workflow.

## Full validation (same as CI)

Run the full suite locally before submitting:

**Using Make (from repo root):**

```bash
make validate-all
```

**Using scripts:**

```bash
# Windows (PowerShell)
./scripts/validate_all.ps1

# Linux/macOS
./scripts/validate_all.sh
```

**Manual sequence:**

1. Backend: `uv run ruff check src tests` then `uv run mypy src` then `uv run pytest -q` (or `python -m pytest -q`)
2. Frontend: `cd frontend && npm test`
3. Frontend types: `cd frontend && npx tsc --noEmit`
4. Frontend build: `cd frontend && npm run build` (see note above if it fails with EPERM)
5. Optional E2E: `cd frontend && npm run e2e` (requires Playwright browsers installed)

CI runs the same steps on every push and pull request. Do not submit with failing tests or type-check.

## Demo workflow

To generate sample outputs locally (no cloud credentials):

```bash
make demo-data
# or: ./scripts/run_demo.ps1   (Windows)   /   ./scripts/run_demo.sh   (Linux/macOS)
```

This produces a standard generation run, a scenario-style run, and a benchmark result under `demo_output/`. You can inspect outputs and use the Product UI (Runs, Artifacts) if the API and frontend are running.

Before submitting, run the **Full validation** steps above (e.g. `make validate-all`).

## Scenarios

Scenarios are reusable configurations. You can **save** from Advanced Config or the Create Wizard, **update** an existing scenario from Advanced Config (when loaded from a scenario), or **save as new** to create a copy without overwriting. Editing metadata (name, description, category, tags) is done on the scenario detail page via "Edit metadata."

### How to add a new scenario example

1. Create a JSON file in `examples/scenarios/` with this structure:

```json
{
  "name": "Human-readable name",
  "description": "Short description",
  "category": "quick_start|testing|pipeline_simulation|warehouse_benchmark|privacy_uat|contracts|custom",
  "tags": ["tag1", "tag2"],
  "config": {
    "pack": "ecommerce",
    "scale": 1000,
    "mode": "full_snapshot",
    "layer": "bronze",
    ...
  }
}
```

1. Import via the UI: Scenarios → Import scenario → select your JSON file.

2. Or via API: `POST /api/scenarios/import` with the same payload.

## Adding a frontend test

Frontend tests use Vitest and React Testing Library in `frontend/src`.

1. Add or edit a `*.test.tsx` file next to the component or page (e.g. `page.test.tsx` next to `page.tsx`).
2. Use `render`, `screen`, `userEvent` from `@testing-library/react`; mock `fetch` and `next/navigation` as needed.
3. Run: `cd frontend && npm test`. Test files are excluded from the main `tsconfig.json` so `npx tsc --noEmit` only type-checks app code.

## Artifacts, runs, and scenarios

- **Runs** are created by the API when you start a generation or benchmark from the UI or API. Run history is stored in the local JSON store (see API run_store).
- **Artifacts** are output files (datasets, event streams, dbt, GE, etc.) registered per run. Use the Artifacts page to filter by run or type.
- **Scenarios** are saved configs (name, category, tags, config blob). Load a scenario in the wizard or Advanced config to run or modify it; use "Save as new" to create a copy without overwriting.

## Adding a new domain pack

1. Add schema and rules under `schemas/` and `rules/`.
2. Register the pack in `src/data_forge/domain_packs/` (see existing packs for structure).
3. Add metadata (description, category, tables_count, supported_features).
4. For event streams: set `supports_event_streams` and `simulation_event_types`.
5. For benchmark relevance: set `benchmark_relevance` ("low" | "medium" | "high").

## Code style and quality gates

- **Backend**: type hints, Ruff (lint), mypy (type check). Run `make backend-check` (or `uv run ruff check src tests`, `uv run mypy src`, `uv run pytest`).
- **Frontend**: TypeScript, Tailwind CSS, existing component structure.
- CI runs: backend tests, Ruff, mypy, frontend tests, frontend typecheck, frontend build, and Playwright e2e. Fix lint and type errors before submitting.
- **Pre-commit**: Install hooks with `pre-commit install` (from repo root). This will run whitespace hygiene hooks, Ruff (with `--fix`), and mypy on changed Python files before each commit.
- Prefer incremental changes and backward compatibility.

## Submitting changes

1. Open an issue or discuss on a PR first for larger changes.
2. Keep PRs focused; avoid mixing unrelated fixes.
3. Ensure backend and frontend tests pass.
4. Update docs/README if behavior changes.
