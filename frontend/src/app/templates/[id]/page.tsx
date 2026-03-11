"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { fetchPack, type PackDetail } from "@/lib/api";

const CAPABILITY_LABELS: Record<string, string> = {
  contracts: "OpenAPI/JSON Schema contracts",
  etl_simulation: "ETL simulation",
  warehouse_load: "Warehouse load",
  privacy_scan: "Privacy scan",
  benchmarking: "Benchmarking",
  cdc: "CDC",
  validation: "Validation",
};

export default function PackDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [pack, setPack] = useState<PackDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPack(id)
      .then(setPack)
      .catch(() => setPack(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="h-32 animate-pulse bg-slate-100 rounded-xl" />;
  }
  if (!pack) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Pack not found</h1>
        <Link href="/templates">
          <Button variant="outline" className="mt-4">← Back to templates</Button>
        </Link>
      </div>
    );
  }

  const tables = (pack.tables as { name: string; columns: string[]; primary_key: string[] }[]) ?? [];
  const relCount = (pack.relationships_count as number) ?? 0;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex justify-between items-start gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight capitalize">
            {(pack.name as string)?.replace(/_/g, " ") ?? id}
          </h1>
          <p className="mt-1 text-slate-600">{pack.description as string}</p>
        </div>
        <div className="flex gap-2 shrink-0">
          <Link href={`/create/wizard?pack=${id}`}><Button>Use This Template</Button></Link>
          <Link href={`/schema?pack=${id}`}><Button variant="outline" size="sm">Schema Diagram</Button></Link>
        </div>
      </div>

      <section>
        <h2 className="text-lg font-semibold text-slate-900 mb-3">Overview</h2>
        <div className="flex gap-2 flex-wrap mb-4">
          {pack.category && (
            <span className="px-3 py-1 rounded-md text-sm font-medium bg-[var(--brand-teal)]/10 text-[var(--brand-teal)]">
              {pack.category}
            </span>
          )}
          <span className="px-3 py-1 rounded-full text-sm bg-slate-100 text-slate-700">
            {tables.length} tables · {relCount} relationships
          </span>
          {pack.supports_event_streams && (
            <span className="px-2 py-1 rounded-md text-xs font-medium bg-indigo-100 text-indigo-800">Event streams</span>
          )}
          {pack.benchmark_relevance && pack.benchmark_relevance !== "low" && (
            <span className="px-2 py-1 rounded-md text-xs font-medium bg-amber-100 text-amber-800">
              Benchmark {pack.benchmark_relevance}
            </span>
          )}
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-slate-500">Tables</p>
              <p className="text-xl font-semibold font-mono">{tables.length}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-slate-500">Relationships</p>
              <p className="text-xl font-semibold font-mono">{relCount}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-sm text-slate-500">Key entities</p>
              <p className="text-sm font-medium text-slate-800">
                {pack.key_entities?.length ? pack.key_entities.slice(0, 4).join(", ") + (pack.key_entities.length > 4 ? "…" : "") : "—"}
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {pack.supports_event_streams && pack.simulation_event_types && pack.simulation_event_types.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-3">Simulation event types</h2>
          <p className="text-sm text-slate-600 mb-2">Event stream generation supports these event types.</p>
          <div className="flex flex-wrap gap-2">
            {pack.simulation_event_types.map((e) => (
              <span key={e} className="px-2 py-1 rounded bg-indigo-50 text-indigo-800 text-sm font-mono">{e}</span>
            ))}
          </div>
        </section>
      )}

      {pack.key_entities && pack.key_entities.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-slate-900 mb-3">Entities</h2>
          <p className="text-sm text-slate-600 mb-2">Primary tables and entities in this schema.</p>
          <div className="flex flex-wrap gap-2">
            {pack.key_entities.map((e) => (
              <span key={e} className="px-2 py-1 rounded bg-slate-100 text-slate-800 text-sm font-mono">{e}</span>
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold text-slate-900 mb-3">Schema Preview</h2>
      <Card>
        <CardHeader>
          <CardTitle>Tables ({tables.length})</CardTitle>
          <p className="text-sm text-slate-500 mt-1">Entities in this schema</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {tables.map((t) => (
              <div key={t.name} className="border-b border-slate-100 pb-4 last:border-0">
                <p className="font-medium text-slate-900">{t.name}</p>
                <p className="text-sm text-slate-500">Columns: {t.columns?.join(", ")}</p>
                {t.primary_key?.length ? (
                  <p className="text-sm text-slate-500">Primary key: {t.primary_key.join(", ")}</p>
                ) : null}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      </section>

      {(pack.recommended_use_cases?.length || pack.supported_features?.length) ? (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-slate-900">Use Cases & Supported Features</h2>
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                {pack.recommended_use_cases && pack.recommended_use_cases.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-slate-700 mb-2">Use Cases</p>
                    <div className="flex flex-wrap gap-2">
                      {pack.recommended_use_cases.map((u) => (
                        <span key={u} className="px-2 py-1 rounded bg-slate-100 text-slate-800 text-sm">{u}</span>
                      ))}
                    </div>
                  </div>
                )}
                {pack.supported_features && pack.supported_features.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-slate-700 mb-2">Supported Features</p>
                    <p className="text-xs text-slate-500 mb-2">ETL simulation, CDC, warehouse loading, validation, contracts, benchmarking</p>
                    <div className="flex flex-wrap gap-2">
                      {pack.supported_features.map((f) => (
                        <span key={f} className="px-2 py-1 rounded bg-green-50 text-green-800 text-sm">
                          ✓ {CAPABILITY_LABELS[f] ?? f}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </section>
      ) : null}

      <div className="flex gap-3 pt-2">
        <Link href={`/create/wizard?pack=${id}`}><Button>Create dataset</Button></Link>
        <Link href={`/schema?pack=${id}`}><Button variant="outline">Schema diagram</Button></Link>
      </div>
    </div>
  );
}
