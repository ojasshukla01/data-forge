# Data Forge Frontend

Next.js 16 product UI for Data Forge: Create wizard, Advanced config, Runs, Scenarios, Artifacts, Schema Studio, validation, and run comparison.

## Getting Started

From the repo root, start the API and frontend:

```bash
# Terminal 1: API
uv run uvicorn data_forge.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev
```

Open [http://localhost:3000](http://localhost:3000). See [docs/demo-walkthrough.md](../docs/demo-walkthrough.md) for a full walkthrough.

## Scripts

| Script | Command |
|--------|---------|
| Dev | `npm run dev` |
| Build | `npm run build` |
| Lint | `npm run lint` |
| Tests | `npm test` |
| E2E | `npm run e2e` (requires API + frontend running) |

## UI Architecture

- **Design system** (`src/components/ui/`): Badge, Button, Card, CodeBlock, Divider, EmptyState, Panel, SectionHeader, Skeleton, StatCard, Tabs
- **Typography**: Space Grotesk (headings), Inter (body), JetBrains Mono (code)
- **Brand colors**: `--brand-teal`, `--brand-cyan`, `--brand-deep-blue`, `--brand-accent`
- **Assets**: `public/branding/`, `public/illustrations/`, `public/domain-pack-illustrations/`
