# Contributing to Data Forge

Thank you for your interest in contributing to Data Forge. This document covers how to run the project, run tests, and add new capabilities.

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

Open http://localhost:3000.

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

### Frontend build

```bash
cd frontend
npm run build
```

## Scenarios

Scenarios are reusable configurations. They can be saved from Advanced Config or created from a run.

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

2. Import via the UI: Scenarios → Import scenario → select your JSON file.

3. Or via API: `POST /api/scenarios/import` with the same payload.

## Adding a new domain pack

1. Add schema and rules under `schemas/` and `rules/`.
2. Register the pack in `src/data_forge/domain_packs/` (see existing packs for structure).
3. Add metadata (description, category, tables_count, supported_features).
4. For event streams: set `supports_event_streams` and `simulation_event_types`.
5. For benchmark relevance: set `benchmark_relevance` ("low" | "medium" | "high").

## Code style

- Backend: follow existing patterns; use type hints.
- Frontend: TypeScript, Tailwind CSS, existing component structure.
- Prefer incremental changes and backward compatibility.

## Submitting changes

1. Open an issue or discuss on a PR first for larger changes.
2. Keep PRs focused; avoid mixing unrelated fixes.
3. Ensure backend and frontend tests pass.
4. Update docs/README if behavior changes.
