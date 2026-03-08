"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { fetchRunDetail, fetchRunStatus, rerunRun, cloneRunConfig, type RunRecord } from "@/lib/api";
import { cn } from "@/lib/utils";

const POLL_INTERVAL_MS = 2000;

export default function RunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [run, setRun] = useState<RunRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const r = await fetchRunDetail(id);
    setRun(r ?? null);
    return r;
  }, [id]);

  useEffect(() => {
    load()
      .catch((e) => { setError(e instanceof Error ? e.message : "Failed"); setRun(null); })
      .finally(() => setLoading(false));
  }, [load]);

  useEffect(() => {
    if (!run || !["queued", "running"].includes(run.status)) return;
    const t = setInterval(async () => {
      const r = await load();
      if (r && ["succeeded", "failed", "cancelled"].includes(r.status)) return;
    }, POLL_INTERVAL_MS);
    return () => clearInterval(t);
  }, [id, run?.status, load]);

  const handleRerun = async () => {
    try {
      const res = await rerunRun(id);
      router.push(`/runs/${res.run_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Rerun failed");
    }
  };

  const handleClone = async () => {
    try {
      const { config } = await cloneRunConfig(id);
      router.push(`/create/advanced?clone=${encodeURIComponent(JSON.stringify(config))}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Clone failed");
    }
  };

  if (loading) return <div className="h-32 animate-pulse bg-slate-100 rounded-xl" />;
  if (!run) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Run not found</h1>
        <Link href="/runs"><Button variant="outline">Back to runs</Button></Link>
      </div>
    );
  }

  const cfg = (run.config_summary ?? {}) as Record<string, unknown>;
  const summary = run.result_summary as Record<string, unknown> | undefined;
  const statusColors: Record<string, string> = {
    queued: "text-slate-600",
    running: "text-blue-600",
    succeeded: "text-green-600",
    failed: "text-red-600",
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight font-mono">{run.id}</h1>
          <p className="text-slate-500 text-sm">
            {run.created_at ? new Date(run.created_at * 1000).toLocaleString() : "—"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleClone}>Clone</Button>
          <Button variant="outline" size="sm" onClick={handleRerun}>Rerun</Button>
          {(summary?.output_dir || (summary as { artifact_run_id?: string }).artifact_run_id) && (
            <Link href={`/artifacts?run=${(summary as { artifact_run_id?: string }).artifact_run_id ?? run.id}`}>
              <Button variant="outline" size="sm">Artifacts</Button>
            </Link>
          )}
          <Link href="/create/wizard"><Button variant="outline" size="sm">New run</Button></Link>
        </div>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-slate-500">Status</p>
            <p className={cn("text-lg font-semibold", statusColors[run.status] ?? "text-slate-900")}>{run.status}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-slate-500">Tables</p>
            <p className="text-lg font-semibold">{summary?.total_tables != null ? String(summary.total_tables) : "—"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-slate-500">Total rows</p>
            <p className="text-lg font-semibold">
              {typeof summary?.total_rows === "number" ? (summary.total_rows as number).toLocaleString() : "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <p className="text-sm text-slate-500">Duration</p>
            <p className="text-lg font-semibold">
              {run.duration_seconds != null ? `${run.duration_seconds}s` : "—"}
            </p>
          </CardContent>
        </Card>
      </div>

      {run.stage_progress && run.stage_progress.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Stage progress</CardTitle>
            <p className="text-sm text-slate-500 mt-1">Stage timeline with durations</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {run.stage_progress.map((s) => (
                  <div key={s.name} className="flex items-center gap-4 text-sm">
                    <span className={cn(
                      "w-24 shrink-0",
                      s.status === "completed" && "text-green-600",
                      s.status === "running" && "text-blue-600 font-medium",
                      s.status === "failed" && "text-red-600",
                      s.status === "skipped" && "text-slate-400 italic"
                    )}>{s.status}</span>
                    <span className="flex-1">{s.name.replace(/_/g, " ")}</span>
                    {s.duration_seconds != null && s.status === "completed" && (
                      <span className="text-slate-400 shrink-0">{s.duration_seconds}s</span>
                    )}
                    {s.message && <span className="text-slate-500 truncate max-w-[200px]">{s.message}</span>}
                  </div>
                ))}
            </div>
            {run.status === "running" && (
              <div className="mt-3 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-300"
                  style={{ width: `${(run.stage_progress?.filter((x) => x.status === "completed").length ?? 0) / (run.stage_progress?.length ?? 1) * 100}%` }}
                />
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {run.events && run.events.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Logs</CardTitle>
            <p className="text-sm text-slate-500 mt-1">Run events and messages</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-1.5 max-h-48 overflow-y-auto font-mono text-xs">
              {run.events.map((e, i) => (
                <div key={i} className="flex gap-2">
                  <span className={cn(
                    "shrink-0 w-14",
                    e.level === "error" && "text-red-600",
                    e.level === "info" && "text-slate-600",
                    e.level === "warning" && "text-amber-600"
                  )}>{e.level}</span>
                  <span className="text-slate-700">{e.message}</span>
                  {e.ts && (
                    <span className="text-slate-400 shrink-0">
                      {new Date(e.ts * 1000).toLocaleTimeString()}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {run.error_message && (
        <Card className="border-red-200 bg-red-50/50">
          <CardHeader>
            <CardTitle className="text-red-900">Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-800">{run.error_message}</p>
          </CardContent>
        </Card>
      )}

      {run.warnings && run.warnings.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/50">
          <CardHeader>
            <CardTitle className="text-amber-900">Warnings</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside text-sm text-amber-800">
              {run.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Config</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="text-sm space-y-2">
              <div><dt className="text-slate-500">Pack</dt><dd className="font-medium">{String(run.selected_pack ?? cfg.pack ?? "—")}</dd></div>
              <div><dt className="text-slate-500">Mode</dt><dd className="font-medium">{String(cfg.mode ?? "full_snapshot")}</dd></div>
              <div><dt className="text-slate-500">Layer</dt><dd className="font-medium">{String(cfg.layer ?? "bronze")}</dd></div>
              <div><dt className="text-slate-500">Scale</dt><dd className="font-medium">{String(cfg.scale ?? "—")}</dd></div>
              <div><dt className="text-slate-500">Export</dt><dd className="font-medium">{String(cfg.export_format ?? "—")}</dd></div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Output</CardTitle>
          </CardHeader>
          <CardContent>
            {summary?.output_dir ? (
              <>
                <p className="text-sm font-mono break-all">{String(summary.output_dir)}</p>
                {Array.isArray(summary.export_paths) && (
                  <p className="text-sm text-slate-500 mt-2">{summary.export_paths.length} file(s) exported</p>
                )}
              </>
            ) : (
              <p className="text-slate-500 text-sm">—</p>
            )}
          </CardContent>
        </Card>
      </div>

      {(summary?.integration_summaries as Record<string, unknown> | undefined) && Object.keys(summary?.integration_summaries as Record<string, unknown> ?? {}).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Integration results</CardTitle>
            <p className="text-sm text-slate-500 mt-1">dbt, GE, Airflow, contracts, manifest</p>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              {Object.entries(summary?.integration_summaries as Record<string, Record<string, unknown>> ?? {}).map(([key, val]) => {
                if (!val || typeof val !== "object") return null;
                const err = val.error as string | undefined;
                const enabled = val.enabled === true;
                const label = key.replace(/_/g, " ");
                return (
                  <div key={key} className="p-3 rounded-lg border border-slate-200 bg-slate-50/50">
                    <p className="font-medium text-sm text-slate-900 capitalize">{label}</p>
                    {err ? (
                      <p className="text-red-600 text-xs mt-1">{err}</p>
                    ) : enabled ? (
                      <ul className="text-xs text-slate-600 mt-2 space-y-0.5">
                        {val.output_dir != null && <li>Output: <code className="font-mono">{String(val.output_dir)}</code></li>}
                        {val.manifest_path != null && <li>Manifest: <code className="font-mono">{String(val.manifest_path)}</code></li>}
                        {val.seeds_generated != null && <li>{Array.isArray(val.seeds_generated) ? val.seeds_generated.length : 0} seeds</li>}
                        {val.suites_generated != null && <li>{String(val.suites_generated)} suite(s)</li>}
                        {val.files_generated != null && <li>{String(val.files_generated)} file(s)</li>}
                        {val.fixtures_generated != null && <li>{Array.isArray(val.fixtures_generated) ? val.fixtures_generated.length : 0} fixture(s)</li>}
                      </ul>
                    ) : (
                      <p className="text-slate-500 text-xs mt-1">Skipped</p>
                    )}
                  </div>
                );
              })}
            </div>
            {(summary as { artifact_run_id?: string }).artifact_run_id && (
              <Link href={`/artifacts?run=${(summary as { artifact_run_id?: string }).artifact_run_id}`} className="inline-block mt-4">
                <Button variant="outline" size="sm">Browse artifacts</Button>
              </Link>
            )}
          </CardContent>
        </Card>
      )}

      {run.run_type === "benchmark" && summary && (
        <Card>
          <CardHeader>
            <CardTitle>Benchmark metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div><p className="text-sm text-slate-500">Rows</p><p className="text-lg font-semibold">{String(summary.total_rows_generated ?? summary.rows_generated ?? "—")}</p></div>
              <div><p className="text-sm text-slate-500">Duration</p><p className="text-lg font-semibold">{summary.duration != null ? `${summary.duration}s` : run.duration_seconds != null ? `${run.duration_seconds}s` : "—"}</p></div>
              <div><p className="text-sm text-slate-500">Throughput</p><p className="text-lg font-semibold">{summary.throughput != null ? `${summary.throughput} rows/s` : "—"}</p></div>
              <div><p className="text-sm text-slate-500">Memory est.</p><p className="text-lg font-semibold">{summary.memory_estimate != null ? `${summary.memory_estimate} MB` : summary.peak_memory_mb_estimate != null ? `${summary.peak_memory_mb_estimate} MB` : "—"}</p></div>
            </div>
          </CardContent>
        </Card>
      )}

      <Link href="/runs"><Button variant="outline">← Back to runs</Button></Link>
    </div>
  );
}
