# CI/CD and Quality Gates

This document describes the CI workflow, quality gates, and validation commands for Data Forge.

---

## CI Workflow

**File**: `.github/workflows/ci.yml`

### Triggers

- Push and pull requests to `main` and `master`

### Jobs

| Job | Purpose | Strict Gates | Optional (continue-on-error) |
|-----|---------|--------------|------------------------------|
| **backend** | Ruff, mypy, pytest | ruff, pytest | mypy, pip-audit |
| **frontend** | Typecheck, Vitest, build | tsc, npm test, npm run build | npm audit |
| **e2e** | Playwright E2E | — | Playwright |

### Backend Steps

1. Checkout
2. Set up Python 3.12
3. Install: `pip install -e ".[dev]"`
4. **Ruff**: `ruff check src tests` — strict
5. **Mypy**: `mypy src` — continue-on-error
6. **Pytest**: `pytest tests -v --tb=short` — strict
7. **pip-audit**: `pip install pip-audit && pip-audit --desc` — continue-on-error

### Frontend Steps

1. Checkout
2. Set up Node 20
3. Install: `cd frontend && npm install`
4. **Typecheck**: `npx tsc --noEmit` — strict
5. **Vitest**: `npm test` — strict
6. **Build**: `npm run build` — strict
7. **npm audit**: `npm audit --audit-level=moderate` — continue-on-error

### E2E Steps

1. Checkout, install backend and frontend
2. `npx playwright install --with-deps chromium`
3. Build frontend
4. Start API: `uvicorn data_forge.api.main:app --host 127.0.0.1 --port 8000`
5. Start frontend: `npm run start`
6. Wait for servers
7. **Playwright**: `npm run e2e` — continue-on-error

---

## Local Validation Commands

### Full validation (Makefile)

```bash
make validate-all
```

Runs: ruff, pytest, frontend tsc + test + build.

### Backend only

```bash
make backend-check
# or:
ruff check src tests
uv run pytest tests -v
```

### Frontend only

```bash
make frontend-check
# or:
cd frontend && npx tsc --noEmit && npm test && npm run build
```

### E2E

```bash
make e2e
# or:
cd frontend && npm run e2e
```

Requires API and frontend running (or Playwright webServer config for local dev).

### Scripts

- **Windows**: `scripts/validate_all.ps1`
- **Unix**: `scripts/validate_all.sh`

---

## Quality Gate Status

| Gate | CI | Blocking |
|------|-----|----------|
| Ruff | Yes | Yes |
| Pytest | Yes | Yes |
| Mypy | Yes | No (continue-on-error) |
| pip-audit | Yes | No |
| Frontend tsc | Yes | Yes |
| Vitest | Yes | Yes |
| Frontend build | Yes | Yes |
| npm audit | Yes | No |
| Playwright | Yes | No |

---

## Known Limitations

1. **Mypy**: ~166 type errors across 34 files (dict type params, no-any-return, Callable, pyarrow imports, Typer path_type). CI uses continue-on-error. Blockers: extensive router/service/store annotations; Typer CLI path_type compatibility; pyarrow lacks stubs.
2. **Playwright**: E2E can be flaky; CI does not fail. Golden path exists. Goal: stabilize and make strict when feasible.
3. **pip-audit / npm audit**: Optional; high/critical findings should be addressed manually.

---

## Improving CI

To make mypy or Playwright strict:

1. Fix underlying issues (typing, flakiness)
2. Remove `continue-on-error: true` from the step
3. Update this document
