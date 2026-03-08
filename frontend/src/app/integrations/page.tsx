import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

const integrations = [
  { name: "Database adapters", desc: "SQLite, DuckDB, PostgreSQL, Snowflake, BigQuery" },
  { name: "dbt export", desc: "Seeds, sources, schema tests" },
  { name: "Great Expectations", desc: "Expectation suites and checkpoints" },
  { name: "Airflow", desc: "DAG templates for common workflows" },
  { name: "Contracts", desc: "OpenAPI fixture generation" },
  { name: "Warehouse validation", desc: "Row count and load verification" },
  { name: "Pipeline simulation", desc: "Event streams, pipeline snapshots, workload replay" },
  { name: "Warehouse benchmark", desc: "Scale presets, workload profiles, throughput metrics" },
];

export default function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Integrations</h1>
        <p className="mt-1 text-slate-600">
          Data Forge fits into your data stack: databases, dbt, Great Expectations, Airflow, and contract testing.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {integrations.map((i) => (
          <Card key={i.name}>
            <CardHeader>
              <CardTitle className="text-base">{i.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-600">{i.desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
