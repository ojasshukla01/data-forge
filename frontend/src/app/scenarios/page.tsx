"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  fetchScenarios,
  runFromScenario,
  deleteScenario,
  exportScenario,
  importScenario,
  type ScenarioRecord,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const CATEGORIES = [
  { value: "", label: "All" },
  { value: "quick_start", label: "Quick start" },
  { value: "testing", label: "Testing" },
  { value: "pipeline_simulation", label: "Pipeline simulation" },
  { value: "warehouse_benchmark", label: "Warehouse benchmark" },
  { value: "privacy_uat", label: "Privacy UAT" },
  { value: "contracts", label: "Contracts" },
  { value: "custom", label: "Custom" },
];

export default function ScenariosPage() {
  const router = useRouter();
  const [scenarios, setScenarios] = useState<ScenarioRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState("");
  const [search, setSearch] = useState("");
  const [runLoading, setRunLoading] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchScenarios({
      category: categoryFilter || undefined,
      search: search || undefined,
    })
      .then((d) => {
        const list = d.scenarios ?? [];
        const seen = new Set<string>();
        setScenarios(list.filter((s) => { if (seen.has(s.id)) return false; seen.add(s.id); return true; }));
      })
      .catch((e) => { setError(e instanceof Error ? e.message : "Failed"); setScenarios([]); })
      .finally(() => setLoading(false));
  };

  useEffect(load, [categoryFilter, search]);

  const handleRun = async (s: ScenarioRecord) => {
    setRunLoading(s.id);
    try {
      const res = await runFromScenario(s.id);
      router.push(`/runs/${res.run_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Run failed");
    } finally {
      setRunLoading(null);
    }
  };

  const handleDelete = async (s: ScenarioRecord) => {
    if (!confirm(`Delete scenario "${s.name}"?`)) return;
    try {
      await deleteScenario(s.id);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  };

  const handleExport = async (s: ScenarioRecord) => {
    try {
      const data = await exportScenario(s.id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `scenario-${s.id}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed");
    }
  };

  const handleImport = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "application/json";
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      try {
        const text = await file.text();
        const parsed = JSON.parse(text);
        const payload = {
          name: parsed.name ?? "Imported",
          description: parsed.description ?? "",
          category: parsed.category ?? "custom",
          tags: parsed.tags ?? [],
          config: parsed.config ?? parsed,
        };
        await importScenario(payload);
        load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Invalid scenario file");
      }
    };
    input.click();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start flex-wrap gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Scenario library</h1>
          <p className="mt-1.5 text-slate-600 text-sm sm:text-base">Reusable configurations for generation, simulation, and benchmarks</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleImport}>Import scenario</Button>
          <Link href="/create/advanced"><Button size="sm">Create from Advanced config</Button></Link>
        </div>
      </div>

      <div className="flex flex-wrap gap-4">
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          {CATEGORIES.map((c) => <option key={c.value || "all"} value={c.value}>{c.label}</option>)}
        </select>
        <input
          type="text"
          placeholder="Search by name or description"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm w-64"
        />
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => <div key={i} className="h-40 rounded-xl border border-slate-200 bg-slate-50 animate-pulse" />)}
        </div>
      ) : scenarios.length === 0 ? (
        <Card className="border-slate-200">
          <CardContent className="py-14 px-6 text-center">
            <p className="text-slate-600 font-medium">No scenarios yet</p>
            <p className="text-sm text-slate-500 mt-1">Save a configuration from Advanced config, import from <code className="text-xs bg-slate-100 px-1 rounded">examples/scenarios/</code>, or create one from a run.</p>
            <div className="flex flex-wrap justify-center gap-3 mt-6">
              <Link href="/create/advanced"><Button size="sm">Go to Advanced config</Button></Link>
              <Button variant="outline" size="sm" onClick={handleImport}>Import scenario</Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {scenarios.map((s) => (
            <Card key={s.id} className="flex flex-col">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <Link href={`/scenarios/${s.id}`} className="flex-1 min-w-0">
                    <CardTitle className="text-base truncate hover:text-[var(--brand-teal)]">{s.name}</CardTitle>
                  </Link>
                  <span className="shrink-0 px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-600">{s.category}</span>
                </div>
                {s.description && <p className="text-sm text-slate-500 mt-1 line-clamp-2">{s.description}</p>}
                <div className="flex flex-wrap gap-1 mt-2">
                  {s.uses_pipeline_simulation && <Badge variant="category" className="text-xs">Simulation</Badge>}
                  {s.uses_benchmark && <Badge variant="category" className="text-xs">Benchmark</Badge>}
                  {s.source_pack && <Badge variant="category" className="text-xs">{s.source_pack}</Badge>}
                </div>
              </CardHeader>
              <CardContent className="pt-0 mt-auto">
                <p className="text-xs text-slate-400 mb-3">
                  Updated {s.updated_at ? new Date(s.updated_at * 1000).toLocaleDateString() : "—"}
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" onClick={() => handleRun(s)} disabled={!!runLoading}>
                    {runLoading === s.id ? "Starting…" : "Run"}
                  </Button>
                  <Link href={`/create/wizard?scenario=${s.id}`}>
                    <Button variant="outline" size="sm">Start in wizard</Button>
                  </Link>
                  <Link href={`/create/advanced?scenario=${s.id}`}>
                    <Button variant="outline" size="sm">Edit in Advanced</Button>
                  </Link>
                  <Button variant="outline" size="sm" onClick={() => handleExport(s)}>Export</Button>
                  <Button variant="outline" size="sm" onClick={() => handleDelete(s)} className="text-red-600">Delete</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Link href="/create/advanced" className="inline-block text-sm text-slate-500 hover:text-[var(--brand-teal)]">
        ← Back to Advanced config
      </Link>
    </div>
  );
}
