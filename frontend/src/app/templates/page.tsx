"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { fetchPacks, type PackInfo } from "@/lib/api";

export default function TemplatesPage() {
  const [packs, setPacks] = useState<PackInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPacks()
      .then(setPacks)
      .catch(() => setPacks([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Domain packs</h1>
        <p className="mt-1 text-slate-600">Pre-built schemas and rules for common domains. Pick one and generate in seconds.</p>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-40 rounded-xl border border-slate-200 bg-slate-50 animate-pulse" />
          ))}
        </div>
      ) : packs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-slate-600">Could not load packs.</p>
            <p className="text-sm text-slate-500 mt-2">Ensure the API is running at <code className="bg-slate-100 px-1.5 py-0.5 rounded font-mono text-xs">http://localhost:8000</code></p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {packs.map((p) => (
            <Link key={p.id} href={`/templates/${p.id}`}>
              <Card className="h-full hover:border-[var(--brand-teal)]/40 hover:shadow-md transition-all cursor-pointer group">
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="capitalize text-lg group-hover:text-[var(--brand-teal)] transition-colors">{p.name ?? p.id.replace(/_/g, " ")}</CardTitle>
                    {p.category && (
                      <span className="px-2 py-0.5 rounded-md text-xs font-medium bg-[var(--brand-teal)]/10 text-[var(--brand-teal)] shrink-0">
                        {p.category}
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-600 line-clamp-3">{p.description}</p>
                  <div className="flex gap-3 mt-3 text-xs text-slate-500">
                    {p.tables_count != null && <span>{p.tables_count} tables</span>}
                    {p.relationships_count != null && <span>·</span>}
                    {p.relationships_count != null && <span>{p.relationships_count} relationships</span>}
                  </div>
                  {p.key_entities && p.key_entities.length > 0 && (
                    <p className="text-xs text-slate-500 mt-1.5">
                      {p.key_entities.slice(0, 4).join(", ")}{p.key_entities.length > 4 ? "…" : ""}
                    </p>
                  )}
                  <p className="text-sm font-medium text-[var(--brand-teal)] mt-3">View template →</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
