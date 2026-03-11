"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Database, GitBranch, CheckCircle2, Layers, Play, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { fetchRuns, fetchScenarios, type RunRecord, type ScenarioRecord } from "@/lib/api";

const capabilities = [
  { title: "Schema Studio", desc: "Design and manage custom schemas. Add tables, columns, relationships, generation rules.", href: "/schema/studio", icon: Layers },
  { title: "Realistic synthetic data", desc: "Schema-aware, FK-respecting, time-consistent.", href: "/create/wizard", icon: Database },
  { title: "Pipeline simulation", desc: "Event streams, full snapshot, incremental, CDC with bronze/silver/gold.", href: "/create/advanced", icon: GitBranch },
  { title: "Validation & quality", desc: "Schema validation, GE expectations, manifest reconciliation.", href: "/validate", icon: CheckCircle2 },
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
      <section className="text-center max-w-2xl mx-auto pt-4 sm:pt-8 pb-2">
        <h1 className="text-hero text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl md:text-5xl">
          Data Forge
        </h1>
        <p className="mt-4 text-slate-600 text-base sm:text-lg max-w-xl mx-auto leading-relaxed">
          Schema-aware synthetic data for databases, APIs, and pipelines. Realistic, relational, privacy-safe.
        </p>
        <div className="flex flex-wrap justify-center gap-3 mt-8">
          <Link
            href="/create/wizard"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 text-base font-medium rounded-lg bg-[var(--brand-teal)] text-white hover:bg-[var(--brand-deep-blue)] shadow-sm hover:shadow transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--brand-teal)] transition-transform hover:scale-[1.02] active:scale-[0.98]"
          >
            <Play className="w-4 h-4 shrink-0" aria-hidden />
            Create dataset
          </Link>
          <Link
            href="/runs"
            className="inline-flex items-center justify-center gap-2 px-6 py-3 text-base font-medium rounded-lg border border-slate-300 text-slate-700 bg-white hover:bg-slate-50 hover:border-slate-400 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-300 transition-transform hover:scale-[1.02] active:scale-[0.98]"
          >
            <FolderOpen className="w-4 h-4 shrink-0" aria-hidden />
            View runs
          </Link>
        </div>
      </section>

      {isFirstRun && (
        <section className="max-w-2xl mx-auto rounded-xl border border-slate-200 bg-slate-50/50 p-5 sm:p-6" aria-label="Get started">
          <h2 className="text-lg font-semibold text-slate-900 mb-2">Get started</h2>
          <p className="text-slate-600 text-sm mb-4">No runs or scenarios yet. Pick one:</p>
          <div className="flex flex-wrap gap-2">
            <Link href="/create/wizard"><Button size="sm">Create</Button></Link>
            <Link href="/schema/studio"><Button variant="outline" size="sm">Schema Studio</Button></Link>
            <Link href="/templates"><Button variant="outline" size="sm">Templates</Button></Link>
            <Link href="/scenarios"><Button variant="outline" size="sm">Scenarios</Button></Link>
            <Link href="/create/advanced"><Button variant="outline" size="sm">Advanced</Button></Link>
          </div>
        </section>
      )}

      {!loading && (recentRuns.length > 0 || recentScenarios.length > 0) && (
        <section className="max-w-2xl mx-auto">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Recent</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {recentRuns.length > 0 && (
              <Card className="group hover:shadow-md transition-shadow duration-200">
                <CardContent className="py-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Play className="w-4 h-4 text-[var(--brand-teal)] shrink-0" aria-hidden />
                    <p className="text-sm font-medium text-slate-800">Runs</p>
                  </div>
                  <ul className="text-sm space-y-1.5">
                    {recentRuns.slice(0, 3).map((r) => (
                      <li key={r.id}>
                        <Link href={`/runs/${r.id}`} className="text-[var(--brand-teal)] hover:underline font-mono text-xs truncate block">{r.id}</Link>
                      </li>
                    ))}
                  </ul>
                  <Link href="/runs" className="text-xs text-slate-500 hover:text-[var(--brand-teal)] mt-3 inline-block font-medium">View all runs</Link>
                </CardContent>
              </Card>
            )}
            {recentScenarios.length > 0 && (
              <Card className="group hover:shadow-md transition-shadow duration-200">
                <CardContent className="py-4">
                  <div className="flex items-center gap-2 mb-2">
                    <FolderOpen className="w-4 h-4 text-[var(--brand-teal)] shrink-0" aria-hidden />
                    <p className="text-sm font-medium text-slate-800">Scenarios</p>
                  </div>
                  <ul className="text-sm space-y-1.5">
                    {recentScenarios.slice(0, 3).map((s) => (
                      <li key={s.id}>
                        <Link href={`/scenarios/${s.id}`} className="text-[var(--brand-teal)] hover:underline truncate block">
                          {s.name || s.id}
                        </Link>
                      </li>
                    ))}
                  </ul>
                  <Link href="/scenarios" className="text-xs text-slate-500 hover:text-[var(--brand-teal)] mt-3 inline-block font-medium">View all scenarios</Link>
                </CardContent>
              </Card>
            )}
          </div>
        </section>
      )}

      <section className="max-w-3xl mx-auto pt-8 border-t border-slate-100">
        <h2 className="text-lg font-semibold text-slate-900 mb-5 text-center">Capabilities</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {capabilities.map((c) => {
            const Icon = c.icon;
            return (
              <Link key={c.title} href={c.href} className="block h-full transition-transform hover:scale-[1.01] active:scale-[0.99]">
                <Card className="h-full hover:border-[var(--brand-teal)]/40 hover:shadow-md transition-all duration-200">
                  <CardContent className="py-4 px-4">
                    <div className="flex items-start gap-3">
                      <span className="flex items-center justify-center w-9 h-9 rounded-lg bg-[var(--brand-teal)]/10 text-[var(--brand-teal)] shrink-0" aria-hidden>
                        <Icon className="w-5 h-5" />
                      </span>
                      <div className="min-w-0">
                        <p className="font-medium text-slate-900 text-sm">{c.title}</p>
                        <p className="text-xs text-slate-600 mt-0.5 leading-relaxed">{c.desc}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
        <p className="text-center mt-8 text-sm text-slate-500">
          <Link href="/docs" className="text-[var(--brand-teal)] hover:underline">Docs</Link>
          {" · "}
          <Link href="/about" className="text-[var(--brand-teal)] hover:underline">About</Link>
        </p>
      </section>
    </div>
  );
}
