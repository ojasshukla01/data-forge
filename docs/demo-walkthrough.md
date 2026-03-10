# Demo walkthrough

This walkthrough is for first-time users, interview demos, and open-source visitors. It assumes you have the repo cloned and dependencies installed.

---

## 1. What to run first

You need two processes:

1. **Backend (API)** — serves runs, scenarios, artifacts, and runs the generation engine.
2. **Frontend** — the Product UI.

From the repo root:

```bash
# Terminal 1
uv run uvicorn data_forge.api.main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Open **http://localhost:3000**. You should see the Data Forge landing page.

---

## 2. Generate demo data (CLI)

Without the UI, you can generate sample outputs so the UI has something to show:

```bash
make demo-data
```

This runs:

- A standard generation (saas_billing, 500 rows, Parquet)
- A second run (ecommerce, 300 rows, CSV)
- A benchmark run (saas_billing, 1000 rows, 1 iteration)

Outputs go to `demo_output/`. These CLI runs do **not** appear in the UI run list (the UI shows only runs started via the API). To see runs in the UI, use the next step.

---

## 3. Generate a run from the UI

1. Go to **Create** (wizard) or open **Create → Start in wizard**.
2. Choose a **domain pack** (e.g. SaaS Billing, E-commerce).
3. Set **scale** (e.g. 500 or 1000) and any options (format, messiness).
4. Click **Run preflight** (optional), then **Start run**.
5. You are redirected to the **run detail** page. Wait until status is **succeeded**.

You now have one run in **Runs**. You can run again with another pack or options to get a second run for comparison.

---

## 4. Inspect runs

- **Runs** — List of all runs (status, pack, row count, duration). Use filters by status, pack, mode, or type. Click a run to open its detail page.
- **Run detail** — Pipeline flow, summary, stage timeline, logs, integration summaries, and links to **Artifacts** and **Compare with another run**.

---

## 5. Compare runs

1. Open a run detail page.
2. Click **Compare with another run**.
3. Or go directly to **/runs/compare** and select **Left run** and **Right run** from the dropdowns.

You’ll see a side-by-side diff (config, summary, benchmark, simulation, artifacts). Expand **Raw / detailed diff (JSON)** to copy the full comparison for debugging.

---

## 6. Save scenarios

1. Go to **Create → Advanced** (or open Advanced config).
2. Configure pack, scale, and any options (simulation, benchmark, etc.).
3. Click **Save as scenario** (or **Update scenario** if you loaded a scenario). Give it a name and optional category/description.
4. Go to **Scenarios**. Your scenario appears in the library. You can **Run** it, **Start in wizard**, or **Edit in Advanced**.

You can also **Import scenario** (JSON from `examples/scenarios/`) or **Create from run** on a run detail page to save that run’s config as a scenario.

---

## 7. Inspect artifacts

- From a **run detail** page, click **Artifacts** (or the Artifacts link in the summary).
- Or go to **Artifacts** and filter by run or by type (dataset, event_stream, dbt, ge, etc.).

You can open or download generated files (Parquet, CSV, JSONL, etc.) produced by that run.

---

## 8. Run a benchmark

1. Go to **Create → Advanced**.
2. Open the **Benchmark** section.
3. Choose **workload profile** and **scale preset** (e.g. small, medium).
4. Click **Start benchmark run**.
5. Open the new run from **Runs**. When it completes, the run detail shows throughput (rows/s), duration, and memory estimate.

---

## Quick reference

| Goal | Where |
|------|--------|
| First run | Create (wizard) → pick pack → set scale → Start run |
| Run history | Runs |
| Run details | Runs → click a run |
| Compare two runs | Run detail → Compare with another run, or /runs/compare |
| Save config | Advanced config → Save as scenario |
| Scenario library | Scenarios |
| Output files | Artifacts (filter by run or type) |
| Benchmark | Advanced config → Benchmark section → Start benchmark run |

For architecture and diagrams, see [architecture-overview.md](architecture-overview.md). For contributing and validation, see [CONTRIBUTING.md](../CONTRIBUTING.md) in the repo root.
