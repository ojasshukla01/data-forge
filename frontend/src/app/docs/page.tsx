import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

const terms = [
  { term: "CDC", def: "Change Data Capture—captures incremental changes from source systems" },
  { term: "Bronze / Silver / Gold", def: "Medallion architecture layers: raw (bronze), cleaned (silver), curated (gold)" },
  { term: "Schema drift", def: "Evolution of schema over time; Data Forge can simulate drift events" },
  { term: "Messiness", def: "clean, realistic, or chaotic—controls null ratios, duplicates, and data quirks" },
  { term: "Privacy modes", def: "off = no checks; warn = detect & report; strict = redact sensitive fields before generation" },
  { term: "Artifacts", def: "Output files: datasets, dbt seeds, GE suites, Airflow DAGs, contracts, manifests" },
  { term: "Manifest", def: "Golden snapshot of row counts and schema for regression testing" },
  { term: "Contracts", def: "OpenAPI or JSON Schema contract fixtures for API testing" },
  { term: "Reconciliation", def: "Comparing expected (manifest) vs actual row counts and structure" },
  { term: "Benchmark runs", def: "Performance runs that measure throughput, duration, and memory estimates" },
  { term: "Great Expectations (GE)", def: "Data validation framework; we export compatible expectation suites" },
  { term: "dbt", def: "Data build tool; we export seeds, sources, and schema tests" },
];

export default function DocsPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Docs & Help</h1>
        <p className="mt-1 text-slate-600">Quick reference for Data Forge concepts and workflows.</p>
      </div>

      <section>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">What is Data Forge?</h2>
        <p className="text-slate-600 leading-relaxed">
          Data Forge is a schema-aware synthetic data platform. It generates realistic, relational test data
          that respects schemas, foreign keys, and business rules. Use it for demos, UAT, pipeline testing,
          warehouse load testing, and API contract validation.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">Quick start</h2>
        <Card>
          <CardContent className="py-5 space-y-3 text-slate-700">
            <p><span className="font-medium text-slate-900">1.</span> Go to Create → choose a domain pack (e.g. SaaS Billing)</p>
            <p><span className="font-medium text-slate-900">2.</span> Select a use case or customize scale, messiness, mode</p>
            <p><span className="font-medium text-slate-900">3.</span> Choose export format and optional integrations (dbt, GE, Airflow)</p>
            <p><span className="font-medium text-slate-900">4.</span> Review and Run</p>
            <p><span className="font-medium text-slate-900">5.</span> Check Runs and Artifacts for outputs</p>
          </CardContent>
        </Card>
        <Link href="/create/wizard" className="inline-block mt-3"><Button size="sm">Start creating</Button></Link>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">How to choose a domain pack</h2>
        <p className="text-slate-600 leading-relaxed mb-4">
          Domain packs are pre-built schemas and rules. Pick the one that matches your domain: SaaS, e‑commerce,
          fintech, healthcare, logistics, ad tech, HR, IoT, social, or payments. Each pack defines tables,
          relationships, and realistic generators. You can also provide your own schema and rules.
        </p>
        <Link href="/templates"><Button variant="outline" size="sm">Browse templates</Button></Link>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">Understanding run results</h2>
        <p className="text-slate-600 leading-relaxed mb-2">
          After a run completes, the run detail page shows: total tables and rows, stage timeline, integration
          summaries (dbt, GE, Airflow, contracts, manifest), logs, and artifact links. Benchmark runs show
          throughput and memory estimates. Use the Artifacts page to browse and download outputs.
        </p>
        <Link href="/runs"><Button variant="outline" size="sm">View runs</Button></Link>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">Glossary</h2>
        <div className="space-y-3">
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
        <h2 className="text-xl font-semibold text-slate-900 mb-4">More resources</h2>
        <div className="flex flex-wrap gap-3">
          <Link href="/about"><Button variant="outline" size="sm">About Data Forge</Button></Link>
          <a href="https://github.com/ojasshukla01/data-forge" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="sm">GitHub</Button>
          </a>
        </div>
      </section>
    </div>
  );
}
