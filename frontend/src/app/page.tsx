"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { fetchRuns, fetchScenarios, type RunRecord, type ScenarioRecord } from "@/lib/api";

const capabilities = [
  { title: "Realistic synthetic data", desc: "Schema-aware, FK-respecting, time-consistent.", href: "/create/wizard" },
  { title: "Pipeline simulation", desc: "Event streams, full snapshot, incremental, CDC with bronze/silver/gold.", href: "/create/advanced" },
  { title: "Validation & quality", desc: "Schema validation, GE expectations, manifest reconciliation.", href: "/validate" },
];

export default function HomePage() {
  const [recentRuns, setRecentRuns] = useState<RunRecord[]>([]);
  const [recentScenarios, setRecentScenarios] = useState<ScenarioRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchRuns({ limit: 5 }).then((d) => setRecentRuns(d.runs ?? [])).catch(() => setRecentRuns([])),
      fetchScenarios({}).then((d) => setRecentScenarios(d.scenarios ?? [])).catch(() => setRecentScenarios([])),
    ]).finally(() => setLoading(false));
  }, []);

  const isFirstRun = !loading && recentRuns.length === 0 && recentScenarios.length === 0;

  return (
    <div className="space-y-12 sm:space-y-16">
      <section className="text-center max-w-xl mx-auto pt-4 sm:pt-8 pb-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Data Forge
        </h1>
        <p className="mt-3 text-slate-600 text-base sm:text-lg">
          Schema-aware synthetic data for databases, APIs, and pipelines. Realistic, relational, privacy-safe.
        </p>
        <div className="flex flex-wrap justify-center gap-3 mt-6">
          <Link href="/create/wizard">
            <Button size="lg">Create dataset</Button>
          </Link>
          <Link href="/runs">
            <Button variant="outline" size="lg">View runs</Button>
          </Link>
        </div>
      </section>

      {isFirstRun && (
        <section className="max-w-2xl mx-auto rounded-xl border border-slate-200 bg-slate-50/50 p-5 sm:p-6" aria-label="Get started">
          <h2 className="text-lg font-semibold text-slate-900 mb-2">Get started</h2>
          <p className="text-slate-600 text-sm mb-4">No runs or scenarios yet. Pick one:</p>
          <div className="flex flex-wrap gap-2">
            <Link href="/create/wizard"><Button size="sm">Create</Button></Link>
            <Link href="/templates"><Button variant="outline" size="sm">Templates</Button></Link>
            <Link href="/scenarios"><Button variant="outline" size="sm">Scenarios</Button></Link>
            <Link href="/create/advanced"><Button variant="outline" size="sm">Advanced / Import</Button></Link>
          </div>
        </section>
      )}

      {!loading && (recentRuns.length > 0 || recentScenarios.length > 0) && (
        <section className="max-w-2xl mx-auto">
          <h2 className="text-lg font-semibold text-slate-900 mb-3">Recent</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {recentRuns.length > 0 && (
              <Card>
                <CardContent className="py-3">
                  <p className="text-sm font-medium text-slate-700 mb-1">Runs</p>
                  <ul className="text-sm space-y-0.5">
                    {recentRuns.slice(0, 3).map((r) => (
                      <li key={r.id}>
                        <Link href={`/runs/${r.id}`} className="text-[var(--brand-teal)] hover:underline font-mono truncate block">{r.id}</Link>
                      </li>
                    ))}
                  </ul>
                  <Link href="/runs" className="text-xs text-slate-500 hover:text-[var(--brand-teal)] mt-2 inline-block">View all</Link>
                </CardContent>
              </Card>
            )}
            {recentScenarios.length > 0 && (
              <Card>
                <CardContent className="py-3">
                  <p className="text-sm font-medium text-slate-700 mb-1">Scenarios</p>
                  <ul className="text-sm space-y-0.5">
                    {recentScenarios.slice(0, 3).map((s) => (
                      <li key={s.id}>
                        <Link href={`/scenarios/${s.id}`} className="text-[var(--brand-teal)] hover:underline truncate block">{s.name}</Link>
                      </li>
                    ))}
                  </ul>
                  <Link href="/scenarios" className="text-xs text-slate-500 hover:text-[var(--brand-teal)] mt-2 inline-block">View all</Link>
                </CardContent>
              </Card>
            )}
          </div>
        </section>
      )}

      <section className="max-w-3xl mx-auto pt-6 border-t border-slate-100">
        <h2 className="text-lg font-semibold text-slate-900 mb-3 text-center">Capabilities</h2>
        <div className="grid gap-3 sm:grid-cols-3">
          {capabilities.map((c) => (
            <Link key={c.title} href={c.href}>
              <Card className="h-full hover:border-[var(--brand-teal)]/30 transition-colors">
                <CardContent className="py-3 px-4">
                  <p className="font-medium text-slate-900 text-sm">{c.title}</p>
                  <p className="text-xs text-slate-600 mt-0.5">{c.desc}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
        <p className="text-center mt-6 text-sm text-slate-500">
          <Link href="/docs" className="text-[var(--brand-teal)] hover:underline">Docs</Link>
          {" · "}
          <Link href="/about" className="text-[var(--brand-teal)] hover:underline">About</Link>
        </p>
      </section>
    </div>
  );
}
