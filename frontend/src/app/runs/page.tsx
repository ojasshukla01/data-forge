"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { fetchRuns, rerunRun, cloneRunConfig, type RunRecord } from "@/lib/api";
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

  const loadRuns = () => {
    setLoading(true);
    setError(null);
    fetchRuns({
      status: filterStatus || undefined,
      pack: filterPack || undefined,
      mode: filterMode || undefined,
      run_type: filterRunType || undefined,
    })
      .then((d) => setRuns(d.runs ?? []))
      .catch((e) => { setError(e instanceof Error ? e.message : "Failed"); setRuns([]); })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadRuns();
  }, [filterStatus, filterPack, filterMode, filterRunType]);

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

  const hasFilters = filterStatus || filterPack || filterMode || filterRunType;
  const clearFilters = () => {
    setFilterStatus("");
    setFilterPack("");
    setFilterMode("");
    setFilterRunType("");
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Runs</h1>
          <p className="mt-1 text-slate-600">Generation and benchmark run history</p>
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
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>Clear filters</Button>
        )}
      </div>

      {!loading && !error && (
        <p className="text-sm text-slate-500">
          Showing {runs.length} run{runs.length !== 1 ? "s" : ""}
          {hasFilters && " (filtered by status, pack, mode, or type)"}
        </p>
      )}

      {loading ? (
        <div className="h-32 animate-pulse bg-slate-100 rounded-xl" />
      ) : error ? (
        <Card>
          <CardContent className="py-8 text-center text-red-600">{error}</CardContent>
        </Card>
      ) : runs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-slate-500">
            <p>{hasFilters ? "No runs match your filters." : "No runs yet."}</p>
            {hasFilters ? (
              <Button variant="outline" size="sm" className="mt-4" onClick={clearFilters}>Clear filters</Button>
            ) : (
              <Link href="/create/wizard" className="mt-4 inline-block text-slate-900 font-medium hover:underline">
                Create your first dataset →
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
                    <Link href={`/runs/${r.id}`} className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-medium text-slate-900 font-mono text-sm">{r.id}</p>
                        {statusBadge(r.status)}
                        {r.run_type === "benchmark" && (
                          <span className="px-2 py-0.5 rounded text-xs font-medium bg-[var(--brand-accent)]/10 text-[var(--brand-accent)]">benchmark</span>
                        )}
                      </div>
                      <p className="text-sm text-slate-500 mt-0.5">
                        {r.created_at ? new Date(r.created_at * 1000).toLocaleString() : "—"}
                        {r.duration_seconds != null && ` · ${r.duration_seconds}s`}
                      </p>
                      <p className="text-sm text-slate-600 mt-1">
                        Pack: {packName} · {totalRows} rows
                      </p>
                    </Link>
                    <div className="flex gap-2 shrink-0">
                      <Link href={`/runs/${r.id}`}>
                        <Button variant="outline" size="sm">View</Button>
                      </Link>
                      <Button variant="ghost" size="sm" onClick={(e) => handleRerun(e, r.id)}>Rerun</Button>
                      <Button variant="ghost" size="sm" onClick={(e) => handleClone(e, r.id)}>Clone</Button>
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
