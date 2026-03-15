# Release checklist

Use this checklist before tagging a release or publishing release notes. Complete each item or document why it was skipped.

---

## 1. Validation commands (run from repo root)

- [ ] **Backend:** `uv run ruff check src tests` — no violations  
- [ ] **Backend:** `uv run mypy src` — no type errors  
- [ ] **Backend:** `uv run pytest tests -v --tb=short` — all pass (run with `-m "not slow"` for faster run if needed)  
- [ ] **Frontend:** `cd frontend && npx tsc --noEmit` — no type errors  
- [ ] **Frontend:** `cd frontend && npm test -- --run` — all pass  
- [ ] **Frontend:** `cd frontend && npm run build` — build succeeds  
- [ ] **E2E:** Start API and frontend, then `cd frontend && npm run e2e` — all specs pass  

**Shortcut:** `make validate-all` (steps 1–6), then `make e2e` (step 7). See [testing.md](testing.md).

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

- [ ] Version bumped in `pyproject.toml` (and any other version files) if doing a tagged release  
- [ ] CHANGELOG or release notes updated with user-facing changes and known limitations  
- [ ] Tag format consistent (e.g. `v0.2.0`)  

---

*Update this checklist when the release process changes.*
