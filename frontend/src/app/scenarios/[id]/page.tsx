"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import {
  fetchScenario,
  fetchRuns,
  runFromScenario,
  deleteScenario,
  exportScenario,
  updateScenario,
  fetchScenarioVersions,
  fetchScenarioDiff,
  type ScenarioRecord,
  type ScenarioVersionsResponse,
  type ScenarioDiffResponse,
} from "@/lib/api";
import { cn } from "@/lib/utils";

function formatLabel(s: string): string {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ScenarioDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;
  const [scenario, setScenario] = useState<ScenarioRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runLoading, setRunLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [exportFeedback, setExportFeedback] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editCategory, setEditCategory] = useState("custom");
  const [editTags, setEditTags] = useState("");
  const [saveMetadataLoading, setSaveMetadataLoading] = useState(false);
  const [saveMetadataError, setSaveMetadataError] = useState<string | null>(null);
  const [saveMetadataSuccess, setSaveMetadataSuccess] = useState(false);
  const [runsFromScenario, setRunsFromScenario] = useState<{ id: string; status: string }[]>([]);
  // Scenario history and diff
  const [versions, setVersions] = useState<ScenarioVersionsResponse | null>(null);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [versionsError, setVersionsError] = useState<string | null>(null);
  const [diffLeft, setDiffLeft] = useState<number | "">("");
  const [diffRight, setDiffRight] = useState<number | "">("");
  const [diffResult, setDiffResult] = useState<ScenarioDiffResponse | null>(null);
  const [diffLoading, setDiffLoading] = useState(false);
  const [diffError, setDiffError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    fetchScenario(id)
      .then((s) => {
        setScenario(s ?? null);
        if (s) {
          setEditName(s.name);
          setEditDescription(s.description ?? "");
          setEditCategory(s.category ?? "custom");
          setEditTags((s.tags ?? []).join(", "));
        }
      })
      .catch((e) => { setError(e instanceof Error ? e.message : "Failed"); setScenario(null); })
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    fetchRuns({ source_scenario_id: id, limit: 20 })
      .then((d) => setRunsFromScenario(d.runs ?? []))
      .catch(() => setRunsFromScenario([]));
  }, [id]);

  useEffect(() => {
    if (!id) return;
    setVersionsLoading(true);
    setVersionsError(null);
    fetchScenarioVersions(id)
      .then((v) => {
        setVersions(v ?? null);
        if (v?.versions?.length && diffLeft === "" && diffRight === "") {
          const oldest = v.versions.length > 1 ? (v.versions[v.versions.length - 1]?.version ?? v.current_version) : v.current_version;
          setDiffLeft(oldest);
          setDiffRight(v.current_version);
        }
      })
      .catch((e) => { setVersionsError(e instanceof Error ? e.message : "Failed to load versions"); setVersions(null); })
      .finally(() => setVersionsLoading(false));
  }, [id]);

  const loadDiff = () => {
    if (!id || diffLeft === "" || diffRight === "" || diffLeft === diffRight) {
      setDiffResult(null);
      setDiffError(diffLeft === diffRight && diffLeft !== "" ? "Choose two different versions" : null);
      return;
    }
    setDiffLoading(true);
    setDiffError(null);
    setDiffResult(null);
    fetchScenarioDiff(id, Number(diffLeft), Number(diffRight))
      .then((d) => { setDiffResult(d ?? null); if (!d) setDiffError("Could not compute diff"); })
      .catch((e) => { setDiffError(e instanceof Error ? e.message : "Diff failed"); setDiffResult(null); })
      .finally(() => setDiffLoading(false));
  };

  const handleRun = async () => {
    if (!scenario) return;
    setRunLoading(true);
    try {
      const res = await runFromScenario(scenario.id);
      router.push(`/runs/${res.run_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Run failed");
    } finally {
      setRunLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!scenario || !confirm(`Delete scenario "${scenario.name}"? This cannot be undone.`)) return;
    setDeleteLoading(true);
    try {
      await deleteScenario(scenario.id);
      router.push("/scenarios");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleSaveMetadata = async () => {
    if (!scenario) return;
    const name = editName.trim();
    if (!name) {
      setSaveMetadataError("Name is required");
      return;
    }
    setSaveMetadataLoading(true);
    setSaveMetadataError(null);
    setSaveMetadataSuccess(false);
    try {
      const updated = await updateScenario(scenario.id, {
        name,
        description: editDescription.trim(),
        category: editCategory,
        tags: editTags.split(",").map((t) => t.trim()).filter(Boolean),
      });
      setScenario(updated);
      setEditMode(false);
      setSaveMetadataSuccess(true);
      setTimeout(() => setSaveMetadataSuccess(false), 3000);
    } catch (e) {
      setSaveMetadataError(e instanceof Error ? e.message : "Failed to update");
    } finally {
      setSaveMetadataLoading(false);
    }
  };

  const handleExport = async () => {
    if (!scenario) return;
    try {
      const data = await exportScenario(scenario.id);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `scenario-${scenario.id}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
      setExportFeedback(true);
      setTimeout(() => setExportFeedback(false), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-64 bg-slate-200 rounded animate-pulse" />
        <div className="h-64 bg-slate-100 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (error || !scenario) {
    return (
      <div className="space-y-6">
        <p className="text-red-600">{error ?? "Scenario not found"}</p>
        <Link href="/scenarios"><Button variant="outline">← Back to scenarios</Button></Link>
      </div>
    );
  }

  const cfg = (scenario.config || {}) as Record<string, unknown>;
  const ps = (cfg.pipeline_simulation || {}) as Record<string, unknown>;
  const bench = (cfg.benchmark || {}) as Record<string, unknown>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{scenario.name}</h1>
          {scenario.description && <p className="mt-1 text-slate-600">{scenario.description}</p>}
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge variant="category">{scenario.category}</Badge>
            {scenario.source_pack && <Badge variant="category">{scenario.source_pack}</Badge>}
            {scenario.uses_pipeline_simulation && <Badge variant="category">Pipeline simulation</Badge>}
            {scenario.uses_benchmark && <Badge variant="category">Benchmark</Badge>}
            {Boolean(cfg.privacy_mode && String(cfg.privacy_mode).toLowerCase() !== "off") && (
              <Badge variant="category">Privacy</Badge>
            )}
            {Boolean(cfg.export_dbt || cfg.export_ge || cfg.export_airflow) && (
              <Badge variant="category">Integrations</Badge>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" onClick={handleRun} disabled={runLoading}>
            {runLoading ? "Starting…" : "Run scenario"}
          </Button>
          <Button variant="outline" size="sm" onClick={() => setEditMode(!editMode)}>
            {editMode ? "Cancel edit" : "Edit metadata"}
          </Button>
          <Link href={`/create/advanced?scenario=${scenario.id}`}>
            <Button variant="outline" size="sm">Edit in Advanced Config</Button>
          </Link>
          <Link href={`/create/wizard?scenario=${scenario.id}`}>
            <Button variant="outline" size="sm">Start in wizard</Button>
          </Link>
          <Button variant="outline" size="sm" onClick={handleExport}>
            {exportFeedback ? "Copied!" : "Export JSON"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleDelete} className="text-red-600" disabled={deleteLoading}>
            {deleteLoading ? "Deleting…" : "Delete"}
          </Button>
        </div>
      </div>

      {scenario.has_masked_sensitive_fields && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-amber-800 text-sm">
          <p className="font-medium">Some sensitive connection values were not preserved and must be re-entered before running.</p>
          {scenario.masked_fields && scenario.masked_fields.length > 0 && (
            <p className="mt-1 text-amber-700">Fields: {scenario.masked_fields.join(", ")}</p>
          )}
        </div>
      )}

      {(saveMetadataError || saveMetadataSuccess) && (
        <div className={saveMetadataSuccess ? "rounded-lg bg-green-50 border border-green-200 px-4 py-2 text-green-800 text-sm" : "rounded-lg bg-red-50 border border-red-200 px-4 py-2 text-red-800 text-sm"}>
          {saveMetadataSuccess ? "Metadata saved." : saveMetadataError}
        </div>
      )}

      {editMode && (
        <Card className="border-[var(--brand-teal)]/30">
          <CardHeader>
            <CardTitle className="text-base">Edit metadata</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                placeholder="Scenario name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
              <input
                type="text"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                placeholder="Optional description"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
              <select
                value={editCategory}
                onChange={(e) => setEditCategory(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                <option value="quick_start">Quick start</option>
                <option value="testing">Testing</option>
                <option value="pipeline_simulation">Pipeline simulation</option>
                <option value="warehouse_benchmark">Warehouse benchmark</option>
                <option value="privacy_uat">Privacy UAT</option>
                <option value="contracts">Contracts</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Tags (comma-separated)</label>
              <input
                type="text"
                value={editTags}
                onChange={(e) => setEditTags(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                placeholder="e.g. ecommerce, demo"
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSaveMetadata} disabled={saveMetadataLoading}>
                {saveMetadataLoading ? "Saving…" : "Save"}
              </Button>
              <Button variant="outline" size="sm" onClick={() => setEditMode(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {scenario.created_from_run_id && (
        <p className="text-sm text-slate-600">
          Derived from run: <Link href={`/runs/${scenario.created_from_run_id}`} className="text-[var(--brand-teal)] hover:underline">{scenario.created_from_run_id}</Link>
        </p>
      )}
      {scenario.created_from_scenario_id && (
        <p className="text-sm text-slate-600">
          Saved as new from scenario: <Link href={`/scenarios/${scenario.created_from_scenario_id}`} className="text-[var(--brand-teal)] hover:underline">{scenario.created_from_scenario_id}</Link>
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Config summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-slate-500">Pack</span><span className="font-mono">{cfg.pack != null ? String(cfg.pack) : "—"}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Mode</span><span>{cfg.mode != null ? formatLabel(String(cfg.mode)) : "—"}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Layer</span><span>{cfg.layer != null ? String(cfg.layer) : "—"}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Scale</span><span>{cfg.scale != null ? String(cfg.scale) : "—"}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Messiness</span><span>{cfg.messiness != null ? String(cfg.messiness) : "—"}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Export</span><span>{cfg.export_format != null ? String(cfg.export_format) : "—"}</span></div>
          </CardContent>
        </Card>

        {Boolean(ps.enabled || bench.enabled) && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Simulation & benchmark</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {Boolean(ps.enabled) && (
                <>
                  <div className="flex justify-between"><span className="text-slate-500">Event pattern</span><span>{ps.event_pattern != null ? String(ps.event_pattern) : "—"}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Event density</span><span>{ps.event_density != null ? String(ps.event_density) : "—"}</span></div>
                </>
              )}
              {Boolean(bench.enabled) && (
                <>
                  <div className="flex justify-between"><span className="text-slate-500">Profile</span><span>{bench.profile != null ? String(bench.profile) : "—"}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Scale preset</span><span>{bench.scale_preset != null ? String(bench.scale_preset) : "—"}</span></div>
                </>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {runsFromScenario.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Runs from this scenario</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="text-sm space-y-1">
              {runsFromScenario.slice(0, 10).map((r) => (
                <li key={r.id}>
                  <Link href={`/runs/${r.id}`} className="text-[var(--brand-teal)] hover:underline font-mono">{r.id}</Link>
                  <span className="text-slate-500 ml-2">{r.status}</span>
                </li>
              ))}
              {runsFromScenario.length > 10 && <li className="text-slate-500">… and {runsFromScenario.length - 10} more</li>}
            </ul>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Metadata</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-600">
          Created {scenario.created_at ? new Date(scenario.created_at * 1000).toLocaleString() : "—"} · 
          Updated {scenario.updated_at ? new Date(scenario.updated_at * 1000).toLocaleString() : "—"}
          {scenario.tags && scenario.tags.length > 0 && (
            <> · Tags: {scenario.tags.join(", ")}</>
          )}
        </CardContent>
      </Card>

      {/* Scenario History */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Version history</CardTitle>
          <p className="text-sm text-slate-500 mt-1">Config changes are versioned. Compare any two versions below.</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {versionsLoading && <p className="text-sm text-slate-500">Loading versions…</p>}
          {versionsError && <p className="text-sm text-red-600" role="alert">{versionsError}</p>}
          {!versionsLoading && !versionsError && versions && (
            <>
              {!(versions.versions && versions.versions.length > 0) ? (
                <p className="text-sm text-slate-500">No version history yet. Update the scenario config to create versions.</p>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-slate-600">Current version: <strong>v{versions.current_version ?? 1}</strong></p>
                  <ul className="text-sm space-y-1.5" aria-label="Scenario versions">
                    {(versions.versions ?? []).map((v) => (
                      <li key={v.version} className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium">v{v.version}</span>
                        {v.updated_at != null && (
                          <span className="text-slate-500">{new Date(v.updated_at * 1000).toLocaleString()}</span>
                        )}
                        {v.version === versions.current_version && (
                          <Badge variant="category">current</Badge>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {(versions.versions?.length ?? 0) >= 2 && (
                <div className="pt-4 border-t border-slate-200 space-y-3">
                  <h3 className="text-sm font-semibold text-slate-900">Compare versions</h3>
                  <div className="flex flex-wrap items-center gap-2">
                    <label className="text-sm text-slate-600">Left</label>
                    <select
                      value={diffLeft === "" ? "" : String(diffLeft)}
                      onChange={(e) => setDiffLeft(e.target.value === "" ? "" : Number(e.target.value))}
                      className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
                      aria-label="Left version"
                    >
                      {(versions.versions ?? []).map((v) => (
                        <option key={v.version} value={v.version}>v{v.version}</option>
                      ))}
                    </select>
                    <label className="text-sm text-slate-600">Right</label>
                    <select
                      value={diffRight === "" ? "" : String(diffRight)}
                      onChange={(e) => setDiffRight(e.target.value === "" ? "" : Number(e.target.value))}
                      className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
                      aria-label="Right version"
                    >
                      {(versions.versions ?? []).map((v) => (
                        <option key={v.version} value={v.version}>v{v.version}</option>
                      ))}
                    </select>
                    <Button size="sm" onClick={loadDiff} disabled={diffLoading || diffLeft === diffRight}>
                      {diffLoading ? "Loading…" : "Show diff"}
                    </Button>
                  </div>
                  {diffError && <p className="text-sm text-red-600" role="alert">{diffError}</p>}
                  {diffResult && (
                    <div className="rounded-lg border border-slate-200 bg-slate-50/50 p-4 space-y-2">
                      <p className="text-sm font-medium text-slate-900">
                        Changes from v{diffResult.left_version} → v{diffResult.right_version}
                      </p>
                      {diffResult.changed.length === 0 ? (
                        <p className="text-sm text-slate-500">No config differences.</p>
                      ) : (
                        <ul className="text-sm space-y-2" role="list">
                          {diffResult.changed.map((c, i) => (
                            <li key={i} className="flex flex-wrap gap-x-2 gap-y-1 items-baseline border-b border-slate-200 pb-2 last:border-0 last:pb-0">
                              <span className="font-mono text-slate-700 shrink-0">{c.key}</span>
                              <span className="text-slate-500">old:</span>
                              <code className="text-xs bg-red-50 text-red-800 px-1 rounded break-all">
                                {typeof c.left === "object" ? JSON.stringify(c.left) : String(c.left ?? "—")}
                              </code>
                              <span className="text-slate-500">new:</span>
                              <code className="text-xs bg-green-50 text-green-800 px-1 rounded break-all">
                                {typeof c.right === "object" ? JSON.stringify(c.right) : String(c.right ?? "—")}
                              </code>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <Link href="/scenarios"><Button variant="outline">← Back to scenarios</Button></Link>
    </div>
  );
}
