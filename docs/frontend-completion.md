# Frontend completion: scenario history, lineage, and UX

This document describes the in-app UI for scenario versioning, run lineage, reproducibility manifest, and related UX added to complete the platform experience.

## Scenario history and diff (scenario detail page)

- **Version history** card lists all config versions with version number and timestamp. Current version is marked.
- **Compare versions**: Choose left and right versions from dropdowns and click "Show diff". A human-readable diff shows changed config keys with old value (red) and new value (green).
- Empty state when no versions yet; loading and error states are handled.
- APIs used: `GET /api/scenarios/{id}/versions`, `GET /api/scenarios/{id}/diff?left=&right=`.

## Lineage and manifest (run detail page)

- **Lineage** card shows run → scenario (with link) → version → pack → artifact run ID and output dir. Shown when lineage is available; graceful message when not.
- **Reproducibility manifest** card shows seed, config schema version, pack, scale, storage backend, git commit SHA (if present), duration, rows generated, created timestamp. Shown when manifest is available (e.g. after run completion and manifest written to disk); graceful message when not.
- APIs used: `GET /api/runs/{id}/lineage`, `GET /api/runs/{id}/manifest`. Timeline is also fetched for "Why slow?" hint.

## Run-type badges and status

- **Runs list**: Each run shows status badge, pinned indicator, archived badge, and run-type badge (Standard / Simulation / Benchmark). Simulation = generate run with pipeline_simulation enabled; Benchmark = run_type benchmark.
- **Run detail**: Same run-type badges and pinned/archived in the header. "Why slow?" is shown prominently when timeline provides a hint or for benchmark runs with duration.

## First-run onboarding (home page)

- When there are no runs and no scenarios, a **Get started** section appears with: Start from template, Start from example scenario, Create new scenario, Import scenario config, and a short guided workflow (choose pack → configure → preflight → run → inspect artifacts → save scenario).
- When there are runs or scenarios, **Recent activity** shows recent runs and recent scenarios with links.

## Home, about, and docs

- **Home**: Hero, quick actions, first-run onboarding or recent activity, core capabilities, concepts (Run, Scenario, Artifact, Pack, Manifest & lineage), example use cases.
- **About**: Mission, concepts, local-first, extensibility, observability and lineage summary (with link to docs), how it works, creator card, open source links.
- **Docs**: "Docs by category" index (Getting started, Architecture, Operations, API, Pack authoring, Observability & lineage); Quick start; Understanding runs (including lineage and manifest); Scenario lifecycle (including version history & diff); API reference with Swagger/ReDoc links.

## API client additions

The frontend `lib/api.ts` now includes:

- `fetchScenarioVersions`, `fetchScenarioVersionConfig`, `fetchScenarioDiff` and types `ScenarioVersionsResponse`, `ScenarioDiffResponse`, etc.
- `fetchRunLineage`, `fetchRunManifest` and types `RunLineage`, `RunManifest`.

All existing API contracts remain backward compatible.

## UX and layout (latest)

- **No nested links**: Runs list cards use a div wrapper; run ID and "From scenario" are separate links to avoid `<a>` inside `<a>` (hydration error).
- **Navigation**: Main nav (Home, Create, Scenarios, Runs, Artifacts, Docs, About) plus "More" dropdown (Advanced config, Templates, Validate, Schema, Integrations). On mobile, all items appear in one list.
- **Home**: Single hero, two primary CTAs, compact first-run or recent-activity section, one Capabilities block. No duplicate sections.
- **Docs**: In-page index ("On this page") with anchor links; section ids for deep linking; shorter headings; scroll-mt for anchor offset.
- **Scenarios**: List deduplicated by scenario id when fetching.
