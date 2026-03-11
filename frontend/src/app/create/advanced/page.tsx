"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { fetchPacks, fetchCustomSchemas, runPreflight, startRunGenerate, runBenchmark, startBenchmarkRun, fetchScenario, createScenario, updateScenario } from "@/lib/api";
import { cn } from "@/lib/utils";

const SECTIONS = [
  { id: "schema", label: "Schema & Input" },
  { id: "rules", label: "Rules" },
  { id: "generation", label: "Generation" },
  { id: "etl", label: "ETL Realism" },
  { id: "simulation", label: "Pipeline Simulation" },
  { id: "privacy", label: "Privacy" },
  { id: "contracts", label: "Contracts" },
  { id: "exports", label: "Exports" },
  { id: "load", label: "Database Load" },
  { id: "validation", label: "Validation" },
  { id: "dbt", label: "dbt / GE / Airflow" },
  { id: "benchmark", label: "Benchmark / Performance" },
  { id: "raw", label: "Raw Config" },
];

const DEFAULT_CONFIG: Record<string, unknown> = {
  pack: null,
  custom_schema_id: null,
  schema_path: null,
  rules_path: null,
  seed: 42,
  scale: 1000,
  include_anomalies: false,
  anomaly_ratio: 0.02,
  mode: "full_snapshot",
  layer: "bronze",
  drift_profile: "none",
  messiness: "clean",
  privacy_mode: "warn",
  export_format: "parquet",
  load_target: null,
  db_uri: null,
  chunk_size: null,
  batch_size: 1000,
  export_ge: false,
  ge_dir: null,
  export_airflow: false,
  airflow_dir: null,
  export_dbt: false,
  dbt_dir: null,
  contracts: false,
  write_manifest: false,
  change_ratio: 0.1,
  pipeline_simulation: { enabled: false, event_density: "medium", event_pattern: "steady", replay_mode: "ordered", late_arrival_ratio: 0 },
  benchmark: { enabled: false, profile: null, scale_preset: null, parallel_tables: 1, batch_size: 1000, iterations: 3 },
};

const MASKED = "***";

function AdvancedConfigContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [section, setSection] = useState("schema");
  const [config, setConfig] = useState<Record<string, unknown>>(DEFAULT_CONFIG);
  const [packs, setPacks] = useState<{ id: string; description: string }[]>([]);
  const [customSchemas, setCustomSchemas] = useState<{ id: string; name: string }[]>([]);
  const [preflight, setPreflight] = useState<Record<string, unknown> | null>(null);
  const [preflightLoading, setPreflightLoading] = useState(false);
  const [runLoading, setRunLoading] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState<Record<string, unknown> | null>(null);
  const [benchmarkRunLoading, setBenchmarkRunLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveScenarioLoading, setSaveScenarioLoading] = useState(false);
  const [saveScenarioOpen, setSaveScenarioOpen] = useState(false);
  const [saveScenarioName, setSaveScenarioName] = useState("");
  const [saveScenarioDesc, setSaveScenarioDesc] = useState("");
  const [saveScenarioCategory, setSaveScenarioCategory] = useState("custom");
  const [maskedFields, setMaskedFields] = useState<string[] | null>(null);
  const [loadedScenarioId, setLoadedScenarioId] = useState<string | null>(null);
  const [loadedScenarioName, setLoadedScenarioName] = useState<string | null>(null);
  const [updateScenarioConfirm, setUpdateScenarioConfirm] = useState(false);
  const [updateScenarioLoading, setUpdateScenarioLoading] = useState(false);

  const hasMaskedCredentials = !!maskedFields?.length;

  useEffect(() => {
    fetchPacks().then(setPacks).catch(() => setPacks([]));
  }, []);
  useEffect(() => {
    fetchCustomSchemas()
      .then((s) => setCustomSchemas(Array.isArray(s) ? s : []))
      .catch(() => setCustomSchemas([]));
  }, []);

  // Clone prefill: read ?clone= JSON from URL and prefill config
  useEffect(() => {
    const cloneRaw = searchParams.get("clone");
    const maskedParam = searchParams.get("masked");
    if (!cloneRaw) {
      if (!searchParams.get("clone")) setMaskedFields(null);
      return;
    }
    try {
      const parsed = JSON.parse(decodeURIComponent(cloneRaw)) as Record<string, unknown>;
      if (!parsed || typeof parsed !== "object") return;
      const masked: string[] = [];
      const collectMasked = (obj: unknown, prefix = ""): void => {
        if (!obj || typeof obj !== "object" || Array.isArray(obj)) return;
        for (const [k, v] of Object.entries(obj)) {
          if (v === MASKED) masked.push(prefix ? `${prefix}.${k}` : k);
          else if (v && typeof v === "object" && !Array.isArray(v)) collectMasked(v, prefix ? `${prefix}.${k}` : k);
        }
      };
      collectMasked(parsed);
      if (!masked.length && maskedParam) {
        try { const names = JSON.parse(decodeURIComponent(maskedParam)); if (Array.isArray(names)) masked.push(...names); } catch { /* ignore */ }
      }
      const merged: Record<string, unknown> = { ...DEFAULT_CONFIG };
      for (const [k, v] of Object.entries(parsed)) {
        if (v === MASKED) continue;
        merged[k] = v;
      }
      if (merged.pack == null && parsed.selected_pack) merged.pack = parsed.selected_pack;
      setConfig(merged);
      setMaskedFields(masked.length ? masked : null);
    } catch {
      setError("Invalid clone payload");
      setMaskedFields(null);
    }
  }, [searchParams]);

  // Scenario prefill: read ?scenario=<id> and load scenario config
  useEffect(() => {
    const scenarioId = searchParams.get("scenario");
    if (!scenarioId) {
      if (!searchParams.get("scenario")) { setMaskedFields(null); setLoadedScenarioId(null); setLoadedScenarioName(null); }
      return;
    }
    fetchScenario(scenarioId)
      .then((s) => {
        if (s?.config) {
          const merged: Record<string, unknown> = { ...DEFAULT_CONFIG };
          for (const [k, v] of Object.entries(s.config)) {
            if (v === MASKED) continue;
            merged[k] = v;
          }
          setConfig(merged);
          setMaskedFields(s.has_masked_sensitive_fields && s.masked_fields?.length ? s.masked_fields : null);
          setLoadedScenarioId(s.id);
          setLoadedScenarioName(s.name);
        }
      })
      .catch(() => { setError("Failed to load scenario"); setMaskedFields(null); setLoadedScenarioId(null); setLoadedScenarioName(null); });
  }, [searchParams]);

  const update = (key: string, value: unknown) => setConfig((c) => ({ ...c, [key]: value }));

  const runPreflightCheck = async () => {
    setPreflightLoading(true);
    setPreflight(null);
    setError(null);
    try {
      const data = await runPreflight(config);
      setPreflight(data);
    } catch (e) {
      setPreflight({ valid: false, blockers: [e instanceof Error ? e.message : "Preflight failed"] });
    } finally {
      setPreflightLoading(false);
    }
  };

  const handleRun = async () => {
    setRunLoading(true);
    setError(null);
    try {
      const res = await startRunGenerate(config);
      router.push(`/runs/${res.run_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Run failed");
    } finally {
      setRunLoading(false);
    }
  };

  const exportConfig = () => {
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "data-forge-config.json";
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const importConfig = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "application/json";
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      const r = new FileReader();
      r.onload = () => {
        try {
          const parsed = JSON.parse(r.result as string);
          setConfig({ ...DEFAULT_CONFIG, ...parsed });
        } catch {
          setError("Invalid JSON");
        }
      };
      r.readAsText(file);
    };
    input.click();
  };

  const blockers = (preflight?.blockers as string[]) ?? [];
  const valid = preflight && (preflight.valid === true) && blockers.length === 0;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Advanced Configuration</h1>
          <p className="mt-1 text-slate-600">Expert workspace for full control over generation settings</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={exportConfig} aria-label="Export config">Export</Button>
          <Button variant="outline" size="sm" onClick={importConfig}>Import</Button>
          <Link href="/create/wizard"><Button variant="ghost" size="sm">Use wizard</Button></Link>
        </div>
      </div>

      {loadedScenarioId && loadedScenarioName && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
          <p className="font-medium text-slate-800">Loaded scenario: {loadedScenarioName}</p>
          <p className="text-slate-600 mt-1">You can update this scenario or save as a new one below. Updating will overwrite the existing scenario.</p>
        </div>
      )}

      {hasMaskedCredentials && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-amber-800 text-sm">
          <p className="font-medium">Some sensitive connection values were not preserved and must be re-entered before running this configuration.</p>
          {maskedFields && maskedFields.length > 0 && (
            <p className="mt-1 text-amber-700">Fields to update: {maskedFields.join(", ")}</p>
          )}
        </div>
      )}

      <div className="flex gap-4 flex-wrap border-b border-slate-200 pb-2">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            onClick={() => setSection(s.id)}
            className={cn(
              "px-3 py-2 rounded-lg text-sm font-medium",
              section === s.id ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            )}
          >
            {s.label}
          </button>
        ))}
      </div>

      <Card>
        <CardContent className="pt-6 space-y-6">
          {section === "schema" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Schema & Input</h3>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Pack</label>
                <select
                  value={(config.pack as string) || ""}
                  onChange={(e) => update("pack", e.target.value || null)}
                  className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="">Select pack</option>
                  {packs.map((p) => (
                    <option key={p.id} value={p.id}>{p.id}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Custom schema (from Schema Studio)</label>
                <select
                  value={(config.custom_schema_id as string) || ""}
                  onChange={(e) => update("custom_schema_id", e.target.value || null)}
                  className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="">None</option>
                  {(customSchemas ?? []).map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
                <p className="text-xs text-slate-500 mt-1">Use a schema from Schema Studio when pack is empty or as override</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Schema path (optional)</label>
                <input
                  type="text"
                  value={(config.schema_path as string) ?? ""}
                  onChange={(e) => update("schema_path", e.target.value || null)}
                  placeholder="schemas/custom.sql"
                  className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Rules path</label>
                <input
                  type="text"
                  value={(config.rules_path as string) ?? ""}
                  onChange={(e) => update("rules_path", e.target.value || null)}
                  placeholder="rules/custom.yaml"
                  className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
          )}

          {section === "rules" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Rules</h3>
              <p className="text-sm text-slate-600">Rules are loaded from the rules path. Use YAML or JSON format.</p>
            </div>
          )}

          {section === "generation" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Generation</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Seed</label>
                  <input
                    type="number"
                    value={config.seed as number}
                    onChange={(e) => update("seed", parseInt(e.target.value, 10) || 42)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Scale (rows per table hint)</label>
                  <input
                    type="number"
                    value={config.scale as number}
                    onChange={(e) => update("scale", parseInt(e.target.value, 10) || 1000)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={!!config.include_anomalies}
                      onChange={(e) => update("include_anomalies", e.target.checked)}
                    />
                    <span className="text-sm">Include anomalies</span>
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Anomaly ratio</label>
                  <input
                    type="number"
                    step="0.01"
                    value={config.anomaly_ratio as number}
                    onChange={(e) => update("anomaly_ratio", parseFloat(e.target.value) || 0.02)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
            </div>
          )}

          {section === "etl" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">ETL Realism</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Mode</label>
                  <select
                    value={(config.mode as string) ?? "full_snapshot"}
                    onChange={(e) => update("mode", e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="full_snapshot">Full snapshot</option>
                    <option value="incremental">Incremental</option>
                    <option value="cdc">CDC</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Layer</label>
                  <select
                    value={(config.layer as string) ?? "bronze"}
                    onChange={(e) => update("layer", e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="bronze">Bronze</option>
                    <option value="silver">Silver</option>
                    <option value="gold">Gold</option>
                    <option value="all">All</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Schema drift probability</label>
                  <select
                    value={(config.drift_profile as string) ?? "none"}
                    onChange={(e) => update("drift_profile", e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="none">None</option>
                    <option value="mild">Mild</option>
                    <option value="moderate">Moderate</option>
                    <option value="aggressive">Aggressive</option>
                  </select>
                  <p className="text-xs text-slate-500 mt-1">Probability of schema drift events</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Messiness</label>
                  <select
                    value={(config.messiness as string) ?? "clean"}
                    onChange={(e) => update("messiness", e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="clean">Clean</option>
                    <option value="realistic">Realistic</option>
                    <option value="chaotic">Chaotic</option>
                  </select>
                </div>
                {String(config.mode) === "cdc" && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Change ratio</label>
                    <input
                      type="number"
                      step="0.01"
                      value={config.change_ratio as number ?? 0.1}
                      onChange={(e) => update("change_ratio", parseFloat(e.target.value) ?? 0.1)}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {section === "privacy" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Privacy</h3>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Privacy mode</label>
                <select
                  value={(config.privacy_mode as string) ?? "warn"}
                  onChange={(e) => update("privacy_mode", e.target.value)}
                  className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="off">Off</option>
                  <option value="warn">Warn</option>
                  <option value="strict">Strict</option>
                </select>
                <p className="text-xs text-slate-500 mt-1">Strict mode blocks generation if sensitive fields lack redaction</p>
              </div>
            </div>
          )}

          {section === "contracts" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Contracts</h3>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={!!config.contracts}
                  onChange={(e) => update("contracts", e.target.checked)}
                />
                <span className="text-sm">Export OpenAPI/JSON Schema contracts</span>
              </label>
            </div>
          )}

          {section === "exports" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Exports</h3>
              <div>
                <label htmlFor="advanced-export-format" className="block text-sm font-medium text-slate-700 mb-1">Export format</label>
                <select
                  id="advanced-export-format"
                  value={(config.export_format as string) ?? "parquet"}
                  onChange={(e) => update("export_format", e.target.value)}
                  className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="parquet">Parquet</option>
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                  <option value="jsonl">JSONL</option>
                </select>
              </div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={!!config.write_manifest}
                  onChange={(e) => update("write_manifest", e.target.checked)}
                />
                <span className="text-sm">Write golden dataset manifest</span>
              </label>
            </div>
          )}

          {section === "load" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Database Load</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Load strategy</label>
                  <select
                    value={(config.load_target as string) ?? ""}
                    onChange={(e) => update("load_target", e.target.value || null)}
                    className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="">None</option>
                    <option value="sqlite">SQLite</option>
                    <option value="duckdb">DuckDB</option>
                    <option value="postgres">PostgreSQL</option>
                    <option value="snowflake">Snowflake</option>
                    <option value="bigquery">BigQuery</option>
                  </select>
                </div>
                {Boolean(config.load_target) && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">DB URI (or configure via load_params)</label>
                    <input
                      type="text"
                      value={(config.db_uri as string) ?? ""}
                      onChange={(e) => update("db_uri", e.target.value || null)}
                      placeholder="postgresql://user:pass@host/db"
                      className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono"
                    />
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Chunk size</label>
                  <input
                    type="number"
                    value={(config.chunk_size as number) ?? ""}
                    onChange={(e) => update("chunk_size", e.target.value ? parseInt(e.target.value, 10) : null)}
                    placeholder="optional"
                    className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Batch size</label>
                  <input
                    type="number"
                    value={config.batch_size as number}
                    onChange={(e) => update("batch_size", parseInt(e.target.value, 10) || 1000)}
                    className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
            </div>
          )}

          {section === "validation" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Validation</h3>
              <p className="text-sm text-slate-600">Quality checks run automatically during generation. Use the Validation Center to validate existing datasets.</p>
            </div>
          )}

          {section === "dbt" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">dbt / GE / Airflow</h3>
              <div className="space-y-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={!!config.export_dbt}
                    onChange={(e) => update("export_dbt", e.target.checked)}
                  />
                  <span className="text-sm">Export dbt seeds</span>
                </label>
                {Boolean(config.export_dbt) && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">dbt dir</label>
                    <input
                      type="text"
                      value={(config.dbt_dir as string) ?? ""}
                      onChange={(e) => update("dbt_dir", e.target.value || null)}
                      placeholder="dbt_project/seeds"
                      className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    />
                  </div>
                )}
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={!!config.export_ge}
                    onChange={(e) => update("export_ge", e.target.checked)}
                  />
                  <span className="text-sm">Export Great Expectations suites</span>
                </label>
                {Boolean(config.export_ge) && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">GE dir</label>
                    <input
                      type="text"
                      value={(config.ge_dir as string) ?? ""}
                      onChange={(e) => update("ge_dir", e.target.value || null)}
                      placeholder="great_expectations/expectations"
                      className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    />
                  </div>
                )}
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={!!config.export_airflow}
                    onChange={(e) => update("export_airflow", e.target.checked)}
                  />
                  <span className="text-sm">Export Airflow DAG</span>
                </label>
                {Boolean(config.export_airflow) && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Airflow dir</label>
                    <input
                      type="text"
                      value={(config.airflow_dir as string) ?? ""}
                      onChange={(e) => update("airflow_dir", e.target.value || null)}
                      placeholder="dags/"
                      className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {section === "simulation" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Pipeline Simulation</h3>
              <p className="text-sm text-slate-600">Generate event streams and pipeline snapshots for simulation workloads.</p>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={!!(config.pipeline_simulation as Record<string, unknown>)?.enabled}
                  onChange={(e) => update("pipeline_simulation", {
                    ...(config.pipeline_simulation as Record<string, unknown> || {}),
                    enabled: e.target.checked,
                  })}
                />
                <span className="text-sm">Enable pipeline simulation</span>
              </label>
              {!!(config.pipeline_simulation as Record<string, unknown>)?.enabled && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Event density</label>
                    <select
                      value={((config.pipeline_simulation as Record<string, unknown>)?.event_density as string) ?? "medium"}
                      onChange={(e) => update("pipeline_simulation", {
                        ...(config.pipeline_simulation as Record<string, unknown> || {}),
                        event_density: e.target.value,
                      })}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Event pattern</label>
                    <select
                      value={((config.pipeline_simulation as Record<string, unknown>)?.event_pattern as string) ?? "steady"}
                      onChange={(e) => update("pipeline_simulation", {
                        ...(config.pipeline_simulation as Record<string, unknown> || {}),
                        event_pattern: e.target.value,
                      })}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    >
                      <option value="steady">Steady</option>
                      <option value="burst">Burst</option>
                      <option value="seasonal">Seasonal</option>
                      <option value="growth">Growth</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Replay mode</label>
                    <select
                      value={((config.pipeline_simulation as Record<string, unknown>)?.replay_mode as string) ?? "ordered"}
                      onChange={(e) => update("pipeline_simulation", {
                        ...(config.pipeline_simulation as Record<string, unknown> || {}),
                        replay_mode: e.target.value,
                      })}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    >
                      <option value="ordered">Ordered</option>
                      <option value="shuffled">Shuffled</option>
                      <option value="windowed">Windowed</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Late arrival ratio (0–1)</label>
                    <input
                      type="number"
                      min={0}
                      max={1}
                      step={0.1}
                      value={((config.pipeline_simulation as Record<string, unknown>)?.late_arrival_ratio as number) ?? 0}
                      onChange={(e) => update("pipeline_simulation", {
                        ...(config.pipeline_simulation as Record<string, unknown> || {}),
                        late_arrival_ratio: parseFloat(e.target.value) || 0,
                      })}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {section === "benchmark" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Benchmark / Performance</h3>
              <p className="text-sm text-slate-600">Run warehouse-style benchmark. Uses profile and scale preset.</p>
              <div className="grid gap-4 sm:grid-cols-2 max-w-xl">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Benchmark profile</label>
                  <select
                    value={((config.benchmark as Record<string, unknown>)?.profile as string) ?? ""}
                    onChange={(e) => update("benchmark", {
                      ...(config.benchmark as Record<string, unknown> || {}),
                      profile: e.target.value || null,
                    })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="">Default</option>
                    <option value="wide_table">Wide table</option>
                    <option value="high_cardinality">High cardinality</option>
                    <option value="event_stream">Event stream</option>
                    <option value="fact_table">Fact table</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Scale preset</label>
                  <select
                    value={((config.benchmark as Record<string, unknown>)?.scale_preset as string) ?? ""}
                    onChange={(e) => update("benchmark", {
                      ...(config.benchmark as Record<string, unknown> || {}),
                      scale_preset: e.target.value || null,
                    })}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="">Use scale</option>
                    <option value="small">Small (~10k)</option>
                    <option value="medium">Medium (~100k)</option>
                    <option value="large">Large (~1M)</option>
                    <option value="xlarge">XLarge (~10M)</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={async () => {
                    setBenchmarkRunLoading(true);
                    setError(null);
                    try {
                      const pack = (config.pack as string) || "saas_billing";
                      const scalePreset = (config.benchmark as Record<string, unknown>)?.scale_preset as string | null;
                      const scale = (config.scale as number) || 1000;
                      const profile = (config.benchmark as Record<string, unknown>)?.profile as string | null;
                      const res = await startBenchmarkRun({
                        pack,
                        scale: scalePreset ? undefined : scale,
                        scale_preset: scalePreset || undefined,
                        profile: profile || undefined,
                        format: "parquet",
                        iterations: 3,
                      });
                      router.push(`/runs/${res.run_id}`);
                    } catch (e) {
                      setError(e instanceof Error ? e.message : "Failed to start benchmark");
                    } finally {
                      setBenchmarkRunLoading(false);
                    }
                  }}
                  disabled={benchmarkRunLoading}
                >
                  {benchmarkRunLoading ? "Starting…" : "Start benchmark run"}
                </Button>
                <Button
                  onClick={async () => {
                    setBenchmarkLoading(true);
                    setBenchmarkResult(null);
                    setError(null);
                    try {
                      const pack = (config.pack as string) || "saas_billing";
                      const scalePreset = (config.benchmark as Record<string, unknown>)?.scale_preset as string | null;
                      const scale = (config.scale as number) || 1000;
                      const profile = (config.benchmark as Record<string, unknown>)?.profile as string | null;
                      const res = await runBenchmark({
                        pack,
                        scale: scalePreset ? undefined : scale,
                        scale_preset: scalePreset || undefined,
                        profile: profile || undefined,
                        format: "parquet",
                        iterations: 3,
                      });
                      setBenchmarkResult(res.benchmark_results ?? res);
                    } catch (e) {
                      setError(e instanceof Error ? e.message : "Benchmark failed");
                    } finally {
                      setBenchmarkLoading(false);
                    }
                  }}
                  disabled={benchmarkLoading}
                >
                  {benchmarkLoading ? "Running…" : "Run inline (sync)"}
                </Button>
              </div>
              {benchmarkResult && (
                <pre className="p-4 bg-slate-50 rounded-lg text-xs overflow-auto font-mono">
                  {JSON.stringify(benchmarkResult, null, 2)}
                </pre>
              )}
            </div>
          )}

          {section === "raw" && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-900">Raw Config & CLI Preview</h3>
              <pre className="p-4 bg-slate-50 rounded-lg text-xs overflow-x-auto max-h-96 overflow-y-auto font-mono">
                {JSON.stringify(config, null, 2)}
              </pre>
              <p className="text-sm text-slate-500">Equivalent CLI: data-forge generate --pack {String(config.pack || "&lt;pack&gt;")} --scale {String(config.scale ?? 1000)} ...</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Preflight & Run</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {blockers.length > 0 && (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 text-sm">
              <p className="font-medium mb-2">Blockers:</p>
              <ul className="list-disc list-inside">{blockers.map((b, i) => <li key={i}>{b}</li>)}</ul>
            </div>
          )}
          {(preflight?.warnings as string[])?.length > 0 && (
            <div className="p-4 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm">
              <p className="font-medium mb-2">Warnings:</p>
              <ul className="list-disc list-inside">{(preflight?.warnings as string[]).map((w, i) => <li key={i}>{w}</li>)}</ul>
            </div>
          )}
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={runPreflightCheck} disabled={preflightLoading}>
              {preflightLoading ? "Running…" : "Run Preflight"}
            </Button>
            <Button
              onClick={handleRun}
              disabled={runLoading || (blockers.length > 0)}
            >
              {runLoading ? "Running…" : "Run Now"}
            </Button>
            {loadedScenarioId ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    if (!updateScenarioConfirm && hasMaskedCredentials) {
                      if (!confirm("This scenario has masked credentials. Updating will keep masked placeholders. Re-enter secrets in Advanced Config if needed. Continue?")) return;
                    }
                    if (!updateScenarioConfirm) {
                      setUpdateScenarioConfirm(true);
                      return;
                    }
                    setUpdateScenarioLoading(true);
                    setError(null);
                    try {
                      await updateScenario(loadedScenarioId, { config });
                      setUpdateScenarioConfirm(false);
                      router.push(`/scenarios/${loadedScenarioId}`);
                    } catch (e) {
                      setError(e instanceof Error ? e.message : "Failed to update scenario");
                    } finally {
                      setUpdateScenarioLoading(false);
                    }
                  }}
                  disabled={updateScenarioLoading}
                >
                  {updateScenarioLoading ? "Updating…" : updateScenarioConfirm ? "Confirm update scenario" : "Update scenario"}
                </Button>
                {updateScenarioConfirm && (
                  <Button variant="outline" size="sm" onClick={() => setUpdateScenarioConfirm(false)}>Cancel update</Button>
                )}
                <Button variant="outline" size="sm" onClick={() => { setSaveScenarioOpen(!saveScenarioOpen); setUpdateScenarioConfirm(false); }}>
                  Save as new scenario
                </Button>
              </>
            ) : (
              <Button variant="outline" size="sm" onClick={() => setSaveScenarioOpen(!saveScenarioOpen)}>
                Save as scenario
              </Button>
            )}
          </div>
          {saveScenarioOpen && (
            <div className="mt-4 p-4 rounded-lg border border-slate-200 bg-slate-50 space-y-3">
              <p className="text-sm font-medium text-slate-700">
                {loadedScenarioId ? "Save current config as a new scenario (original will not be changed)" : "Save current config as reusable scenario"}
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs text-slate-600 mb-1">Name</label>
                  <input
                    type="text"
                    value={saveScenarioName}
                    onChange={(e) => setSaveScenarioName(e.target.value)}
                    placeholder="e.g. Ecommerce order simulation"
                    className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-600 mb-1">Category</label>
                  <select
                    value={saveScenarioCategory}
                    onChange={(e) => setSaveScenarioCategory(e.target.value)}
                    className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
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
              </div>
              <div>
                <label className="block text-xs text-slate-600 mb-1">Description (optional)</label>
                <input
                  type="text"
                  value={saveScenarioDesc}
                  onChange={(e) => setSaveScenarioDesc(e.target.value)}
                  placeholder="Brief description"
                  className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={async () => {
                    if (!saveScenarioName.trim()) { setError("Name is required"); return; }
                    setSaveScenarioLoading(true);
                    setError(null);
                    try {
                      await createScenario({
                        name: saveScenarioName.trim(),
                        description: saveScenarioDesc.trim(),
                        category: saveScenarioCategory,
                        config,
                        created_from_scenario_id: loadedScenarioId || undefined,
                      });
                      setSaveScenarioOpen(false);
                      setSaveScenarioName("");
                      setSaveScenarioDesc("");
                      router.push("/scenarios");
                    } catch (e) {
                      setError(e instanceof Error ? e.message : "Failed to save scenario");
                    } finally {
                      setSaveScenarioLoading(false);
                    }
                  }}
                  disabled={saveScenarioLoading}
                >
                  {saveScenarioLoading ? "Saving…" : "Save as new scenario"}
                </Button>
                <Button variant="outline" size="sm" onClick={() => setSaveScenarioOpen(false)}>Cancel</Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AdvancedConfigPage() {
  return (
    <Suspense fallback={<div className="p-8 text-slate-500">Loading…</div>}>
      <AdvancedConfigContent />
    </Suspense>
  );
}
