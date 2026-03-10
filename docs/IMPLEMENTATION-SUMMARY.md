# Data Forge — implementation summary (product evolution)

This document summarizes the implementation delivered in one coordinated pass: frontend completion for existing backend capabilities, onboarding and UX polish, testing fixes, and documentation.

---

## 1. Architecture summary of what changed

- **Frontend–API wiring**: The existing backend already exposed scenario versioning (list versions, get version config, diff) and run lineage/manifest. The frontend now calls these APIs and renders the data.
- **No backend API changes**: All new behavior uses existing endpoints. No new routes, services, or storage logic were added.
- **Frontend**:
  - **Scenario detail**: Version history card (list versions, current version), compare selector (left/right), human-readable diff (key, old value, new value). Empty/loading/error handling; safe when `versions.versions` is missing.
  - **Run detail**: Lineage card (run → scenario → version → pack → artifacts), Reproducibility manifest card (seed, config version, pack, git SHA, etc.). Timeline used for prominent "Why slow?" hint. Run-type badges (Standard / Simulation / Benchmark) and pinned/archived in header.
  - **Runs list**: Run-type badges (Standard, Simulation, Benchmark) and archived indicator alongside existing status and pinned.
  - **Home**: Client-side fetch of recent runs and scenarios. First-run onboarding panel when no runs and no scenarios (quick start actions + guided workflow). Recent activity (recent runs, recent scenarios) when data exists. Concepts section (Run, Scenario, Artifact, Pack, Manifest & lineage).
  - **About**: New "Observability and lineage" section with link to docs.
  - **Docs**: "Docs by category" index; Understanding runs updated for lineage and manifest; Scenario lifecycle updated for version history & diff; API reference section unchanged.
- **Tests**: Scenario detail tests updated to mock `fetchScenarioVersions` and `fetchRuns` so version history UI does not throw. Docs test updated to use a specific query (heading) to avoid duplicate "Quick start" matches. All 16 frontend tests pass.
- **Docs**: New `docs/frontend-completion.md` (scenario history, lineage, manifest, run badges, onboarding, API client). New `docs/diagrams/lineage-and-manifest.md` (Mermaid diagram for lineage and manifest).

---

## 2. File-by-file summary

### Backend
- No backend files were modified. All features use existing APIs.

### Frontend
- **`frontend/src/lib/api.ts`** — Added types and functions: `ScenarioVersionInfo`, `ScenarioVersionsResponse`, `ScenarioVersionDetailResponse`, `ScenarioDiffChange`, `ScenarioDiffResponse`, `fetchScenarioVersions`, `fetchScenarioVersionConfig`, `fetchScenarioDiff`, `RunLineage`, `RunManifest`, `fetchRunLineage`, `fetchRunManifest`.
- **`frontend/src/app/scenarios/[id]/page.tsx`** — State and effect for versions; load diff on left/right change; Version history card with list, compare dropdowns, "Show diff", and diff result (key, old, new). Safe handling when `versions.versions` is undefined.
- **`frontend/src/app/runs/[id]/page.tsx`** — State and effect for lineage, manifest, timeline; Lineage card; Reproducibility manifest card; "Why slow?" callout; run-type badges and pinned/archived in header.
- **`frontend/src/app/runs/page.tsx`** — Run-type badges (Simulation, Standard) and consistent "Benchmark" label on runs list.
- **`frontend/src/app/page.tsx`** — Converted to client component; fetch recent runs and scenarios; first-run onboarding section; recent activity section; concepts section.
- **`frontend/src/app/about/page.tsx`** — "Observability and lineage" section with link to docs.
- **`frontend/src/app/docs/page.tsx`** — "Docs by category" section; Understanding runs bullet for lineage and manifest; Scenario lifecycle bullet for version history & diff.

