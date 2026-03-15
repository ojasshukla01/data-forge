# Data Forge — Gap Analysis and Next Phase (Release-Prep)

This document lists the current platform state, remaining gaps relevant to release-prep, and what will **not** be done in this pass.

---

## Current Platform State (Verified)

### Backend

- FastAPI app, routers, services, task runner, run_store, scenario_store, custom_schema_store
- RunConfig / GenerationConfig with `custom_schema_id`; manifest and lineage with provenance (schema_missing, snapshot hash when custom schema deleted)
- Custom schema: CRUD, versions, diff, validate, preview, restore version as new revision
- Generation rules: faker, uuid, sequence, range, static, weighted_choice, null_probability; column-level generation_rule
- Security: request logging, body size limit (2MB), schema limits, schema ID validation, path safety, metadata sanitization, in-memory rate limiting; structured 413/429
- Domain packs, simulation, benchmark, preflight; engine in `engine.py`

### Frontend

- Next.js app: Home, About, Docs, Create Wizard, Advanced Config, Templates, Runs, Scenarios, Artifacts, Schema Studio, Validate
- Schema Studio: form + JSON mode, validation (errors + warnings), preview, version history, diff, duplicate, restore
- Wizard: Domain Pack or Custom Schema source; run detail shows lineage, manifest, custom schema provenance
- Scenarios: API and UI

### Tests and CI

- Pytest (backend), Vitest (frontend), Playwright E2E; strict gates in CI
- Ruff, mypy, tsc, build in CI
- Makefile: validate-all, backend-check, frontend-check, e2e, demo-data

### Docs

- architecture-current-state, api-reference, testing, ci-cd, security, schema-studio, lineage-and-reproducibility, create-and-config, demo-walkthrough
- release-checklist, release-process
- INDEX.md as docs hub

---

## Remaining Gaps (Release-Prep Scope)

| Gap | Priority | Notes |
|-----|----------|-------|
| CHANGELOG discipline | High | Ensure Keep a Changelog style; link from README |
| Versioning guidance | High | docs/versioning.md; tag format, bump rules |
| GitHub release workflow | High | release.yml on v* tags; CHANGELOG-driven notes |
| README polish | High | Open-source feel; badges; docs map; known limitations |
| Issue/PR templates | Medium | Add documentation_issue; verify existing |
| License file | Medium | Add LICENSE (MIT) if missing |
| Docs hub alignment | Medium | Versioning, release workflow cross-links |
| Website content alignment | Medium | In-app copy matches released product |

---

## What Will NOT Be Done in This Pass

- New product features (beyond release polish)
- Schema Studio ERD or drag-and-drop
- Run cancellation
- Run cleanup/retention automation
- Distributed rate limiting
- Production deployment automation
- Cloud/container packaging

---

## Release-Readiness Checklist (This Pass)

- [ ] CHANGELOG.md in Keep a Changelog style
- [ ] docs/versioning.md created and linked
- [ ] .github/workflows/release.yml on v* tags
- [ ] README polished; badges; docs map
- [ ] LICENSE file present
- [ ] Issue/PR templates complete
- [ ] docs/INDEX.md includes versioning and release
- [ ] Website/in-app copy aligned with product
- [ ] Full validation passes
