"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatCard } from "@/components/ui/StatCard";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Badge } from "@/components/ui/Badge";
import { BenchmarkMetrics } from "@/components/BenchmarkMetrics";
import { LogPanel } from "@/components/LogPanel";
import { PipelineFlowGraph } from "@/components/PipelineFlowGraph";
import { PipelineSimulationSection } from "@/components/PipelineSimulationSection";
import { CopyButton } from "@/components/CopyButton";
import {
  fetchRunDetail,
  rerunRun,
  cloneRunConfig,
  createScenarioFromRun,
  fetchRunLineage,
  fetchRunManifest,
  fetchRunTimeline,
  type RunRecord,
  type RunLineage,
  type RunManifest,
  type RunTimeline,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const POLL_INTERVAL_MS = 2000;

export default function RunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [run, setRun] = useState<RunRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lineage, setLineage] = useState<RunLineage | null>(null);
  const [manifest, setManifest] = useState<RunManifest | null>(null);
  const [timeline, setTimeline] = useState<RunTimeline | null>(null);
  const [lineageManifestLoading, setLineageManifestLoading] = useState(false);

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

  useEffect(() => {
    if (!id) return;
    setLineageManifestLoading(true);
    Promise.all([
      fetchRunLineage(id).then(setLineage).catch(() => setLineage(null)),
      fetchRunManifest(id).then(setManifest).catch(() => setManifest(null)),
      fetchRunTimeline(id).then(setTimeline).catch(() => setTimeline(null)),
    ]).finally(() => setLineageManifestLoading(false));
  }, [id]);

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
      const { config, has_masked_sensitive_fields, masked_fields } = await cloneRunConfig(id);
      const cloneParam = encodeURIComponent(JSON.stringify(config));
      const maskedParam = has_masked_sensitive_fields && masked_fields?.length
        ? `&masked=${encodeURIComponent(JSON.stringify(masked_fields))}`
        : "";
      router.push(`/create/advanced?clone=${cloneParam}${maskedParam}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Clone failed");
    }
  };

  const handleCreateScenario = async () => {
    try {
      const s = await createScenarioFromRun(id, {
        name: `From run ${id.slice(0, 12)}`,
        description: `Scenario created from run ${id}`,
      });
      router.push(`/scenarios`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create scenario failed");
    }
  };

  if (loading) return <div className="h-32 animate-pulse bg-slate-200 rounded-xl" />;
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
      <div className="flex justify-between items-start gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap min-w-0">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight font-mono truncate min-w-0">{run.id}</h1>
            <CopyButton text={run.id} label="Copy run ID" title="Copy run ID" />
            {run.run_type === "benchmark" && <Badge variant="category" className="shrink-0">Benchmark</Badge>}
            {run.run_type === "generate" && (cfg?.pipeline_simulation as { enabled?: boolean })?.enabled && <Badge variant="category" className="shrink-0">Simulation</Badge>}
            {run.run_type === "generate" && !(cfg?.pipeline_simulation as { enabled?: boolean })?.enabled && <Badge variant="category" className="shrink-0 bg-slate-100 text-slate-700">Standard</Badge>}
            {run.pinned && <span className="text-sm text-slate-500" title="Pinned (excluded from cleanup)">📌 Pinned</span>}
            {run.archived_at != null && <Badge variant="category" className="shrink-0 bg-slate-200 text-slate-600">Archived</Badge>}
          </div>
          <p className="text-slate-500 text-sm mt-0.5">
            {run.created_at ? new Date(run.created_at * 1000).toLocaleString() : "—"}
            {run.source_scenario_id && (
              <> · From scenario: <Link href={`/scenarios/${run.source_scenario_id}`} className="text-[var(--brand-teal)] hover:underline">{run.source_scenario_id}</Link></>
            )}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={handleClone}>Clone</Button>
          <Button variant="outline" size="sm" onClick={handleCreateScenario}>Create scenario from run</Button>
          <Button variant="outline" size="sm" onClick={handleRerun}>Rerun</Button>
          {Boolean(summary?.output_dir || (summary as { artifact_run_id?: string })?.artifact_run_id) && (
            <Link href={`/artifacts?run=${(summary as { artifact_run_id?: string })?.artifact_run_id ?? run.id}`}>
              <Button variant="outline" size="sm">Artifacts</Button>
            </Link>
          )}
          {run.source_scenario_id && (
            <Link href={`/scenarios/${run.source_scenario_id}`}>
              <Button variant="outline" size="sm">View scenario</Button>
            </Link>
          )}
          <Link href="/create/wizard"><Button variant="outline" size="sm">New run</Button></Link>
        </div>
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <Card>
        <CardHeader>
          <CardTitle>Pipeline Flow</CardTitle>
          <p className="text-sm text-slate-500 mt-1">Generation through completion</p>
        </CardHeader>
        <CardContent>
          <PipelineFlowGraph
            stages={run.stage_progress?.map((s) => ({
              id: s.name,
              label: s.name.replace(/_/g, " "),
              status: s.status as "pending" | "running" | "completed" | "skipped" | "failed",
            }))}
          />
        </CardContent>
      </Card>

      <SectionHeader title="Run Summary" description="Key metrics for this run" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 [&>div]:min-w-0">
        <StatCard
          label="Status"
          value={
            <Badge
              variant={run.status === "succeeded" ? "success" : run.status === "failed" ? "error" : run.status === "running" ? "info" : "category"}
            >
              {run.status}
            </Badge>
          }
        />
        <StatCard label="Duration" value={run.duration_seconds != null ? `${run.duration_seconds}s` : "—"} />
        <StatCard
          label="Rows Generated"
          value={typeof summary?.total_rows === "number" ? (summary.total_rows as number).toLocaleString() : (summary?.total_rows_generated ?? summary?.rows_generated) != null ? String((summary?.total_rows_generated ?? summary?.rows_generated) as number).replace(/\B(?=(\d{3})+(?!\d))/g, ",") : "—"}
        />
        <StatCard
          label="Artifacts"
          value={Array.isArray(summary?.export_paths) ? String(summary.export_paths.length) : (summary?.output_dir ? "Yes" : "—")}
        />
        <StatCard label="Domain Pack" value={String(run.selected_pack ?? cfg.pack ?? "—")} />
        <StatCard label="Run Mode" value={String(cfg.mode ?? "full_snapshot")} />
      </div>

      {(timeline?.why_slow_hint || (run.run_type === "benchmark" && run.duration_seconds != null)) && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3" role="status">
          <p className="text-sm font-medium text-amber-900">Why slow?</p>
          <p className="text-sm text-amber-800 mt-0.5">
            {timeline?.why_slow_hint ?? (run.duration_seconds != null ? `Total duration: ${run.duration_seconds}s. Check stage timeline for bottlenecks.` : "")}
          </p>
        </div>
      )}

      {run.stage_progress && run.stage_progress.length > 0 && (() => {
        const withDuration = run.stage_progress!.filter((s) => s.duration_seconds != null && s.status === "completed");
        const total = run.duration_seconds ?? (withDuration.length ? withDuration.reduce((a, s) => a + (s.duration_seconds ?? 0), 0) : 0);
        const slowest = withDuration.length ? withDuration.reduce((a, s) => (s.duration_seconds ?? 0) > (a?.duration_seconds ?? 0) ? s : a, withDuration[0]) : null;
        const whySlow = total && total > 0 && slowest && slowest.duration_seconds
          ? `${slowest.name.replace(/_/g, " ")} took ${Math.round(100 * slowest.duration_seconds / total)}% of total time (${slowest.duration_seconds}s)`
          : null;
        return (
        <Card>
          <CardHeader>
            <CardTitle>Stage Timeline</CardTitle>
            <p className="text-sm text-slate-500 mt-1">Stage name, status, duration, and timestamp</p>
            {whySlow && (
              <p className="text-sm text-amber-700 mt-2 px-3 py-1.5 bg-amber-50 rounded-md border border-amber-200" role="status">
                <strong>Why slow?</strong> {whySlow}
              </p>
            )}
          </CardHeader>
          <CardContent>
            <div className="relative pl-6 space-y-0">
              <div className="absolute left-1.5 top-2 bottom-2 w-px bg-slate-200" />
              {run.stage_progress.map((s, idx) => {
                const isLast = idx === run.stage_progress!.length - 1;
                const dotClass = s.status === "completed"
                  ? "bg-green-500"
                  : s.status === "running"
                  ? "border-2 border-blue-500 border-t-transparent animate-spin"
                  : s.status === "failed"
                  ? "bg-red-500"
                  : "border border-slate-300 bg-slate-100";
                return (
                  <div key={s.name} className={cn("relative flex items-start gap-4 pb-4", isLast && "pb-0")}>
                    <span className={cn("absolute -left-4.5 mt-0.5 inline-flex w-4 h-4 shrink-0 rounded-full", dotClass)} aria-hidden />
                    <div className="flex-1 min-w-0 overflow-hidden">
                      <div className="flex flex-wrap items-center gap-2 min-w-0">
                        <span className="font-medium text-slate-900 capitalize truncate">{s.name.replace(/_/g, " ")}</span>
                        <span className={cn(
                          "text-xs capitalize shrink-0",
                          s.status === "completed" && "text-green-600",
                          s.status === "running" && "text-blue-600",
                          s.status === "failed" && "text-red-600",
                          s.status === "skipped" && "text-slate-400 italic"
                        )}>{s.status}</span>
                      </div>
                      <div className="flex flex-wrap gap-3 mt-0.5 text-xs text-slate-500 min-w-0">
                        {s.duration_seconds != null && s.status === "completed" && <span className="shrink-0">{s.duration_seconds}s</span>}
                        {s.message && <span className="break-words overflow-hidden">{s.message}</span>}
                      </div>
                    </div>
                  </div>
                );
              })}
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
        );
      })()}

      {run.events && run.events.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Logs</CardTitle>
            <p className="text-sm text-slate-500 mt-1">Run events and messages. JetBrains Mono, timestamps, log level colors. Copy and auto-scroll.</p>
          </CardHeader>
          <CardContent>
            <LogPanel events={run.events} />
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
            <dl className="text-sm space-y-2 min-w-0 overflow-hidden">
              <div className="min-w-0"><dt className="text-slate-500 truncate">Pack</dt><dd className="font-medium truncate">{String(run.selected_pack ?? cfg.pack ?? "—")}</dd></div>
              <div className="min-w-0"><dt className="text-slate-500 truncate">Mode</dt><dd className="font-medium truncate">{String(cfg.mode ?? "full_snapshot")}</dd></div>
              <div className="min-w-0"><dt className="text-slate-500 truncate">Layer</dt><dd className="font-medium truncate">{String(cfg.layer ?? "bronze")}</dd></div>
              <div className="min-w-0"><dt className="text-slate-500 truncate">Scale</dt><dd className="font-medium truncate">{String(cfg.scale ?? "—")}</dd></div>
              <div className="min-w-0"><dt className="text-slate-500 truncate">Export</dt><dd className="font-medium truncate">{String(cfg.export_format ?? "—")}</dd></div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Output</CardTitle>
          </CardHeader>
          <CardContent className="min-w-0 overflow-hidden">
            {summary?.output_dir ? (
              <>
                <p className="text-sm font-mono break-all overflow-hidden">{String(summary.output_dir)}</p>
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

      {/* Lineage */}
      <Card>
        <CardHeader>
          <CardTitle>Lineage</CardTitle>
          <p className="text-sm text-slate-500 mt-1">Run → scenario → version → pack → artifacts</p>
        </CardHeader>
        <CardContent>
          {lineageManifestLoading && !lineage && !manifest ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : lineage ? (
            <dl className="text-sm space-y-2 grid grid-cols-1 sm:grid-cols-2 gap-x-4">
              <div><dt className="text-slate-500">Run ID</dt><dd className="font-mono">{lineage.run_id}</dd></div>
              <div><dt className="text-slate-500">Run type</dt><dd>{lineage.run_type ?? "—"}</dd></div>
              <div><dt className="text-slate-500">Pack</dt><dd>{lineage.pack ?? "—"}</dd></div>
              <div><dt className="text-slate-500">Artifact run ID</dt><dd className="font-mono">{lineage.artifact_run_id ?? "—"}</dd></div>
              {lineage.scenario_id && (
                <>
                  <div><dt className="text-slate-500">Scenario</dt><dd><Link href={`/scenarios/${lineage.scenario_id}`} className="text-[var(--brand-teal)] hover:underline">{lineage.scenario?.name ?? lineage.scenario_id}</Link></dd></div>
                  <div><dt className="text-slate-500">Scenario version</dt><dd>v{lineage.scenario?.version ?? "—"}</dd></div>
                </>
              )}
              {lineage.output_dir && <div className="sm:col-span-2"><dt className="text-slate-500">Output dir</dt><dd className="font-mono text-xs break-all">{lineage.output_dir}</dd></div>}
            </dl>
          ) : (
            <p className="text-sm text-slate-500">Lineage not available for this run.</p>
          )}
        </CardContent>
      </Card>

      {/* Reproducibility manifest */}
      <Card>
        <CardHeader>
          <CardTitle>Reproducibility manifest</CardTitle>
          <p className="text-sm text-slate-500 mt-1">Seed, config version, git SHA, and environment used for this run</p>
        </CardHeader>
        <CardContent>
          {lineageManifestLoading && !manifest ? (
            <p className="text-sm text-slate-500">Loading…</p>
          ) : manifest ? (
            <dl className="text-sm space-y-2 grid grid-cols-1 sm:grid-cols-2 gap-x-4">
              <div><dt className="text-slate-500">Run ID</dt><dd className="font-mono">{manifest.run_id}</dd></div>
              <div><dt className="text-slate-500">Config schema version</dt><dd>{manifest.config_schema_version ?? "—"}</dd></div>
              <div><dt className="text-slate-500">Seed</dt><dd>{manifest.seed != null ? String(manifest.seed) : "—"}</dd></div>
              <div><dt className="text-slate-500">Pack</dt><dd>{manifest.pack ?? "—"}</dd></div>
              <div><dt className="text-slate-500">Scale</dt><dd>{manifest.scale != null ? String(manifest.scale) : "—"}</dd></div>
              <div><dt className="text-slate-500">Storage backend</dt><dd>{manifest.storage_backend ?? "—"}</dd></div>
              {manifest.git_commit_sha && <div><dt className="text-slate-500">Git commit</dt><dd className="font-mono text-xs">{manifest.git_commit_sha}</dd></div>}
              {manifest.duration_seconds != null && <div><dt className="text-slate-500">Duration (s)</dt><dd>{manifest.duration_seconds}</dd></div>}
              {manifest.total_rows_generated != null && <div><dt className="text-slate-500">Rows generated</dt><dd>{manifest.total_rows_generated.toLocaleString()}</dd></div>}
              {manifest.created_at != null && <div className="sm:col-span-2"><dt className="text-slate-500">Created</dt><dd>{new Date(manifest.created_at * 1000).toLocaleString()}</dd></div>}
            </dl>
          ) : (
            <p className="text-sm text-slate-500">Manifest not available (e.g. run not yet completed or output not on disk).</p>
          )}
        </CardContent>
      </Card>

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
                  <div key={key} className="p-3 rounded-lg border border-slate-200 bg-slate-50/50 min-w-0 overflow-hidden">
                    <p className="font-medium text-sm text-slate-900 capitalize truncate">{label}</p>
                    {err ? (
                      <p className="text-red-600 text-xs mt-1 break-words overflow-hidden">{err}</p>
                    ) : enabled ? (
                      <ul className="text-xs text-slate-600 mt-2 space-y-0.5 overflow-hidden">
                        {val.output_dir != null && <li className="min-w-0 overflow-hidden">Output: <code className="font-mono break-all">{String(val.output_dir)}</code></li>}
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
            <CardTitle>Benchmark Metrics</CardTitle>
            <p className="text-sm text-slate-500 mt-1">Profile, throughput, stage timing, memory estimate</p>
          </CardHeader>
          <CardContent>
            <BenchmarkMetrics data={summary as Record<string, unknown>} />
          </CardContent>
        </Card>
      )}

      {(cfg?.pipeline_simulation as Record<string, unknown>)?.enabled || (summary?.event_stream_count != null) ? (
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Simulation</CardTitle>
            <p className="text-sm text-slate-500 mt-1">Event streams, patterns, replay settings</p>
          </CardHeader>
          <CardContent>
            <PipelineSimulationSection
              config={cfg}
              result={summary}
              runId={run.id}
              artifacts={run.artifacts}
              stageProgress={run.stage_progress}
            />
          </CardContent>
        </Card>
      ) : null}

          <Link href={`/runs/compare?left=${id}`}><Button variant="outline" size="sm">Compare with another run</Button></Link>
          <Link href="/runs"><Button variant="outline">← Back to runs</Button></Link>
    </div>
  );
}
