# Screenshot checklist

Use this list when capturing UI screenshots for README, docs, or demos. Run the app locally (API on port 8000, frontend on 3000), then capture each view.

## Target filenames (use these for consistency)

| Screenshot | Target filename | How to get there |
|------------|-----------------|------------------|
| Landing / home | `landing.png` | Open `/` |
| Create wizard | `create-wizard.png` | `/create/wizard` |
| Templates / domain packs | `templates.png` | `/templates` |
| Schema visualizer | `schema-visualizer.png` | `/schema` or open a pack with schema |
| Runs list | `runs.png` | `/runs` (after at least one run) |
| Run detail | `run-detail.png` | `/runs/[id]` for a succeeded run |
| Artifacts page | `artifacts.png` | `/artifacts` (optionally `?run=...`) |
| Scenarios page | `scenarios.png` | `/scenarios` |
| Compare runs | `compare.png` | `/runs/compare` with left/right selected |
| Advanced config | `advanced-config.png` | `/create/advanced` |

## Checklist

- [ ] `landing.png` — Home with hero and capability cards
- [ ] `create-wizard.png` — Wizard step (e.g. pack selection or scale)
- [ ] `templates.png` — Domain packs grid with at least one category
- [ ] `schema-visualizer.png` — Schema graph for one pack
- [ ] `runs.png` — Run list with at least one run
- [ ] `run-detail.png` — Run detail with timeline/summary
- [ ] `artifacts.png` — Artifacts list (by run or global)
- [ ] `scenarios.png` — Scenario library (empty or with scenarios)
- [ ] `compare.png` — Compare view with two runs
- [ ] `advanced-config.png` — Advanced config form (optional)

## Tips

- Use a consistent browser width (e.g. 1280px) for comparable layout.
- Prefer PNG. Keep file names lowercase with hyphens.
- For “no data” states, capture the empty state message and CTA.
- After capturing, add the image to this folder and reference in README or docs as `docs/screenshots/<filename>`.
