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
    <div className="max-w-4xl mx-auto space-y-6">
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

      <div className="flex gap-2 flex-wrap">
        {pack.category && (
          <span className="px-3 py-1 rounded-md text-sm font-medium bg-[var(--brand-teal)]/10 text-[var(--brand-teal)]">
            {pack.category}
          </span>
        )}
        <span className="px-3 py-1 rounded-full text-sm bg-slate-100 text-slate-700">
          {tables.length} tables · {relCount} relationships
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-slate-500">Tables</p>
            <p className="text-xl font-semibold">{tables.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-slate-500">Relationships</p>
            <p className="text-xl font-semibold">{relCount}</p>
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

      {(pack.recommended_use_cases?.length || pack.supported_features?.length) ? (
        <Card>
          <CardHeader>
            <CardTitle>Pack capabilities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {pack.recommended_use_cases && pack.recommended_use_cases.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-slate-700 mb-2">Recommended use cases</p>
                  <div className="flex flex-wrap gap-2">
                    {pack.recommended_use_cases.map((u) => (
                      <span key={u} className="px-2 py-1 rounded bg-slate-100 text-slate-800 text-sm">{u}</span>
                    ))}
                  </div>
                </div>
              )}
              {pack.supported_features && pack.supported_features.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-slate-700 mb-2">Supported features</p>
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
      ) : null}

      <div className="flex gap-3 pt-2">
        <Link href={`/create/wizard?pack=${id}`}><Button>Create dataset</Button></Link>
        <Link href={`/schema?pack=${id}`}><Button variant="outline">Schema diagram</Button></Link>
      </div>
    </div>
  );
}
