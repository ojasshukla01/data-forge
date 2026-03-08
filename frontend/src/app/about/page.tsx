import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-12">
      <div>
        <h1 className="text-page-title text-3xl font-bold text-slate-900 tracking-tight">About Data Forge</h1>
        <p className="mt-2 text-slate-600">
          An open-source, schema-aware synthetic data platform for developers and data teams.
        </p>
      </div>

      <section>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">What is Data Forge?</h2>
        <p className="text-slate-600 leading-relaxed">
          Data Forge generates realistic, relational, time-aware synthetic data for databases, APIs, and data pipelines.
          It respects schemas, foreign keys, business rules, and optional anomaly injection. The result is production-like
          test data for demos, UAT, integration testing, and pipeline development.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">Why we built it</h2>
        <p className="text-slate-600 leading-relaxed">
          Data engineers and platform teams need realistic test data that mirrors production structure. Off-the-shelf
          generators typically produce flat, unrealistic datasets. Data Forge fills that gap with schema-aware,
          relationship-preserving data that integrates with dbt, Great Expectations, Airflow, and major data warehouses.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">Problems it solves</h2>
        <ul className="space-y-2 text-slate-600">
          <li className="flex gap-2"><span className="text-[var(--brand-teal)] font-medium shrink-0">•</span> Demo and UAT data without touching production</li>
          <li className="flex gap-2"><span className="text-[var(--brand-teal)] font-medium shrink-0">•</span> Pipeline and warehouse load testing with realistic volumes</li>
          <li className="flex gap-2"><span className="text-[var(--brand-teal)] font-medium shrink-0">•</span> Contract and API testing with generated fixtures</li>
          <li className="flex gap-2"><span className="text-[var(--brand-teal)] font-medium shrink-0">•</span> Privacy-safe test datasets with PII detection and redaction</li>
          <li className="flex gap-2"><span className="text-[var(--brand-teal)] font-medium shrink-0">•</span> ETL realism: event streams, CDC, incremental, bronze/silver/gold, schema drift</li>
          <li className="flex gap-2"><span className="text-[var(--brand-teal)] font-medium shrink-0">•</span> Warehouse benchmarking with scale presets and workload profiles</li>
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">How it works</h2>
        <p className="text-slate-600 leading-relaxed mb-4">
          Provide a schema (SQL DDL, JSON Schema, or OpenAPI) or select a pre-built domain pack. Data Forge loads
          business rules, resolves dependencies, and generates data in dependency order. Pipeline simulation adds
          event streams and pipeline snapshots. Warehouse benchmark mode supports scale presets and workload profiles.
          Optional integrations export to dbt seeds, GE suites, Airflow DAGs, and contract fixtures. Data loads directly
          to SQLite, DuckDB, PostgreSQL, Snowflake, or BigQuery.
        </p>
        <Link href="/docs">
          <Button variant="outline" size="md">Full documentation</Button>
        </Link>
      </section>

      <Card className="border-slate-200 bg-slate-50/50">
        <CardHeader>
          <CardTitle className="text-lg">Creator & Maintainer</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="font-semibold text-slate-900">Ojas Shukla</p>
            <p className="text-sm text-slate-600">Senior Data Engineer</p>
          </div>
          <p className="text-sm text-slate-600">
            Built Data Forge to provide data teams with a schema-aware synthetic data tool that integrates
            with the modern data stack. Focused on realism, developer experience, and production readiness.
          </p>
          <a
            href="https://github.com/ojasshukla01"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm font-medium text-[var(--brand-teal)] hover:underline transition-opacity"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
            GitHub profile
          </a>
        </CardContent>
      </Card>

      <section>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">Open source</h2>
        <p className="text-slate-600 leading-relaxed mb-4">
          Data Forge is open source. Contributions, issues, and feature requests are welcome on GitHub.
        </p>
        <div className="flex flex-wrap gap-3">
          <a href="https://github.com/ojasshukla01/data-forge" target="_blank" rel="noopener noreferrer">
            <Button size="md">View on GitHub</Button>
          </a>
          <Link href="/docs"><Button variant="outline" size="md">Documentation</Button></Link>
          <Link href="/create/wizard"><Button variant="outline" size="md">Create Dataset</Button></Link>
        </div>
      </section>
    </div>
  );
}
