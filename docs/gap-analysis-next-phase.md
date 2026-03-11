# Data Forge — Gap Analysis and Next Phase Plan

This document lists what already exists, what remains incomplete, what this implementation pass will change, and risks/compatibility constraints.

---

## What Already Exists (Baseline)

### Backend

- FastAPI app, routers, services, task runner
- RunConfig / GenerationConfig with `custom_schema_id`
- Custom schema store (CRUD, versions, diff, validate, preview)
- Run generation via pack, custom_schema_id, schema_path, or schema_text
- Manifest: `build_run_manifest()` writes pack, custom_schema_id, custom_schema_version, schema_source_type
- Lineage: `get_run_lineage()` returns pack, custom_schema_id, custom_schema_version, schema_source_type
- Rule engine: faker, uuid, sequence, range, static, weighted_choice
- Generation engine with column-level generation_rule support
- Schema validation, preview, preflight APIs
- Security middleware: request logging, size limits, schema ID validation, path safety, metadata sanitization
- Domain packs, simulation (event streams), benchmark

### Frontend

- Create Wizard with pack/custom schema source
- Advanced Config with custom schema dropdown
- Schema Studio: form mode, JSON mode, validation, preview, version history, diff, duplicate schema
- Run detail: Config, Lineage, Manifest cards show custom schema provenance when used
- Templates, Scenarios, Runs, Artifacts, Validate, Integrations

### Tests

- ~222 pytest backend tests
- ~25 Vitest frontend tests
- Playwright smoke tests (homepage, create wizard load)

### CI

- Backend: ruff (strict), mypy (continue-on-error), pytest (strict), pip-audit (continue-on-error)
- Frontend: tsc (strict), Vitest (strict), build (strict), npm audit (continue-on-error)
- E2E: Playwright (continue-on-error)

### Docs

- architecture-current-state.md, gap-analysis-next-phase.md
- schema-studio.md, generation-engine.md, create-and-config.md
- lineage-and-reproducibility.md, security.md, api-reference.md
- dependency-audit.md, PLATFORM-CAPABILITIES.md, repository-cleanup-summary.md
- ci-cd.md, testing.md exist

---

## Gaps This Implementation Pass Addresses

### High Priority

| Gap | Status | Planned Action |
|-----|--------|----------------|
| Mypy not strict gate | Open | Fix pyproject config; fix typing where feasible; document blockers (166 errors across 34 files) |
| Playwright E2E not strict | Open | Stabilize golden path; add robustness; consider strict gate |
| Golden path exists | Done | golden-path.spec.ts: Schema Studio → save → wizard → run → provenance |
| Docs/website content lag | Open | Align all pages and docs with implementation |
| api-reference.md | Done | Health, Schema, Generation, Runs, Scenarios |
| ci-cd.md | Done | CI steps, local commands, quality gates |
| testing.md | Done | pytest, Vitest, Playwright structure and commands |

### Medium Priority

| Gap | Status | Planned Action |
|-----|--------|----------------|
| Schema Studio: unique_constraints not in form | Open | Add form editing or document JSON-only |
| Schema Studio: check constraints not in form | Open | Add form editing or document JSON-only |
| Validation UX: warnings vs errors | Open | Improve validation summary; distinguish if API supports |
| No restore-to-new-version in Schema Studio | Open | Add flow if feasible (non-destructive) |
| Preflight messaging generic | Open | Make failure messages actionable; guide to Schema Studio when schema missing |
| Terminology drift | Open | Line-by-line alignment across pages |

### Additional Hardening

| Gap | Status | Planned Action |
|-----|--------|----------------|
| Real rate limiting | Open | Add or document in security.md |
| Dependency audit not strict | Open | Document; consider stricter governance |
| Conservative cleanup | Open | Safe dead-code and unused-import cleanup |
| Test warnings/shallow coverage | Open | Fix warnings; expand critical-path coverage |

---

## What This Implementation Pass Will Change

| Phase | Area | Planned Changes |
|-------|------|-----------------|
| 1 | Docs | architecture-current-state.md, gap-analysis-next-phase.md (done) |
| 2 | CI / typing | Fix mypy; improve CI strictness; create ci-cd.md |
| 3 | E2E | Playwright golden path; stabilize; document |
| 4 | Schema Studio | unique_constraints/check form support; validation UX; restore flow; preview polish |
| 5 | Wizard/Advanced | Review step schema source; preflight guidance; cross-flow links |
| 6 | Provenance | Lineage/Manifest UI polish; run detail clarity |
| 7 | Security | Payload checks; rate limiting or doc; security tests |
| 8 | Rule engine | Optional: null_probability, date range; only if clean |
| 9 | Dependencies | Audit alignment; command/script hygiene |
| 10 | Website content | Line-by-line alignment of all pages |
| 11 | Cleanup | Dead code, unused imports; document in repository-cleanup-summary.md |
| 12 | Docs | api-reference, testing, schema-studio, create-and-config, etc. |
| 13 | Validation | Full pytest, ruff, mypy, Vitest, build, Playwright |

---

## Compatibility Constraints

1. **Backward compatibility**: Pack-based runs must continue to work. Manifest and lineage must not break existing consumers.
2. **API contracts**: Adding optional fields is safe; changing or removing fields is not.
3. **Frontend API types**: Older API responses without new fields must still render.
4. **Custom schema version**: Resolved at manifest build time; if schema deleted later, version in result_summary may be the only record.
5. **Local-first**: No database required for core operation.

---

## Test / Doc / CI / Security Risks

| Risk | Mitigation |
|------|------------|
| E2E continue-on-error | Fix flakiness; add golden path; document blockers if strict gate not feasible |
| Mypy continue-on-error | Fix errors; add types; document blockers |
| Docs drift | Update docs with every phase; review at end |
| pip/npm audit optional | Document; consider making strict for high/critical |
| Rate limiting placeholder | Document in security.md; add if feasible |

---

## Cleanup Opportunities

- Unused imports (ruff F401)
- Stale doc references
- Duplicate helper logic
- Dead components or routes
- Obsolete scripts

---

## Gaps Fully Solved vs Partially Improved

| Gap | Target |
|-----|--------|
| Mypy | Reduce failures substantially; strict gate if feasible |
| Playwright | Add golden path; stabilize; strict gate if feasible |
| Schema Studio form | unique_constraints/check: form or documented JSON-only |
| Validation UX | Improve summary; warnings/errors if API supports |
| Restore flow | Add if safe; else document as future |
| Preflight messaging | Actionable messages; Schema Studio links |
| Rate limiting | Add or document |
| ci-cd.md, testing.md | Create |
