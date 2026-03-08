import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

const domainPacks = [
  { id: "saas_billing", name: "SaaS Billing", category: "SaaS", desc: "Organizations, plans, subscriptions, invoices, support tickets" },
  { id: "ecommerce", name: "E‑commerce", category: "Retail", desc: "Customers, products, orders, payments, shipments" },
  { id: "fintech_transactions", name: "Fintech", category: "Finance", desc: "Accounts, transactions, ledgers" },
  { id: "healthcare_ops", name: "Healthcare", category: "Healthcare", desc: "Patients, providers, claims" },
  { id: "logistics_supply_chain", name: "Logistics", category: "Supply Chain", desc: "Shipments, warehouses, inventory" },
  { id: "adtech_analytics", name: "AdTech", category: "Advertising", desc: "Impressions, campaigns, events" },
  { id: "hr_workforce", name: "HR", category: "HR", desc: "Employees, departments, payroll" },
  { id: "iot_telemetry", name: "IoT", category: "IoT", desc: "Devices, sensors, telemetry" },
  { id: "social_platform", name: "Social", category: "Social", desc: "Users, posts, interactions" },
  { id: "payments_ledger", name: "Payments", category: "Finance", desc: "Transactions, ledgers, reconciliations" },
];

const integrations = [
  { name: "dbt", desc: "Seeds, sources, schema tests", icon: "dbt" },
  { name: "Great Expectations", desc: "Expectation suites and checkpoints", icon: "ge" },
  { name: "Airflow", desc: "DAG templates for pipelines", icon: "af" },
  { name: "Warehouses", desc: "SQLite, DuckDB, Postgres, Snowflake, BigQuery", icon: "wh" },
  { name: "Contracts", desc: "OpenAPI fixture generation", icon: "ct" },
  { name: "Manifests", desc: "Golden dataset row counts", icon: "mf" },
];

const capabilities = [
  { title: "Realistic synthetic datasets", desc: "Schema-aware, FK-respecting, time-consistent data for demos and UAT.", href: "/create/wizard" },
  { title: "Pipeline simulation", desc: "Full snapshot, incremental, CDC with bronze/silver/gold and schema drift.", href: "/create/wizard" },
  { title: "Validation & quality", desc: "Schema validation, GE expectations, manifest reconciliation.", href: "/validate" },
  { title: "Warehouse loading", desc: "Load directly into SQLite, DuckDB, Postgres, Snowflake, or BigQuery.", href: "/create/advanced" },
  { title: "Benchmarking", desc: "Performance benchmarks with chunked generation.", href: "/create/advanced" },
  { title: "Artifacts & integrations", desc: "dbt, GE, Airflow, contracts—all in one run.", href: "/artifacts" },
];

