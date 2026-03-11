"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { InfoTooltip } from "@/components/ui/InfoTooltip";

const terms = [
  { term: "CDC", def: "Change Data Capture—captures incremental changes from source systems" },
  { term: "Bronze / Silver / Gold", def: "Medallion architecture layers: raw (bronze), cleaned (silver), curated (gold)" },
  { term: "Schema drift", def: "Evolution of schema over time; Data Forge can simulate drift events" },
  { term: "Messiness", def: "clean, realistic, or chaotic—controls null ratios, duplicates, and data quirks" },
  { term: "Privacy modes", def: "off = no checks; warn = detect & report; strict = redact sensitive fields before generation" },
  { term: "Artifacts", def: "Output files: datasets, event streams, pipeline snapshots, benchmark profiles, dbt seeds, GE suites, Airflow DAGs, contracts, manifests" },
  { term: "Manifest", def: "Golden snapshot of row counts and schema for regression testing" },
  { term: "Contracts", def: "OpenAPI or JSON Schema contract fixtures for API testing" },
  { term: "Reconciliation", def: "Comparing expected (manifest) vs actual row counts and structure" },
  { term: "Event stream", def: "Time-ordered event data (e.g. order lifecycle, payments). Used in pipeline simulation" },
  { term: "Scale preset", def: "small (~10k), medium (~100k), large (~1M), xlarge (~10M) for benchmark workloads" },
  { term: "Benchmark runs", def: "Performance runs that measure throughput, duration, and memory estimates" },
  { term: "Great Expectations (GE)", def: "Data validation framework; we export compatible expectation suites" },
  { term: "dbt", def: "Data build tool; we export seeds, sources, and schema tests" },
];