### Tests
- **`frontend/src/app/scenarios/[id]/page.test.tsx`** — Mock `fetch` to return version response for `/versions` and runs list for `/api/runs` so component does not throw and tests can find "Test scenario" / "Test".
- **`frontend/src/app/docs/page.test.tsx`** — Assert "Docs by category" and use `getByRole("heading", { name: /Quick start/ })` instead of `getByText(/Quick start/)`.

### Docs
- **`docs/frontend-completion.md`** — New: describes scenario history/diff UI, lineage/manifest UI, run-type badges, first-run onboarding, home/about/docs updates, API client additions.
- **`docs/diagrams/lineage-and-manifest.md`** — New: Mermaid diagram and short description for lineage, manifest, scenario versioning.
- **`docs/IMPLEMENTATION-SUMMARY.md`** — This file.

### CI / dev tooling
- No changes. Existing CI (backend pytest, ruff, mypy; frontend typecheck, test, build) and Makefile targets remain valid.

---

## 3. Commands to run

| Action | Command |
|--------|--------|
| Backend tests | `python -m pytest tests -v --tb=short` or `uv run pytest tests -q` |
| Backend lint | `uv run ruff check src tests` or `make backend-lint` |
| Backend typecheck | `uv run python -m mypy src` or `make backend-typecheck` |
| Frontend install | `cd frontend && npm install` |
| Frontend tests | `cd frontend && npm test` (or `npm test -- --run`) |
| Frontend typecheck | `cd frontend && npx tsc --noEmit` |
| Frontend build | `cd frontend && npm run build` |
| Full validation | `make validate-all` (if available) or run backend tests + frontend tests + frontend build |

---

## 4. Assumptions

- Backend API base URL is `NEXT_PUBLIC_API_URL` or `http://localhost:8000`. Frontend is run with backend available for full lineage/manifest data.
- Scenario versions API returns `{ scenario_id, versions: [...], current_version }`; diff returns `{ left_version, right_version, changed: [{ key, left, right }] }`. Lineage and manifest shapes match existing backend responses.
- First-run state is "no runs and no scenarios" (from list endpoints with small limit). No persistence of "onboarding dismissed" in this implementation.
- Run type "simulation" is inferred from `config_summary.pipeline_simulation.enabled === true` for generate runs; "benchmark" from `run_type === "benchmark"`.
- Existing file-based and SQLite storage, retention, and cleanup behavior are unchanged.

---

## 4b. UX and cleanup (latest)

- **Runs page**: Fixed hydration error — no nested `<a>` tags. Run ID is a link; "From scenario" is a sibling link (both inside a div).
- **Navigation**: Main nav shows Home, Create, Scenarios, Runs, Artifacts, Docs, About. "More" dropdown: Advanced config, Templates, Validate, Schema, Integrations. Mobile: all items in a single list.
- **Home**: Simplified — one hero, two CTAs (Create dataset, View runs), compact first-run or recent-activity block, one Capabilities section, Docs/About links. Removed long concepts and duplicate use-case blocks.
- **Docs**: "On this page" index with anchor links; section ids (quick-start, packs, runs, simulation, benchmark, scenarios, api, glossary); shorter section titles; consistent spacing.
- **Scenarios list**: Deduplicated by scenario id when loading (filters duplicate entries from API).

---

## 5. Known limitations

- **Wizard / advanced config**: UX is still focused on core flows; simulation, benchmark, and runtime remain primarily in Advanced. Nested config sections are not yet exposed in the wizard.
- **Manifest download**: Run detail shows manifest fields from API but does not add a "Download manifest.json" button (artifact download would depend on how artifact URLs are exposed).
- **Scenario restore**: No "restore version" or "duplicate from version" action; version history is view and diff only.

---

## 6. Optional future improvements

- Expand wizard UX: nested config sections (generation, simulation, benchmark, privacy, export, load, runtime), validation messages, save/update/save-as, import/export scenario in UI.
- Scenario "use this version": e.g. open advanced config with a selected version’s config (via query or sessionStorage) so user can save as new scenario.
- Backend test that asserts lineage and manifest response shape for a completed run (not only 404 for missing run).
