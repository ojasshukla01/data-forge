# Documentation index

Use this page as the **canonical docs hub** for Data Forge.

---

## Start here (canonical docs)

These are the **current, authoritative** docs for users and contributors. Keep them up to date with the codebase.

| Doc | Purpose |
|-----|---------|
| [README](../README.md) | Product overview, quick start, docs map, known limitations |
| [Architecture (current state)](architecture-current-state.md) | Repository structure, API surface, schema system, frontend routes, CI/E2E |
| [API Reference](api-reference.md) | REST endpoints, request/response shapes, errors (413/429), lineage & manifest |
| [Testing](testing.md) | Backend (ruff, mypy, pytest), frontend (Vitest), E2E (Playwright), validation checklist, debugging |
| [CI/CD](ci-cd.md) | GitHub Actions workflow, strict gates, local parity, troubleshooting |
| [Security](security.md) | Schema limits, rate limiting, path safety, preview safety |
| [Schema Studio](schema-studio.md) | Custom schemas: form/JSON, validation, preview, version history, restore, duplicate |
| [Lineage & reproducibility](lineage-and-reproducibility.md) | Run lineage, manifest, custom schema provenance |
| [Create and config](create-and-config.md) | Create wizard, advanced config, config schema |
| [Demo walkthrough](demo-walkthrough.md) | Step-by-step UI walkthrough |
| [Release checklist](release-checklist.md) | Validation and sanity checks before a release (when present) |
| [Deployment](deployment.md) | Local Docker Compose, production env vars, cloud deployment guidance |
| [Adapter maturity](adapter-maturity.md) | Database load adapter audit: SQLite, DuckDB, Postgres, Snowflake, BigQuery |

### Other canonical docs

- [Generation engine](generation-engine.md) — Generation rules and engine behavior  
- [Rehearsal](rehearsal.md) — Migration rehearsal: schema evolution, drift, CDC, linked unstructured
- [Dependency audit](dependency-audit.md) — Dependency and audit notes  
- [Retention and cleanup](retention-and-cleanup.md)  
- [Scenario versioning](scenario-versioning.md)  
- [Pack authoring](pack-authoring.md)
- [Migration and upgrades](migration-and-upgrades.md) — Version upgrades, config/schema changes
- [Performance tuning](performance-tuning.md) — Scaling, benchmarks, limits
- [Repository cleanup summary](repository-cleanup-summary.md) — What was cleaned and left in place
- [Release process](release-process.md) — Release tagging, CHANGELOG, version bump
- [Versioning](versioning.md) — Semantic Versioning, tag format, bump rules
- [Environment variables](env.md) — Backend and frontend env vars
- [Observability and metrics](observability-and-metrics.md) — Prometheus, structured logging, run timeline
- [Use cases](use-cases.md) — Why Data Forge exists; pipeline testing, benchmarking, demos
- [Service layer](service-layer.md) — RunService, ScenarioService, storage abstraction

---

## Diagrams and assets

- [diagrams/](diagrams/) — frontend-backend-api, run-scenario-artifact, pipeline-simulation, benchmark-workflow, lineage-and-manifest, generation-pipeline  
- [screenshots/](screenshots/) — Screenshots and demo assets; [SCREENSHOT-CHECKLIST.md](screenshots/SCREENSHOT-CHECKLIST.md)

## Archived (historical)

- [archive/](archive/) — Historical planning docs (gap-analysis-next-phase, release-prep-plan)  

---

## Quick links for contributors

1. **New to the repo?** → [README](../README.md) → [architecture-current-state.md](architecture-current-state.md) → [testing.md](testing.md).  
2. **Running tests?** → [testing.md](testing.md) (final validation checklist) and [ci-cd.md](ci-cd.md).  
3. **Working on the API?** → [api-reference.md](api-reference.md) and [security.md](security.md).  
4. **Preparing a release?** → [release-process.md](release-process.md) and [release-checklist.md](release-checklist.md).  