export default function HomePage() {
  return (
    <div className="space-y-20">
      <section className="text-center space-y-8 py-12 md:py-16">
        <div className="flex justify-center">
          <Image src="/branding/logo-mark.svg" alt="" width={64} height={64} />
        </div>
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl md:text-6xl">
            Data Forge
          </h1>
          <p className="mt-4 text-xl text-slate-600 max-w-2xl mx-auto font-medium">
            Schema-aware synthetic data for databases, APIs, and pipelines
          </p>
        </div>
        <p className="mx-auto max-w-2xl text-slate-600">
          Generate realistic, relational, privacy-safe test data. Not just fake names—production-like data
          that respects schemas, foreign keys, and business rules. Built for demos, UAT, and pipeline development.
        </p>
        <div className="flex flex-wrap justify-center gap-3 pt-2">
          <Link href="/create/wizard"><Button size="lg">Create Dataset</Button></Link>
          <Link href="/templates"><Button variant="outline" size="lg">Explore Templates</Button></Link>
          <Link href="/validate"><Button variant="outline" size="lg">Validate Data</Button></Link>
          <Link href="/runs"><Button variant="ghost" size="lg">View Runs</Button></Link>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-slate-900 mb-6">Core capabilities</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((c) => (
            <Link key={c.title} href={c.href}>
              <Card className="h-full hover:border-[var(--brand-teal)]/40 hover:shadow-md transition-all cursor-pointer group">
                <CardHeader>
                  <CardTitle className="text-base group-hover:text-[var(--brand-teal)] transition-colors">{c.title}</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-slate-600">
                  {c.desc}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-slate-900 mb-2">Domain packs</h2>
        <p className="text-slate-600 mb-6">Pre-built schemas and rules for common domains. Choose one and generate in seconds.</p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {domainPacks.map((p) => (
            <Link key={p.id} href={`/templates/${p.id}`}>
              <Card className="h-full hover:border-[var(--brand-teal)]/40 hover:shadow-md transition-all cursor-pointer">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-slate-900">{p.name}</span>
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-[var(--brand-teal)]/10 text-[var(--brand-teal)]">
                      {p.category}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600">{p.desc}</p>
                  <p className="text-xs text-[var(--brand-teal)] font-medium mt-2">View template →</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
        <div className="mt-6 text-center">
          <Link href="/templates"><Button variant="outline" size="sm">View all templates</Button></Link>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold text-slate-900 mb-2">Integrations</h2>
        <p className="text-slate-600 mb-6">
          Data Forge fits into your data stack. Export dbt seeds, GE suites, Airflow DAGs, and load to warehouses.
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {integrations.map((i) => (
            <Card key={i.name}>
              <CardContent className="py-4">
                <p className="font-medium text-slate-900">{i.name}</p>
                <p className="text-sm text-slate-600 mt-0.5">{i.desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>
        <Link href="/integrations" className="inline-block mt-4 text-sm text-[var(--brand-teal)] font-medium hover:underline">
          Learn more about integrations →
        </Link>
      </section>

      <section className="border-t border-slate-200 pt-12">
        <h2 className="text-2xl font-semibold text-slate-900 mb-4">How it works</h2>
        <ol className="space-y-3 text-slate-600 max-w-xl">
          <li className="flex gap-3"><span className="font-semibold text-[var(--brand-teal)] shrink-0">1.</span> Select a domain pack or provide your schema</li>
          <li className="flex gap-3"><span className="font-semibold text-[var(--brand-teal)] shrink-0">2.</span> Configure scale, mode, layers, and optional messiness</li>
          <li className="flex gap-3"><span className="font-semibold text-[var(--brand-teal)] shrink-0">3.</span> Run preflight and start generation</li>
          <li className="flex gap-3"><span className="font-semibold text-[var(--brand-teal)] shrink-0">4.</span> Export to Parquet/CSV/JSON or load to your warehouse</li>
          <li className="flex gap-3"><span className="font-semibold text-[var(--brand-teal)] shrink-0">5.</span> Use artifacts for dbt, GE, Airflow, and validation</li>
        </ol>
      </section>

      <section className="border-t border-slate-200 pt-12">
        <h2 className="text-2xl font-semibold text-slate-900 mb-4">Who uses Data Forge</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="pt-4">
              <p className="font-medium text-slate-900">Data engineers</p>
              <p className="text-sm text-slate-600 mt-1">Full control over ETL realism, rules, exports, and warehouse loading.</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="font-medium text-slate-900">Platform & QA teams</p>
              <p className="text-sm text-slate-600 mt-1">Privacy checks, contracts, manifests, benchmarking, and validation.</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="font-medium text-slate-900">Product & demo teams</p>
              <p className="text-sm text-slate-600 mt-1">Realistic demo and UAT data with guided presets.</p>
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="border-t border-slate-200 pt-12 text-center">
        <p className="text-slate-600 mb-4">Open-source. Built for the modern data stack.</p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link href="/create/wizard"><Button size="lg">Get started</Button></Link>
          <Link href="/about"><Button variant="outline" size="lg">About</Button></Link>
          <a href="https://github.com/ojasshukla01/data-forge" target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="lg">GitHub</Button>
          </a>
        </div>
      </section>
    </div>
  );
}
