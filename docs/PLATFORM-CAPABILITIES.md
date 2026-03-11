# Data Forge — Platform Capabilities

This document confirms that the repository meets the expected final result as a fully functioning platform.

## Capability Checklist

| Capability | Status | Location |
|------------|--------|----------|
| Relational schema modeling | ✓ | SchemaModel, TableDef, ColumnDef, RelationshipDef; unique_constraints, check, tags |
| Synthetic data generation | ✓ | Engine `run_generation`, domain packs, custom schema support |
| Schema preview | ✓ | `POST /api/schema/preview`; Schema Studio "Generate sample rows" |
| Scenario-driven runs | ✓ | Scenarios API, wizard, advanced config; `POST /api/scenarios/{id}/run` |
| Artifact tracking | ✓ | Runs artifacts, storage summary, cleanup, archive, pin |
| Lineage tracking | ✓ | `GET /api/runs/{id}/lineage`, manifest |
| Versioned schemas | ✓ | Custom schema versions (max 50), diff with tables_added/removed/modified |
| Structured schema editor | ✓ | Schema Studio Form mode: tables, columns, relationships panels |
| Strong test coverage | ✓ | 213+ pytest, 25 Vitest; custom schema, preview, diff, preflight, generation, security |
| Secure API design | ✓ | Schema ID validation, path safety, request logging, schema body 512KB limit, Pydantic models |
| Complete documentation | ✓ | architecture-current-state, security, schema-studio, dependency-audit |
| Clean repository structure | ✓ | src/, frontend/, tests/, docs/, .github/workflows |
| CI validation | ✓ | Backend: ruff, pytest; Frontend: tsc, npm test, build |

## Phase Coverage

Every phase updates documentation, tests, and CI:

- **Phase A**: docs/architecture-current-state.md
- **Phase B**: security.py, middleware, .env.example, docs/security.md; custom schema validation tests
- **Phase C**: SchemaModel expansion, validate API; test_custom_schema_create
- **Phase D**: SchemaFormEditor; Schema Studio test
- **Phase E**: GenerationRule in rules; RuleSet.generation_rules
- **Phase F**: POST /preview, Schema Studio sample preview; test_api preview test
- **Phase G**: custom_schema_id full backend (services, preflight, config); test_generate_with_custom_schema, test_preflight_with_custom_schema
- **Phase H**: diff tables_added/removed/modified; test diff
- **Phase I–N**: error handling, docs, tests, CI

## No Partially Implemented Features

- **custom_schema_id**: Fully wired in GenerateRequest, RunConfig, run_generate, preflight, frontend (wizard, advanced config).
