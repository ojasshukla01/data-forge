# Release checklist

Use this checklist before tagging a release or publishing release notes. Complete each item or document why it was skipped.

---

## 1. Validation commands (run from repo root)

- [ ] **Backend:** `uv run ruff check src tests` — no violations  
- [ ] **Backend:** `uv run mypy src` — no type errors  
- [ ] **Backend:** `uv run pytest tests -v --tb=short` — all pass  
- [ ] **Frontend:** `cd frontend && npx tsc --noEmit` — no type errors  
- [ ] **Frontend:** `cd frontend && npm run lint` — no lint errors  
- [ ] **Frontend:** `cd frontend && npm test -- --run` — all pass  
- [ ] **Frontend:** `cd frontend && npm run build` — build succeeds  
- [ ] **E2E:** Start API and frontend, then `cd frontend && npm run e2e` — all specs pass  

**Shortcut:** `make validate-all` (steps 1–7), then `make e2e` (step 8). See [testing.md](testing.md).

**Optional:** Run `uv lock` if `pyproject.toml` dependencies changed; commit `uv.lock` for reproducible installs. Run `python scripts/export_openapi.py` to refresh `docs/openapi.json`.

---

## 2. CI status

- [ ] GitHub Actions workflow (`.github/workflows/ci.yml`) is green for the release branch  
- [ ] No bypassed or ignored steps for quality (ruff, mypy, pytest, tsc, npm test, build, Playwright)  

---

## 3. Docs to verify

- [ ] [README](../README.md) — quick start, docs map, known limitations are current  
- [ ] [docs/api-reference.md](api-reference.md) — endpoints and error shapes match the API  
- [ ] [docs/testing.md](testing.md) — test layout and commands match CI and scripts  
- [ ] [docs/ci-cd.md](ci-cd.md) — workflow and troubleshooting are current  
- [ ] [docs/security.md](security.md) — limits and rate limiting described  
- [ ] [docs/INDEX.md](INDEX.md) — doc index is current  

---

## 4. Security review points

- [ ] No secrets or credentials in repo; `.env` in .gitignore  
- [ ] Schema ID validation and path safety documented and tested  
- [ ] Rate limiting and body size limits documented ([security.md](security.md))  
- [ ] Dependency audit: `uv pip audit` / `pip-audit` and `npm audit` run (optional in CI; run manually before release)  

---

## 5. Known limitations to mention in release notes

- **Local-first:** No built-in cloud deployment; API and frontend run locally or in CI.  
- **E2E:** Requires API and frontend running; start both before `make e2e`.  
- **Build:** On some environments (e.g. OneDrive-synced folders), `npm run build` may fail with EPERM; run from a non-synced path.  
- **Maturity:** Data Forge is open-source and actively developed; some integrations and adapters are evolving.  

See [README](../README.md#-known-limitations) and [release-prep-plan.md](release-prep-plan.md).

---

## 6. Manual UI checks (recommended)

- [ ] Create wizard: Domain Pack and Custom Schema paths work; run completes and appears in Runs  
- [ ] Schema Studio: Create schema, validate, save, use in wizard  
- [ ] Runs: List, filters, run detail (lineage, manifest, custom schema provenance)  
- [ ] Templates: List loads; template detail and “Use This Template” work  
- [ ] Advanced config: Key sections render; preflight and run work  

---

## 7. Versioning and changelog

- [ ] Version bumped in `pyproject.toml` and `src/data_forge/__init__.py` (and frontend `package.json` if applicable)  
- [ ] CHANGELOG.md: "Unreleased" items moved into `[X.Y.Z] - YYYY-MM-DD` for the release  
- [ ] Tag format: `vX.Y.Z` (e.g. `v0.1.0`). See [versioning.md](versioning.md).

---

*Update this checklist when the release process changes.*
