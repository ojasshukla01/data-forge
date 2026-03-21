"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { CodeBlock } from "@/components/ui/CodeBlock";
import { CopyButton } from "@/components/CopyButton";
import { fetchArtifacts } from "@/lib/api";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/utils";

interface Artifact {
  path: string;
  name: string;
  size: number;
  modified?: number;
  category?: string;
  type?: string;
  run_id?: string;
}

function ArtifactsContent() {
  const searchParams = useSearchParams();
  const runParam = searchParams.get("run");
  const typeParam = searchParams.get("type");
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [runs, setRuns] = useState<{ id: string; artifact_count?: number; exists?: boolean }[]>([]);
  const [runFilter, setRunFilter] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Artifact | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (runParam) setRunFilter(runParam);
  }, [runParam]);

  useEffect(() => {
    if (typeParam && typeParam !== "all") setCategoryFilter(typeParam);
  }, [typeParam]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchArtifacts(runFilter ?? runParam ?? undefined)
      .then((data: { artifacts: Artifact[]; runs?: { id: string; artifact_count?: number; exists?: boolean }[] }) => {
        setArtifacts(data.artifacts ?? []);
        setRuns(data.runs ?? []);
      })
      .catch((e) => { setError(e instanceof Error ? e.message : "Failed"); setArtifacts([]); setRuns([]); })
      .finally(() => setLoading(false));
  }, [runFilter, runParam, reloadToken]);

  const filtered = artifacts.filter((a) => {
    const t = a.type ?? a.category ?? "dataset";
    if (categoryFilter !== "all" && t !== categoryFilter) return false;
    if (search && !a.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const rawCategories = Array.from(new Set(artifacts.map((a) => a.type ?? a.category ?? "dataset")));
  const categories = ["all", ...rawCategories];
  const hasActiveFilters = Boolean((runFilter ?? runParam ?? "") || categoryFilter !== "all" || search.trim());
  const TYPE_LABELS: Record<string, string> = {
    dataset: "Dataset",
    sql: "SQL",
    parquet: "Parquet",
    csv: "CSV",
    event_stream: "Event stream",
    unstructured: "Linked notes",
    pipeline_snapshot: "Pipeline snapshot",
    benchmark_profile: "Benchmark profile",
    contract: "Contract",
    manifest: "Manifest",
    dbt: "dbt",
    ge: "Great Expectations",
    airflow: "Airflow",
  };

  const loadPreview = (a: Artifact) => {
    setSelected(a);
    setPreview(null);
    const runId = a.run_id ?? runFilter ?? runs[0]?.id;
    if (!runId) return;
    const url = `${API_BASE}/api/artifacts/file?run_id=${encodeURIComponent(runId)}&path=${encodeURIComponent(a.path)}`;
    fetch(url)
      .then((r) => r.text())
      .then((text) => {
        if (text.length > 50000) {
          setPreview(`(File too large to preview: ${(text.length / 1024).toFixed(0)} KB)`);
          return;
        }
        if (a.name.endsWith(".json") || a.path.endsWith(".json")) {
          try {
            const parsed = JSON.parse(text);
            setPreview(JSON.stringify(parsed, null, 2));
          } catch {
            setPreview(text);
          }
        } else {
          setPreview(text);
        }
      })
      .catch(() => setPreview("(Preview unavailable)"));
  };

  const downloadUrl = selected && (selected.run_id ?? runFilter ?? runs[0]?.id)
    ? `${API_BASE}/api/artifacts/file?run_id=${encodeURIComponent(selected.run_id ?? runFilter ?? runs[0]!.id)}&path=${encodeURIComponent(selected.path)}`
    : null;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Artifacts</h1>
          <p className="mt-1.5 text-slate-600 text-sm sm:text-base">Browse datasets, event streams, contracts, manifests, dbt seeds, GE suites, and DAGs</p>
        </div>
        <Link href="/create/wizard"><Button variant="outline" size="sm">New run</Button></Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-3 gap-4 h-64 animate-pulse bg-slate-100 rounded-xl" />
      ) : error ? (
        <Card className="border-red-200 bg-red-50/50">
          <CardContent className="pt-6">
            <p className="text-red-700">{error}</p>
            <Button variant="outline" size="sm" className="mt-4" onClick={() => setReloadToken((v) => v + 1)}>Retry</Button>
          </CardContent>
        </Card>
      ) : artifacts.length === 0 ? (
        <Card className="border-slate-200">
          <CardContent className="py-14 px-6 text-center">
            <p className="text-slate-600 font-medium">No artifacts found</p>
            <p className="text-sm text-slate-500 mt-1">Run a generation or benchmark to create datasets and artifacts. Filter by run if you have runs with outputs.</p>
            <Link href="/create/wizard"><Button size="sm" className="mt-5">Create a run</Button></Link>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-600">
            Showing {filtered.length} of {artifacts.length} artifact{artifacts.length === 1 ? "" : "s"}
          </div>
          <div className="flex gap-4 flex-wrap">
            <select
              value={runFilter ?? runParam ?? ""}
              onChange={(e) => setRunFilter(e.target.value || null)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              <option value="">All runs</option>
              {runs.map((r) => (
                <option key={r.id} value={r.id}>{r.id} ({r.artifact_count ?? 0} files)</option>
              ))}
            </select>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {categories.map((c) => (
                <option key={c} value={c}>{c === "all" ? "All types" : TYPE_LABELS[c] ?? c}</option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Search by name"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm w-48"
            />
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setRunFilter(null);
                  setCategoryFilter("all");
                  setSearch("");
                }}
              >
                Clear filters
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>Files</CardTitle>
              </CardHeader>
              <CardContent>
                {filtered.length === 0 ? (
                  <p className="text-sm text-slate-500">
                    No artifacts match the current filters.
                  </p>
                ) : (
                  <div className="space-y-1 max-h-[400px] overflow-y-auto">
                    {filtered.map((a) => (
                      <button
                        key={a.path + (a.run_id ?? "")}
                        onClick={() => loadPreview(a)}
                        className={cn(
                          "w-full text-left px-3 py-2 rounded-lg text-sm truncate flex justify-between items-center gap-2",
                          selected?.path === a.path ? "bg-slate-200 font-medium" : "hover:bg-slate-100"
                        )}
                      >
                        <span className="truncate">{a.name}</span>
                        <span className="shrink-0 text-slate-400 text-xs">{formatSize(a.size ?? 0)}</span>
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Preview</CardTitle>
                {selected && (
                  <div className="mt-3 p-4 rounded-lg border border-slate-200 bg-slate-50">
                    <p className="text-xs font-medium text-slate-500 mb-3">File metadata</p>
                    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                      <dt className="text-slate-500">File type</dt>
                      <dd className="font-mono text-slate-900">{selected.type ?? selected.category ?? "dataset"}</dd>
                      <dt className="text-slate-500">File size</dt>
                      <dd className="font-mono tabular-nums text-slate-900">{formatSize(selected.size ?? 0)}</dd>
                      <dt className="text-slate-500">Created</dt>
                      <dd className="font-mono text-xs text-slate-900">
                        {selected.modified != null ? new Date(selected.modified * 1000).toLocaleString() : "—"}
                      </dd>
                      <dt className="text-slate-500">Run ID</dt>
                      <dd>
                        {selected.run_id ? (
                          <Link href={`/runs/${selected.run_id}`} className="font-mono text-[var(--brand-teal)] hover:underline text-xs">
                            {selected.run_id}
                          </Link>
                        ) : (
                          "—"
                        )}
                      </dd>
                    </dl>
                    <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-slate-200">
                      <CopyButton text={selected.path} label="Copy path" title="Copy artifact path" />
                      {downloadUrl && (
                        <a href={downloadUrl} download={selected.name}>
                          <Button variant="outline" size="sm">Download</Button>
                        </a>
                      )}
                    </div>
                  </div>
                )}
              </CardHeader>
              <CardContent>
                {!selected ? (
                  <p className="text-slate-500 text-sm">Select a file to preview</p>
                ) : preview === null ? (
                  <p className="text-slate-500 text-sm">Loading…</p>
                ) : (
                  <div className="max-h-96 overflow-auto rounded-lg border border-slate-200">
                    {(selected.name.endsWith(".json") || selected.path.endsWith(".json")) && typeof preview === "string" && !preview.startsWith("(File too large") ? (
                      <CodeBlock copyable className="font-mono text-code">{preview}</CodeBlock>
                    ) : (
                      <pre className="p-4 bg-slate-900 text-xs overflow-auto max-h-96 font-mono text-slate-100 whitespace-pre-wrap break-words text-code">
                        {preview}
                      </pre>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}

      <Link href="/validate"><Button variant="ghost" size="sm">Validation Center</Button></Link>
    </div>
  );
}

export default function ArtifactsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-slate-500">Loading…</div>}>
      <ArtifactsContent />
    </Suspense>
  );
}
