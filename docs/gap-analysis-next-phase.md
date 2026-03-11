# Data Forge — Gap Analysis and Next Phase Plan

This document lists what already exists, what gaps remain, what this implementation pass will change, and risks/compatibility constraints.

---

## What Already Exists (Baseline)

### Backend
- FastAPI app, routers, services, task runner
- RunConfig / GenerationConfig with `custom_schema_id`
- Custom schema store (CRUD, versions, diff)
- Run generation via pack, custom_schema_id, schema_path, or schema_text
- Manifest: `build_run_manifest()` writes pack, custom_schema_id, custom_schema_version, schema_source_type
- Lineage: `get_run_lineage()` returns pack, custom_schema_id, custom_schema_version, schema_source_type
- Rule engine: faker, uuid, sequence, range, static
- Generation engine with column-level generation_rule support
- Schema validation, preview, preflight APIs
- Security middleware: request logging, size limits, schema ID validation

### Frontend
- Create Wizard with pack/custom schema source
- Advanced Config with custom schema dropdown
- Schema Studio: form mode, JSON mode, validation, preview, version history, diff
- Run detail: Config, Lineage, Manifest cards show custom schema provenance when used

### Tests
- ~205+ pytest backend tests
- Vitest frontend tests
- Playwright smoke tests

### CI
- Backend: ruff, mypy (continue-on-error), pytest
- Frontend: tsc, Vitest, build
- E2E: Playwright (continue-on-error)

---

## Gaps This Pass Will Address

### Phase 2 — Custom Schema Provenance (DONE)
Manifest, lineage, and run detail UI already include custom_schema_id, custom_schema_version, schema_source_type.

### Phase 2 (This Pass) — Schema Studio Maturity
- Table/column/relationship editing robustness
- Validation UX: field-level display, summary panel, warnings vs errors
- Version history UX: compare, diff readability, duplicate/copy
- Preview UX: table selector, row count, regenerate, error handling

### Phase 4 — Wizard / Advanced Config Alignment
- Custom schema source consistency across flows
- Preflight and review step clarity
- Schema Studio links and helper text

### Phase 5 — Generation Rules
- Validation rigor, error messages
- Optional new rules: weighted_choice, static, null_probability, date refinements

### Phase 6 — Security Hardening
- Structured error responses
- Schema preview payload safety
- Defensive validation in custom schema endpoints

### Phase 7 — Testing
- Custom schema generation flows, manifest/lineage provenance
- Wizard/advanced custom schema flows
- Playwright golden path including custom schema

### Phase 8 — CI, Type Safety
- Mypy: reduce failures, consider removing continue-on-error
- Dependency audit, script hygiene

### Phase 9 — Website Content
- Align all pages with custom schema flows and terminology

### Phase 10 — Repository Cleanup
- Dead code, unused imports, stale files

### Phase 11 — Documentation
- Update all docs to reflect implementation

---

## What This Implementation Pass Will Change

| Phase | Area | Planned Changes |
|-------|------|-----------------|
| 1 | Docs | architecture-current-state.md, gap-analysis-next-phase.md |
| 2 | Schema Studio | generation_rule form editing, table tags/display_name, validation summary, duplicate schema, preview/version UX |
| 3 | Wizard/Advanced | Review step schema source section, preflight guidance, cross-flow links |
| 4 | Generation rules | weighted_choice, null_probability; validation improvements |
| 5 | Provenance UX | Lineage/Manifest card polish, run detail clarity |
| 6 | Security | Payload checks, schema body limits, security tests |
| 7 | Testing | Vitest for run detail provenance; Playwright golden path; backend expansion |
| 8 | CI | Mypy fixes; pip/npm audit; validation scripts |
| 9 | Website content | Line-by-line alignment of all pages |
| 10 | Cleanup | Dead code, unused imports; document in repository-cleanup-summary.md |
| 11 | Docs | All docs updated to match implementation |
| 12 | Validation | Full pytest, ruff, mypy, Vitest, build, Playwright |

---

## Compatibility Constraints

1. **Backward compatibility**: Pack-based runs must continue to work. Manifest and lineage must not break existing consumers.
2. **API contracts**: Adding optional fields is safe; changing or removing fields is not.
3. **Frontend API types**: Older API responses without new fields must still render.
4. **Custom schema version**: Resolved at manifest build time; if schema deleted later, version in result_summary may be the only record.

---

## Test / Doc / CI / Security Risks

- **E2E**: continue-on-error means Playwright failures do not block CI; fix or document.
- **Mypy**: continue-on-error means type errors do not block; fix or document.
- **Docs drift**: Ensure docs/ matches code after each phase.
- **Security**: No pip/npm audit in CI; consider adding.

---

## Cleanup Opportunities

- Unused imports (ruff F401)
- Stale doc references
- Duplicate helper logic (none identified in baseline)