export default function DocsPage() {
  return (
    <div className="w-full min-w-0 max-w-4xl mx-auto px-2 sm:px-4 space-y-12 pb-12">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Documentation</h1>
        <p className="mt-1 text-slate-600 text-sm">Concepts, workflows, and features.</p>
      </div>

      <nav className="rounded-lg border border-slate-200 bg-slate-50/50 p-4" aria-label="Documentation index">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">On this page</p>
        <ul className="text-sm space-y-1">
          <li><a href="#quick-start" className="text-[var(--brand-teal)] hover:underline">Quick start</a></li>
          <li><a href="#packs" className="text-[var(--brand-teal)] hover:underline">Domain packs</a></li>
          <li><a href="#schema-studio" className="text-[var(--brand-teal)] hover:underline">Schema Studio</a></li>
          <li><a href="#runs" className="text-[var(--brand-teal)] hover:underline">Runs</a></li>
          <li><a href="#simulation" className="text-[var(--brand-teal)] hover:underline">Pipeline simulation</a></li>
          <li><a href="#benchmark" className="text-[var(--brand-teal)] hover:underline">Benchmark</a></li>
          <li><a href="#scenarios" className="text-[var(--brand-teal)] hover:underline">Scenarios</a></li>
          <li><a href="#api" className="text-[var(--brand-teal)] hover:underline">API reference</a></li>
          <li><a href="#glossary" className="text-[var(--brand-teal)] hover:underline">Glossary</a></li>
        </ul>
      </nav>

      {/* Quick Start */}
      <section id="quick-start" className="scroll-mt-6 border-b border-slate-200 pb-8">
        <h2 className="text-lg font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Quick start
          <InfoTooltip content="Follow these steps to generate your first dataset in under a minute. Best for new users." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          The fastest way to create synthetic data. Go to Create (wizard), pick a domain pack, set your scale, and run.
        </p>
        <Card>
          <CardContent className="py-5 space-y-4 text-slate-700">
            <div>
              <p className="font-medium text-slate-900">Step 1: Choose a domain pack</p>
              <p className="text-sm mt-1">Pick a pre-built schema (e.g. SaaS Billing, E-commerce). Each pack includes tables, relationships, and realistic data generators.</p>
            </div>
            <div>
              <p className="font-medium text-slate-900">Step 2: Configure scale & options</p>
              <p className="text-sm mt-1">Set how many rows to generate (scale), messiness level, and export format (Parquet, CSV, JSON, SQL).</p>
            </div>
            <div>
              <p className="font-medium text-slate-900">Step 3: Add integrations (optional)</p>
              <p className="text-sm mt-1">Enable dbt seeds, Great Expectations, or Airflow DAG export if needed.</p>
            </div>
            <div>
              <p className="font-medium text-slate-900">Step 4: Run preflight & generate</p>
              <p className="text-sm mt-1">Run preflight to validate your config, then start the run. Progress appears on the run detail page.</p>
            </div>
            <div>
              <p className="font-medium text-slate-900">Step 5: Get outputs</p>
              <p className="text-sm mt-1">Check Runs for status, then Artifacts to browse and download your generated files.</p>
            </div>
          </CardContent>
        </Card>
        <Link href="/create/wizard" className="inline-block mt-4">
          <Button size="md">Start creating</Button>
        </Link>
      </section>

      {/* Domain packs */}
      <section id="packs" className="scroll-mt-6 border-b border-slate-200 pb-8">
        <h2 className="text-lg font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Domain packs
          <InfoTooltip content="Domain packs are ready-to-use schemas and rules. No need to write SQL or YAML yourself." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          Domain packs are pre-built schemas and business rules. Each pack defines tables, foreign keys, and realistic generators for a specific domain.
        </p>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          <strong>How to use:</strong> Go to Templates, browse by category (SaaS, E-commerce, Fintech, Healthcare, etc.), click a pack to see its schema and entities, then use &quot;Use This Template&quot; or go to Create. Packs marked &quot;Event streams&quot; or &quot;Benchmark high&quot; are best for simulation and benchmarking.
        </p>
        <Link href="/templates">
          <Button variant="outline" size="md">Browse templates</Button>
        </Link>
      </section>

      {/* Schema Studio */}
      <section id="schema-studio" className="scroll-mt-6 border-b border-slate-200 pb-8">
        <h2 className="text-lg font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Schema Studio
          <InfoTooltip content="Design and manage custom relational schemas. Use with the Create wizard or Advanced config." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          Schema Studio lets you design custom relational schemas from scratch—tables, columns, relationships, and column-level generation rules (faker, sequence, uuid, etc.).
        </p>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          <strong>Important:</strong> You must choose or create a schema first before adding tables. Select an existing schema from the sidebar or click &quot;New schema&quot;.
        </p>
        <ul className="list-disc list-inside text-slate-600 text-sm sm:text-base space-y-1 mb-4">
          <li><strong>Form mode</strong> — Tables, Columns, and Relationships tabs; add tables, columns, PK, FK, generation rules</li>
          <li><strong>JSON mode</strong> — Edit raw schema JSON for advanced control</li>
          <li><strong>Validate</strong> — Check structure and rules before save</li>
          <li><strong>Version history</strong> — Compare versions, diff tables and columns</li>
          <li><strong>Sample preview</strong> — Generate sample rows without a full run</li>
        </ul>
        <p className="text-slate-600 text-sm sm:text-base mb-4">
          Schemas are used in the Create wizard (custom schema source) or Advanced config (custom schema dropdown).
        </p>
        <Link href="/schema/studio">
          <Button variant="outline" size="md">Open Schema Studio</Button>
        </Link>
      </section>

      {/* Understanding runs */}
      <section id="runs" className="scroll-mt-6 border-b border-slate-200 pb-8">
        <h2 className="text-lg font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Runs
          <InfoTooltip content="A run is one generation or benchmark execution. Each run has a unique ID and stores config, results, and artifacts." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          After you start a run, the <strong>run detail page</strong> shows everything about that execution.
        </p>
        <ul className="list-disc list-inside text-slate-600 text-sm sm:text-base space-y-2 mb-4">
          <li><strong>Pipeline flow</strong> — Visual flow: Generation → Transform → Validate → Export → Load → Complete</li>
          <li><strong>Run summary</strong> — Status, duration, rows generated, domain pack, run-type badge (Standard / Simulation / Benchmark)</li>
          <li><strong>Stage timeline</strong> — Each stage (preflight, schema load, generation, export, etc.) with status and duration; &quot;Why slow?&quot; hint</li>
          <li><strong>Lineage</strong> — Run → scenario → version → pack → artifacts</li>
          <li><strong>Reproducibility manifest</strong> — Seed, config version, git SHA, environment (when run has completed)</li>
          <li><strong>Logs</strong> — Event log with timestamps and severity</li>
          <li><strong>Integration summaries</strong> — dbt, GE, Airflow, contracts, manifest status</li>
          <li><strong>Artifacts link</strong> — Browse and download outputs</li>
        </ul>
        <p className="text-slate-600 text-sm sm:text-base mb-2">For <strong>benchmark runs</strong>, you also see profile, scale preset, throughput (rows/s), and memory estimate.</p>
        <p className="text-slate-600 text-sm sm:text-base mb-4">For <strong>pipeline simulation runs</strong>, you see event stream counts, event pattern, and replay mode.</p>
        <Link href="/runs">
          <Button variant="outline" size="md">View runs</Button>
        </Link>
      </section>

      {/* Pipeline simulation */}
      <section id="simulation" className="scroll-mt-6 border-b border-slate-200 pb-8">
        <h2 className="text-lg font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Pipeline simulation
          <InfoTooltip content="Generate event streams and pipeline snapshots instead of (or in addition to) static tables. Ideal for streaming, CDC, and event-driven pipelines." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          Pipeline simulation generates <strong>event streams</strong> and <strong>pipeline snapshots</strong>—time-ordered event data (e.g. order lifecycle, payment events, logistics updates). This is useful for testing streaming pipelines, CDC, and event-driven architectures.
        </p>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          <strong>How to use:</strong> In Advanced config, open the &quot;Pipeline Simulation&quot; section. Enable it, then set:
        </p>
        <ul className="list-disc list-inside text-slate-600 text-sm sm:text-base space-y-1 mb-4">
          <li><strong>Event density</strong> — low, medium, or high (affects event count)</li>
          <li><strong>Event pattern</strong> — steady, burst, seasonal, or growth</li>
          <li><strong>Replay mode</strong> — ordered, shuffled, or windowed</li>
          <li><strong>Late arrival ratio</strong> — fraction of events that arrive &quot;late&quot; (0–1)</li>
        </ul>
        <p className="text-slate-600 text-sm sm:text-base mb-4">
          Supported packs: ecommerce, fintech_transactions, logistics_supply_chain, iot_telemetry, social_platform, saas_billing, payments_ledger.
        </p>
        <Link href="/create/advanced" className="inline-block">
          <Button variant="outline" size="sm">Pipeline simulation in Advanced</Button>
        </Link>
      </section>

      {/* Warehouse benchmark */}
      <section id="benchmark" className="scroll-mt-6 border-b border-slate-200 pb-8">
        <h2 className="text-lg font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Benchmark
          <InfoTooltip content="Measure throughput (rows/s), generation time, and memory. Use scale presets and workload profiles for realistic warehouse load tests." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          Benchmark runs measure performance: rows generated per second, generation and export duration, memory estimate.
        </p>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          <strong>Scale presets:</strong> small (~10k rows), medium (~100k), large (~1M), xlarge (~10M). They control the effective data volume.
        </p>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          <strong>Workload profiles:</strong> wide_table (many columns), high_cardinality (many distinct values), event_stream (append-heavy), fact_table (analytics-style).
        </p>
        <p className="text-slate-600 text-sm sm:text-base mb-4">
          <strong>How to use:</strong> In Advanced config, open the Benchmark section. Choose profile and scale preset, then click &quot;Start benchmark run&quot;. Results appear on the run detail page.
        </p>
        <Link href="/create/advanced" className="inline-block">
          <Button variant="outline" size="sm">Benchmark in Advanced</Button>
        </Link>
      </section>

      {/* Artifacts */}
      <section className="border-b border-slate-200 pb-10">
        <h2 className="text-xl font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Artifacts and manifests
          <InfoTooltip content="Artifacts are all output files from a run: datasets, event streams, dbt seeds, GE suites, DAGs, contracts, manifests." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          Outputs include datasets (Parquet, CSV, JSON, JSONL, SQL), event streams (JSONL), pipeline snapshots, benchmark profiles, dbt seeds, Great Expectations suites, Airflow DAGs, and manifests.
        </p>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          <strong>How to use:</strong> Go to Artifacts. Filter by run or by type (dataset, event_stream, pipeline_snapshot, dbt, ge, etc.). Click a file to preview, or download. Use manifests for regression testing and reconciliation.
        </p>
        <Link href="/artifacts">
          <Button variant="outline" size="md">Browse artifacts</Button>
        </Link>
      </section>

      {/* Data contracts */}
      <section className="border-b border-slate-200 pb-10">
        <h2 className="text-xl font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Data contracts
          <InfoTooltip content="Generate API test fixtures from OpenAPI or JSON Schema. Use for contract testing and validation workflows." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          Generate contract fixtures from OpenAPI or JSON Schema. These are sample request/response payloads that conform to your API spec. Use them for contract testing, mocking, and validation.
        </p>
        <p className="text-slate-600 text-sm sm:text-base mb-4">
          <strong>How to use:</strong> Enable contracts in Advanced config, provide the schema path, and run. Fixtures appear in the artifacts output.
        </p>
      </section>

      {/* Saved scenarios */}
      <section id="scenarios" className="scroll-mt-6 border-b border-slate-200 pb-8">
        <h2 className="text-lg font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Scenarios
          <InfoTooltip content="Save, update, or save-as-new. Edit metadata on the scenario detail page. Masked secrets are never stored." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          Scenarios are named, reusable configs. You can <strong>save</strong> (from Advanced Config or the Create Wizard), <strong>update</strong> an existing scenario when loaded in Advanced Config, or <strong>save as new</strong> to create a copy without overwriting. On the scenario detail page, use &quot;Edit metadata&quot; to change name, description, category, and tags.
        </p>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          <strong>Masked credentials:</strong> Connection secrets (e.g. db_uri, passwords) are never persisted as real values. When you create a scenario from a run or clone a config, sensitive fields are replaced with a placeholder. The UI shows a warning and which fields must be re-entered before running. Do not re-save a scenario with placeholders as real values.
        </p>
        <p className="text-slate-600 text-sm sm:text-base mb-4">
          <strong>Import/Export:</strong> Export as JSON from the scenario detail or library; import via Scenario library. Examples: <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">examples/scenarios/</code>.
        </p>
        <p className="text-slate-600 text-sm sm:text-base mb-4">
          <strong>Version history &amp; diff:</strong> On the scenario detail page, use &quot;Version history&quot; to see all config versions and &quot;Compare versions&quot; to diff any two versions (changed fields, old vs new values).
        </p>
        <Link href="/scenarios">
          <Button variant="outline" size="sm">Scenario library</Button>
        </Link>
      </section>

      {/* Compare runs */}
      <section className="border-b border-slate-200 pb-10">
        <h2 className="text-xl font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Compare runs &amp; debug
          <InfoTooltip content="Side-by-side diff plus optional raw JSON diff for debugging." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          Compare two runs to see what changed: pack, mode, scale, benchmark profile, row counts, throughput, artifact counts. A top summary shows how many fields differ. Changed and missing-on-side values are highlighted.
        </p>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          <strong>Raw diff:</strong> Expand the &quot;Raw / detailed diff (JSON)&quot; section to view or copy the full structured comparison as JSON for debugging or scripting.
        </p>
        <p className="text-slate-600 text-sm sm:text-base mb-4">
          <strong>How to use:</strong> From a run detail page, click &quot;Compare with another run&quot;. Or go to /runs/compare and pick left and right runs. Copy to clipboard from the raw diff block if needed.
        </p>
        <Link href="/runs/compare">
          <Button variant="outline" size="sm">Compare runs</Button>
        </Link>
      </section>

      {/* Local validation and CI */}
      <section className="border-b border-slate-200 pb-10">
        <h2 className="text-xl font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Local validation and demo
          <InfoTooltip content="Run the same checks as CI locally. Use the demo to generate sample outputs without cloud credentials." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          <strong>Full validation</strong> (backend tests, frontend tests, type-check, build): from the repo root run <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">make validate-all</code>, or use <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">scripts/validate_all.ps1</code> / <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">scripts/validate_all.sh</code>. CI runs these steps on every push and pull request.
        </p>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          <strong>Demo workflow:</strong> <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">make demo-data</code> (or <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">scripts/run_demo.ps1</code> / <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">run_demo.sh</code>) generates a standard run, a scenario-style run, and a benchmark result under <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">demo_output/</code>. No cloud credentials required.
        </p>
        <p className="text-slate-600 text-sm sm:text-base mb-4">
          <strong>Scenario examples:</strong> Import JSON from <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">examples/scenarios/</code> via Scenarios → Import scenario. Use Compare runs to diff two runs and the raw JSON diff for debugging.
        </p>
      </section>

      {/* Validation */}
      <section className="border-b border-slate-200 pb-10">
        <h2 className="text-xl font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Validation workflow
          <InfoTooltip content="Validate data against schema and rules, run GE expectations, and reconcile manifest expected vs actual." />
        </h2>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed mb-4">
          Use the Validation Center to validate data against a schema and rules, run Great Expectations expectations, or reconcile a manifest (expected row counts) against actual data.
        </p>
        <p className="text-slate-600 text-sm sm:text-base mb-4">
          <strong>How to use:</strong> Go to Validate. Choose validation type (schema+rules, GE, or reconciliation), enter paths to schema, data, and optional rules/expectations/manifest. Run validation and review the report.
        </p>
        <Link href="/validate">
          <Button variant="outline" size="md">Validation Center</Button>
        </Link>
      </section>

      {/* API reference */}
      <section id="api" className="scroll-mt-6 border-b border-slate-200 pb-8">
        <h2 className="text-lg font-semibold text-slate-900 mb-2">API reference</h2>
        <p className="text-slate-600 text-sm sm:text-base mb-4">
          REST API for generation, runs, scenarios, artifacts, and metrics. OpenAPI (Swagger) docs are available when the backend is running.
        </p>
        <div className="flex flex-wrap gap-3">
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="md">Swagger UI (localhost:8000/docs)</Button>
          </a>
          <a href="http://localhost:8000/redoc" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="md">ReDoc (localhost:8000/redoc)</Button>
          </a>
        </div>
        <p className="text-sm text-slate-500 mt-2">See <code className="bg-slate-100 px-1 rounded">docs/api-reference.md</code> in the repo for an endpoint overview.</p>
      </section>

      {/* Glossary */}
      <section id="glossary" className="scroll-mt-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-2 flex items-center gap-2">
          Glossary
          <InfoTooltip content="Definitions of Data Forge and data-engineering terms used in this product." />
        </h2>
        <div className="grid gap-3 sm:grid-cols-1 lg:grid-cols-2">
          {terms.map((t) => (
            <Card key={t.term}>
              <CardContent className="py-4">
                <p className="font-medium text-slate-900">{t.term}</p>
                <p className="text-sm text-slate-600 mt-1">{t.def}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="border-t border-slate-200 pt-8">
        <div className="flex flex-wrap gap-3">
          <Link href="/about"><Button variant="outline" size="md">About Data Forge</Button></Link>
          <a href="https://github.com/ojasshukla01/data-forge" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="md">GitHub</Button>
          </a>
        </div>
      </section>
    </div>
  );
}
