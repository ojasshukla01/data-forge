"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import {
  fetchRuns,
  rerunRun,
  cloneRunConfig,
  fetchStorageSummary,
  fetchCleanupPreview,
  executeCleanup,
  fetchRunMetrics,
  archiveRun,
  unarchiveRun,
  deleteRun,
  pinRun,
  unpinRun,
  type RunRecord,
  type StorageUsage,
  type CleanupPreview,
  type RunMetricsSummary,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";

function statusBadge(status: string) {
  const classes: Record<string, string> = {
    queued: "bg-slate-100 text-slate-700",
    running: "bg-blue-100 text-blue-800",
    succeeded: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
    cancelled: "bg-amber-100 text-amber-800",
  };
  return (
    <span className={cn("px-2 py-0.5 rounded text-xs font-medium", classes[status] ?? "bg-slate-100")}>
      {status}
    </span>
  );
}

export default function RunsPage() {
  const router = useRouter();
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [filterPack, setFilterPack] = useState<string>("");
  const [filterMode, setFilterMode] = useState<string>("");
  const [filterRunType, setFilterRunType] = useState<string>("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [storage, setStorage] = useState<StorageUsage | null>(null);
  const [cleanupPreview, setCleanupPreview] = useState<CleanupPreview | null>(null);
  const [cleanupModalOpen, setCleanupModalOpen] = useState(false);
  const [cleanupDeleteArtifacts, setCleanupDeleteArtifacts] = useState(false);
  const [cleanupExecuting, setCleanupExecuting] = useState(false);
  const [deleteModalRunId, setDeleteModalRunId] = useState<string | null>(null);
  const [deleteArtifacts, setDeleteArtifacts] = useState(false);
  const [metrics, setMetrics] = useState<RunMetricsSummary | null>(null);

  const loadRuns = () => {
    setLoading(true);
    setError(null);
    fetchRuns({
      status: filterStatus || undefined,
      pack: filterPack || undefined,
      mode: filterMode || undefined,
      run_type: filterRunType || undefined,
      include_archived: includeArchived,
    })
      .then((d) => setRuns(d.runs ?? []))
      .catch((e) => { setError(e instanceof Error ? e.message : "Failed"); setRuns([]); })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadRuns();
  }, [filterStatus, filterPack, filterMode, filterRunType, includeArchived]);

  const loadStorage = () => {
    fetchStorageSummary().then(setStorage).catch(() => setStorage(null));
  };
  const loadCleanupPreview = () => {
    fetchCleanupPreview().then(setCleanupPreview).catch(() => setCleanupPreview(null));
  };
  useEffect(() => {
    loadStorage();
  }, [runs.length]);
  useEffect(() => {
    fetchRunMetrics(300).then(setMetrics).catch(() => setMetrics(null));
  }, [runs.length]);

  const handleArchive = async (e: React.MouseEvent, runId: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await archiveRun(runId);
      loadRuns();
      loadStorage();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Archive failed");
    }
  };
  const handleUnarchive = async (e: React.MouseEvent, runId: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await unarchiveRun(runId);
      loadRuns();
      loadStorage();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unarchive failed");
    }
  };
  const handlePin = async (e: React.MouseEvent, runId: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await pinRun(runId);
      loadRuns();
      loadStorage();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pin failed");
    }
  };
  const handleUnpin = async (e: React.MouseEvent, runId: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await unpinRun(runId);
      loadRuns();
      loadStorage();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unpin failed");
    }
  };
  const handleDeleteClick = (e: React.MouseEvent, runId: string) => {
    e.preventDefault();
    e.stopPropagation();
    setDeleteModalRunId(runId);
    setDeleteArtifacts(false);
  };
  const handleDeleteConfirm = async () => {
    if (!deleteModalRunId) return;
    try {
      await deleteRun(deleteModalRunId, deleteArtifacts);
      setDeleteModalRunId(null);
      loadRuns();
      loadStorage();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };
  const handleCleanupOpen = () => {
    loadCleanupPreview();
    setCleanupModalOpen(true);
  };
  const handleCleanupExecute = async () => {
    setCleanupExecuting(true);
    try {
      await executeCleanup({ delete_artifacts: cleanupDeleteArtifacts });
      setCleanupModalOpen(false);
      loadRuns();
      loadStorage();
      setCleanupPreview(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cleanup failed");
    } finally {
      setCleanupExecuting(false);
    }
  };

  const handleRerun = async (e: React.MouseEvent, runId: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const res = await rerunRun(runId);
      router.push(`/runs/${res.run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rerun failed");
    }
  };

  const handleClone = async (e: React.MouseEvent, runId: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      const { config } = await cloneRunConfig(runId);
      router.push(`/create/advanced?clone=${encodeURIComponent(JSON.stringify(config))}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Clone failed");
    }
  };

  const hasFilters = Boolean(filterStatus || filterPack || filterMode || filterRunType || includeArchived);
  const activeFilterCount = [
    Boolean(filterStatus),
    Boolean(filterPack),
    Boolean(filterMode),
    Boolean(filterRunType),
    includeArchived,
  ].filter(Boolean).length;
  const clearFilters = () => {
    setFilterStatus("");
    setFilterPack("");
    setFilterMode("");
    setFilterRunType("");
    setIncludeArchived(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Runs</h1>
          <p className="mt-1.5 text-slate-600 text-sm sm:text-base">Generation and benchmark run history</p>
        </div>
        <Link href="/create/wizard">
          <Button>New run</Button>
        </Link>
      </div>

      <div className="flex gap-3 flex-wrap items-center">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="queued">Queued</option>
          <option value="running">Running</option>
          <option value="succeeded">Succeeded</option>
          <option value="failed">Failed</option>
        </select>
        <input
          type="text"
          placeholder="Filter by pack"
          value={filterPack}
          onChange={(e) => setFilterPack(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm w-40"
        />
        <select
          value={filterMode}
          onChange={(e) => setFilterMode(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">All modes</option>
          <option value="full_snapshot">Full snapshot</option>
          <option value="incremental">Incremental</option>
          <option value="cdc">CDC</option>
        </select>
        <select
          value={filterRunType}
          onChange={(e) => setFilterRunType(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">All types</option>
          <option value="generate">Generate</option>
          <option value="benchmark">Benchmark</option>
        </select>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={includeArchived}
            onChange={(e) => setIncludeArchived(e.target.checked)}
            className="rounded border-slate-300"
          />
          Include archived
        </label>
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>Clear filters</Button>
        )}
      </div>
      <p className="text-xs text-slate-500">
        Filters update automatically as you change values.
        {hasFilters && ` Active filters: ${activeFilterCount}.`}
      </p>

      {(storage || metrics) && (
        <div className="flex flex-wrap gap-4">
          {storage && (
            <Card className="bg-slate-50 border-slate-200 flex-1 min-w-0">
              <CardContent className="py-3 px-4 flex flex-wrap items-center gap-6">
                <span className="text-sm text-slate-600">
                  <strong>{storage.runs_count}</strong> runs · <strong>{storage.artifact_count}</strong> artifacts · <strong>{storage.total_size_mb}</strong> MB
                </span>
                <Button variant="outline" size="sm" onClick={handleCleanupOpen}>Cleanup preview</Button>
              </CardContent>
            </Card>
          )}
          {metrics && (
            <Card className="bg-slate-50 border-slate-200 flex-1 min-w-0">
              <CardContent className="py-3 px-4">
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Performance summary</p>
                <div className="flex flex-wrap gap-4 text-sm text-slate-700">
                  <span><strong>{metrics.total_runs}</strong> runs</span>
                  {metrics.average_duration_seconds != null && <span>Avg <strong>{metrics.average_duration_seconds}s</strong></span>}
                  {metrics.total_rows_generated > 0 && <span><strong>{metrics.total_rows_generated.toLocaleString()}</strong> rows</span>}
                  {(metrics.runs_by_status?.failed ?? 0) > 0 && <span className="text-red-600"><strong>{metrics.runs_by_status.failed}</strong> failed</span>}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {cleanupModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" aria-modal="true" role="dialog">
          <Card className="mx-4 max-w-lg w-full shadow-xl">
            <CardContent className="p-5">
              <h3 className="font-semibold text-slate-900 mb-2">Run cleanup</h3>
              <p className="text-sm text-slate-600 mb-3">
                {cleanupPreview ? (
                  <>About <strong>{cleanupPreview.candidates?.length ?? 0}</strong> run(s) would be removed by retention policy (keep last {cleanupPreview.policy?.retention_count ?? 100}, max age {cleanupPreview.policy?.retention_days ?? "—"} days). Pinned runs are never removed.</>
                ) : (
                  "Loading preview…"
                )}
              </p>
              <label className="flex items-center gap-2 text-sm text-slate-600 mb-4">
                <input
                  type="checkbox"
                  checked={cleanupDeleteArtifacts}
                  onChange={(e) => setCleanupDeleteArtifacts(e.target.checked)}
                  className="rounded border-slate-300"
                />
                Also delete artifact files (output directories)
              </label>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setCleanupModalOpen(false)} disabled={cleanupExecuting}>Cancel</Button>
                <Button onClick={handleCleanupExecute} disabled={cleanupExecuting || !cleanupPreview}>
                  {cleanupExecuting ? "Running…" : "Run cleanup"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {deleteModalRunId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" aria-modal="true" role="dialog">
          <Card className="mx-4 max-w-md w-full shadow-xl">
            <CardContent className="p-5">
              <h3 className="font-semibold text-slate-900 mb-2">Delete run</h3>
              <p className="text-sm text-slate-600 mb-3">Permanently delete run <code className="bg-slate-100 px-1 rounded">{deleteModalRunId}</code>? This cannot be undone.</p>
              <label className="flex items-center gap-2 text-sm text-slate-600 mb-4">
                <input
                  type="checkbox"
                  checked={deleteArtifacts}
                  onChange={(e) => setDeleteArtifacts(e.target.checked)}
                  className="rounded border-slate-300"
                />
                Also delete artifact files (output directory)
              </label>
              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setDeleteModalRunId(null)}>Cancel</Button>
                <Button variant="outline" className="text-red-600 border-red-200 hover:bg-red-50" onClick={handleDeleteConfirm}>Delete</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {!loading && !error && (
        <p className="text-sm text-slate-500">
          Showing {runs.length} run{runs.length !== 1 ? "s" : ""}
          {hasFilters && " (filtered by status, pack, mode, type, or archived state)"}
        </p>
      )}

      {loading ? (
        <div className="h-32 animate-pulse bg-slate-100 rounded-xl" />
      ) : error ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-red-600">{error}</p>
            <Button variant="outline" size="sm" className="mt-4" onClick={loadRuns}>
              Retry
            </Button>
          </CardContent>
        </Card>
      ) : runs.length === 0 ? (
        <Card className="border-slate-200">
          <CardContent className="py-14 px-6 text-center">
            <p className="text-slate-600 font-medium">{hasFilters ? "No runs match your filters." : "No runs yet."}</p>
            <p className="text-sm text-slate-500 mt-1">{hasFilters ? "Try clearing filters or run a new job." : "Start a generation or benchmark from Create to see runs here."}</p>
            {hasFilters ? (
              <Button variant="outline" size="sm" className="mt-5" onClick={clearFilters}>Clear filters</Button>
            ) : (
              <Link href="/create/wizard" className="mt-5 inline-block">
                <Button size="sm">Create your first run</Button>
              </Link>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {runs.map((r) => {
            const cfg = (r.config_summary ?? {}) as Record<string, unknown>;
            const packName = r.selected_pack ?? (cfg.pack as string) ?? "—";
            const rs = r.result_summary as { total_rows?: number; total_rows_generated?: number; rows_generated?: number } | undefined;
            const totalRows = rs && (typeof rs.total_rows === "number" || typeof rs.total_rows_generated === "number" || typeof rs.rows_generated === "number")
              ? (rs.total_rows ?? rs.total_rows_generated ?? rs.rows_generated ?? 0).toLocaleString()
              : "—";
            return (
              <Card key={r.id} className="hover:border-slate-300 hover:shadow-sm transition-all">
                <CardContent className="py-4">
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Link href={`/runs/${r.id}`} className="font-medium text-slate-900 font-mono text-sm hover:text-[var(--brand-teal)] hover:underline">
                          {r.id}
                        </Link>
                        {statusBadge(r.status)}
                        {r.pinned && <span className="text-xs" title="Pinned">📌</span>}
                        {r.archived_at != null && <span className="px-2 py-0.5 rounded text-xs bg-slate-200 text-slate-600">archived</span>}
                        {r.run_type === "benchmark" && (
                          <span className="px-2 py-0.5 rounded text-xs font-medium bg-[var(--brand-accent)]/10 text-[var(--brand-accent)]">Benchmark</span>
                        )}
                        {r.run_type === "generate" && (r.config_summary as { pipeline_simulation?: { enabled?: boolean } })?.pipeline_simulation?.enabled && (
                          <span className="px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">Simulation</span>
                        )}
                        {r.run_type === "generate" && !(r.config_summary as { pipeline_simulation?: { enabled?: boolean } })?.pipeline_simulation?.enabled && (
                          <span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-600">Standard</span>
                        )}
                      </div>
                      <p className="text-sm text-slate-500 mt-0.5">
                        {r.created_at ? new Date(r.created_at * 1000).toLocaleString() : "—"}
                        {r.duration_seconds != null && ` · ${r.duration_seconds}s`}
                      </p>
                      <p className="text-sm text-slate-600 mt-1">
                        Pack: {packName} · {totalRows} rows
                        {r.source_scenario_id && (
                          <> · From <Link href={`/scenarios/${r.source_scenario_id}`} className="text-[var(--brand-teal)] hover:underline">scenario</Link></>
                        )}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2 shrink-0">
                      <Link href={`/runs/${r.id}`}>
                        <Button variant="outline" size="sm">View</Button>
                      </Link>
                      <Button variant="ghost" size="sm" onClick={(e) => handleRerun(e, r.id)}>Rerun</Button>
                      <Button variant="ghost" size="sm" onClick={(e) => handleClone(e, r.id)}>Clone</Button>
                      {r.pinned ? (
                        <Button variant="ghost" size="sm" onClick={(e) => handleUnpin(e, r.id)} title="Unpin">📌</Button>
                      ) : (
                        <Button variant="ghost" size="sm" onClick={(e) => handlePin(e, r.id)} title="Pin (exclude from cleanup)">Pin</Button>
                      )}
                      {r.archived_at ? (
                        <Button variant="ghost" size="sm" onClick={(e) => handleUnarchive(e, r.id)}>Unarchive</Button>
                      ) : (
                        <Button variant="ghost" size="sm" onClick={(e) => handleArchive(e, r.id)}>Archive</Button>
                      )}
                      <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={(e) => handleDeleteClick(e, r.id)}>Delete</Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
