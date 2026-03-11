# Changelog

All notable changes to Data Forge are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). We use **Semantic Versioning** (major.minor.patch); see [docs/release-process.md](docs/release-process.md) for release steps.

## [Unreleased]

### Added

- **GitHub launch polish:** README upgrade (feature matrix, “Why Data Forge is different”, core workflows, project structure, quick links). Architecture docs and Mermaid diagrams (platform overview, generation pipeline, run/scenario/artifact, pipeline simulation, benchmark, frontend–backend API). Screenshot checklist and target filenames in `docs/screenshots/`. Demo walkthrough (`docs/demo-walkthrough.md`), use cases (`docs/use-cases.md`), release process (`docs/release-process.md`). Light UI polish on landing, runs, scenarios, compare, and templates for screenshot-readiness.
- CI/CD: GitHub Actions workflow (`.github/workflows/ci.yml`) for backend tests, frontend tests, type-check, and build on push/PR.
- Local validation: Makefile targets (`backend-test`, `frontend-test`, `frontend-typecheck`, `frontend-build`, `validate-all`) and `scripts/validate_all.ps1` / `validate_all.sh`.
- Demo: One-command demo via `make demo-data` or `scripts/run_demo.ps1` / `run_demo.sh` (standard generation, scenario-style run, benchmark).
- Example scenarios in `examples/scenarios/` (ecommerce quick start, saas billing benchmark, fintech pipeline).
- Issue/PR templates: bug report, feature request, pull request template.
- Repo health: CODE_OF_CONDUCT.md, SECURITY.md, .editorconfig.

## [0.1.0] — Scenario lifecycle & release hardening

### Added

- Scenario lifecycle UX: save, update, save-as-new from Advanced Config and Create Wizard; edit metadata (name, description, category, tags) on scenario detail page.
- Lifecycle signals: `updated_at`, `created_from_scenario_id` when saving as new; run list and scenario detail show “from scenario” / “runs from this scenario”.
- Run comparison: raw JSON diff section and clearer headings on compare page.
- Backend: scenario metadata update, empty name rejection, `created_from_scenario_id`, list runs by `source_scenario_id`.
- Frontend tests for scenario detail, run detail, artifacts, scenarios list, compare page.
- CONTRIBUTING: validation sequence, EPERM note, scenario lifecycle and add-scenario instructions.

## Earlier

- Schema-aware synthetic generation, SQL/JSON Schema/OpenAPI ingest, YAML rule engine, relational/FK generation, anomaly injection.
- ETL realism: full snapshot, incremental, CDC, bronze/silver/gold, schema drift, messiness profiles.
- Privacy detection and redaction, contract fixtures, dbt/GE/Airflow export, reconciliation, benchmark mode.
- Async local run system, artifact registry, pipeline simulation, event streams, scenario persistence and API, run comparison API.
