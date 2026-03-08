import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";

const capabilities = [
  { title: "Realistic synthetic data", desc: "Schema-aware, FK-respecting, time-consistent.", href: "/create/wizard" },
  { title: "Pipeline simulation", desc: "Event streams, full snapshot, incremental, CDC with bronze/silver/gold.", href: "/create/advanced" },
  { title: "Validation & quality", desc: "Schema validation, GE expectations, manifest reconciliation.", href: "/validate" },
];

export default function HomePage() {
  return (
    <div className="space-y-16">
      <section className="text-center max-w-2xl mx-auto pt-4">
        <h1 className="text-hero text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Data Forge
        </h1>
        <p className="mt-4 text-xl text-slate-600 font-medium">
          Schema-aware synthetic data for databases, APIs, and pipelines
        </p>
        <p className="mt-3 text-slate-600">
          Generate realistic, relational, privacy-safe test data. Production-like data that respects
          schemas, foreign keys, and business rules.
        </p>
        <div className="flex flex-wrap justify-center gap-3 mt-8">
          <Link href="/create/wizard">
            <Button size="lg">Create Dataset</Button>
          </Link>
          <Link href="/templates">
            <Button variant="outline" size="lg">Explore Templates</Button>
          </Link>
          <Link href="/validate">
            <Button variant="outline" size="lg">Validate Data</Button>
          </Link>
        </div>
        <Link href="/runs" className="inline-block mt-4 text-sm text-slate-500 hover:text-[var(--brand-teal)] transition-colors">
          View runs →
        </Link>
      </section>

      <section className="border-t border-slate-200 pt-12">
        <h2 className="text-xl font-semibold text-slate-900 mb-2 text-center">Why Data Forge Exists</h2>
        <p className="text-slate-600 text-center max-w-2xl mx-auto mb-8">
          Synthetic datasets for demos and UAT. Pipeline simulation with event streams, full snapshot, incremental, and CDC.
          Warehouse benchmark mode with scale presets and workload profiles. Validation and contracts for data quality.
        </p>
        <h2 className="text-xl font-semibold text-slate-900 mb-6 text-center">Core capabilities</h2>
        <div className="grid gap-4 sm:grid-cols-3 max-w-3xl mx-auto">
          {capabilities.map((c) => (
            <Link key={c.title} href={c.href}>
              <Card className="h-full hover:border-[var(--brand-teal)]/40 hover:shadow-md transition-all duration-200 cursor-pointer group">
                <CardContent className="pt-4 pb-4">
                  <p className="font-medium text-slate-900 group-hover:text-[var(--brand-teal)] transition-colors">{c.title}</p>
                  <p className="text-sm text-slate-600 mt-1">{c.desc}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
        <div className="text-center mt-8">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Example Use Cases</h2>
          <div className="grid gap-4 sm:grid-cols-3 max-w-3xl mx-auto text-left">
            <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
              <p className="font-medium text-slate-900">Pipeline simulation</p>
              <p className="text-sm text-slate-600 mt-1">Event streams, full snapshot, incremental, CDC with bronze/silver/gold layers.</p>
            </div>
            <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
              <p className="font-medium text-slate-900">Warehouse benchmark</p>
              <p className="text-sm text-slate-600 mt-1">Scale presets, workload profiles. Load test SQLite, DuckDB, Postgres, Snowflake, BigQuery.</p>
            </div>
            <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50">
              <p className="font-medium text-slate-900">Synthetic analytics</p>
              <p className="text-sm text-slate-600 mt-1">Realistic demo datasets with schema-aware, FK-respecting data.</p>
            </div>
          </div>
          <Link href="/templates" className="inline-block mt-6">
            <Button variant="outline" size="md">Browse templates</Button>
          </Link>
        </div>
      </section>

      <section className="border-t border-slate-200 pt-12 text-center">
        <p className="text-slate-600 mb-4">Open-source. Built for the modern data stack.</p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link href="/create/wizard"><Button size="md">Get started</Button></Link>
          <Link href="/about"><Button variant="outline" size="md">About</Button></Link>
          <Link href="/docs"><Button variant="outline" size="md">Docs</Button></Link>
          <a href="https://github.com/ojasshukla01/data-forge" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="md">GitHub</Button>
          </a>
        </div>
      </section>
    </div>
  );
}
