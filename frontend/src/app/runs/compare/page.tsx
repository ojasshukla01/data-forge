"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { fetchRuns, fetchRunComparison } from "@/lib/api";
import { cn } from "@/lib/utils";

interface DiffItem {
  left: unknown;
  right: unknown;
  changed: boolean;
  status?: "changed" | "unchanged" | "missing_on_left" | "missing_on_right";
}

interface CompareResult {
  left_run: { id: string; status: string; run_type: string; selected_pack?: string };
  right_run: { id: string; status: string; run_type: string; selected_pack?: string };
  metadata_diff: Record<string, DiffItem>;
  config_diff: Record<string, DiffItem>;
  summary_diff: Record<string, DiffItem>;
  simulation_diff: Record<string, DiffItem>;
  benchmark_diff: Record<string, DiffItem>;
  artifact_diff: Record<string, DiffItem>;
  summary?: { total_changed_fields?: number };
  raw_diff?: string;
}

function DiffRow({ label, item }: { label: string; item: DiffItem }) {
  const changed = item.changed;
  const status = item.status || (changed ? "changed" : "unchanged");
  const statusLabel = status === "missing_on_left" ? "Missing (left)" : status === "missing_on_right" ? "Missing (right)" : changed ? "Changed" : null;
  return (
    <tr className={cn(
      changed && "bg-amber-50",
      status === "missing_on_left" && "bg-slate-50",
      status === "missing_on_right" && "bg-slate-50"
    )}>
      <td className="py-1.5 pr-4 text-slate-600 text-sm">{label}</td>
      <td className="py-1.5 pr-4 text-sm font-mono">{String(item.left ?? "—")}</td>
      <td className="py-1.5 text-sm font-mono">{String(item.right ?? "—")}</td>
      {statusLabel && (
        <td className="pl-2">
          <Badge variant="category" className="text-xs">{statusLabel}</Badge>
        </td>
      )}
    </tr>
  );
}

function CompareContent() {
  const searchParams = useSearchParams();
  const leftParam = searchParams.get("left");
  const rightParam = searchParams.get("right");
  const [runs, setRuns] = useState<{ id: string; status: string; run_type?: string }[]>([]);
  const [comparison, setComparison] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leftId, setLeftId] = useState(leftParam || "");
  const [rightId, setRightId] = useState(rightParam || "");

  useEffect(() => {
    fetchRuns({ limit: 50 })
      .then((d) => setRuns(d.runs ?? []))
      .catch(() => setRuns([]));
  }, []);

  useEffect(() => {
    const l = leftParam || leftId;
    const r = rightParam || rightId;
    if (!l || !r || l === r) {
      setComparison(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    fetchRunComparison(l, r)
      .then(setComparison)
      .catch((e) => { setError(e instanceof Error ? e.message : "Compare failed"); setComparison(null); })
      .finally(() => setLoading(false));
  }, [leftParam, rightParam, leftId, rightId]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Compare runs</h1>
        <p className="mt-1.5 text-slate-600 text-sm sm:text-base">Side-by-side comparison of config, summary, benchmark, and artifacts. Use the raw JSON diff for debugging.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Select runs</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-4">
          <div>
            <label className="block text-sm text-slate-600 mb-1">Left run</label>
            <select
              value={leftId}
              onChange={(e) => setLeftId(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm min-w-[200px]"
            >
              <option value="">Select…</option>
              {runs.map((r) => (
                <option key={r.id} value={r.id}>{r.id} ({r.status})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-slate-600 mb-1">Right run</label>
            <select
              value={rightId}
              onChange={(e) => setRightId(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm min-w-[200px]"
            >
              <option value="">Select…</option>
              {runs.map((r) => (
                <option key={r.id} value={r.id}>{r.id} ({r.status})</option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      {loading && <div className="h-32 animate-pulse bg-slate-100 rounded-xl" />}

      {comparison && !loading && (
        <div className="space-y-6">
          {comparison.summary?.total_changed_fields != null && (
            <p className="text-sm text-slate-600">
              <strong>{comparison.summary.total_changed_fields}</strong> field{comparison.summary.total_changed_fields !== 1 ? "s" : ""} differ between runs.
            </p>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Left: {comparison.left_run.id}</CardTitle>
                <div className="flex gap-2 mt-1">
                  <Badge variant="category">{comparison.left_run.status}</Badge>
                  <Badge variant="category">{comparison.left_run.run_type}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <Link href={`/runs/${comparison.left_run.id}`}>
                  <Button variant="outline" size="sm">View run</Button>
                </Link>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Right: {comparison.right_run.id}</CardTitle>
                <div className="flex gap-2 mt-1">
                  <Badge variant="category">{comparison.right_run.status}</Badge>
                  <Badge variant="category">{comparison.right_run.run_type}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <Link href={`/runs/${comparison.right_run.id}`}>
                  <Button variant="outline" size="sm">View run</Button>
                </Link>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Config comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-left">
                <tbody>
                  {Object.entries(comparison.config_diff).map(([k, v]) => (
                    <DiffRow key={k} label={k} item={v} />
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Summary comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-left">
                <tbody>
                  {Object.entries(comparison.summary_diff).map(([k, v]) => (
                    <DiffRow key={k} label={k} item={v} />
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          {Object.keys(comparison.benchmark_diff).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Benchmark comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <table className="w-full text-left">
                  <tbody>
                    {Object.entries(comparison.benchmark_diff).map(([k, v]) => (
                      <DiffRow key={k} label={k} item={v} />
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}

          {Object.keys(comparison.simulation_diff).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Simulation comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <table className="w-full text-left">
                  <tbody>
                    {Object.entries(comparison.simulation_diff).map(([k, v]) => (
                      <DiffRow key={k} label={k} item={v} />
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}

          {comparison.raw_diff && (
            <details className="group">
              <summary className="cursor-pointer list-none rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-100">
                <span className="inline-flex items-center gap-2">
                  <span className="text-slate-500 group-open:rotate-90 transition-transform">▶</span>
                  Raw / detailed diff (JSON)
                </span>
              </summary>
              <div className="mt-2">
                <p className="text-sm text-slate-600 mb-2">
                  Structured JSON diff for debugging. Copy to clipboard or inspect in a JSON viewer.
                </p>
                <CodeBlock copyable language="json">
                  {comparison.raw_diff}
                </CodeBlock>
              </div>
            </details>
          )}
        </div>
      )}

      <Link href="/runs"><Button variant="outline">← Back to runs</Button></Link>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="h-32 animate-pulse bg-slate-100 rounded-xl" />}>
      <CompareContent />
    </Suspense>
  );
}
