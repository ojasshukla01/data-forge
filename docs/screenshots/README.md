# Screenshots and demo assets

This folder holds **screenshots** of the Product UI and **demo assets** for README and docs.

## Target filenames

Use consistent names when capturing. See **[SCREENSHOT-CHECKLIST.md](SCREENSHOT-CHECKLIST.md)** for the full checklist and how to reach each view.

| File | Page |
|------|------|
| `landing.png` | Home |
| `create-wizard.png` | Create wizard |
| `templates.png` | Domain packs / templates |
| `schema-visualizer.png` | Schema visualizer |
| `runs.png` | Runs list |
| `run-detail.png` | Run detail |
| `artifacts.png` | Artifacts |
| `scenarios.png` | Scenario library |
| `compare.png` | Compare runs |
| `advanced-config.png` | Advanced config |

## How to add screenshots

1. Run the app locally (API: `uv run uvicorn data_forge.api.main:app --reload --port 8000`; frontend: `cd frontend && npm run dev`).
2. Open the target page (see [SCREENSHOT-CHECKLIST.md](SCREENSHOT-CHECKLIST.md)).
3. Capture and save here with the target filename (e.g. `run-detail.png`).
4. Reference in README or docs as `docs/screenshots/<filename>`.

Use lowercase and hyphens; prefer PNG.
