"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useWizardStore } from "@/stores/wizardStore";
import { scenarioConfigToWizardConfig, scenarioHasAdvancedOnlySettings } from "@/stores/wizardStore";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { startRunGenerate, runPreflight, fetchPacks, fetchScenarios, fetchScenario, createScenario, fetchCustomSchemas, type PackInfo } from "@/lib/api";
import type { CustomSchemaSummary } from "@/lib/api";
import type { ScenarioRecord } from "@/lib/api";
import { cn } from "@/lib/utils";

const MASKED = "***";

const STEPS = [
  { id: "input", label: "Choose Input" },
  { id: "usecase", label: "Use Case" },
  { id: "realism", label: "Realism" },
  { id: "export", label: "Export" },
  { id: "review", label: "Review & Run" },
];

function formatPackLabel(id: string): string {
  return id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const USE_CASES = [
  { id: "demo", label: "Demo Data", scale: 500, messiness: "clean" },
  { id: "unit", label: "Unit Test", scale: 50, messiness: "clean" },
  { id: "integration", label: "Integration Test", scale: 1000, messiness: "realistic" },
  { id: "etl", label: "ETL Simulation", scale: 2000, messiness: "realistic" },
  { id: "load", label: "Warehouse Load Test", scale: 5000, messiness: "clean" },
];

function WizardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const packFromUrl = searchParams.get("pack");
  const scenarioIdFromUrl = searchParams.get("scenario");
  const { config, setConfig, reset } = useWizardStore();
  const [stepIndex, setStepIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [packs, setPacks] = useState<PackInfo[]>([]);
  const [packsLoading, setPacksLoading] = useState(true);
  const [packsError, setPacksError] = useState<string | null>(null);
  const [schemaSource, setSchemaSource] = useState<"pack" | "custom">("pack");
  const [customSchemas, setCustomSchemas] = useState<CustomSchemaSummary[]>([]);
  const [customSchemasLoading, setCustomSchemasLoading] = useState(false);
  const [customSchemasError, setCustomSchemasError] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioRecord[]>([]);
  const [scenariosLoading, setScenariosLoading] = useState(false);
  const [loadedScenario, setLoadedScenario] = useState<ScenarioRecord | null>(null);
  const [entryMode, setEntryMode] = useState<"scratch" | "scenario">("scratch");
  const [preflight, setPreflight] = useState<Record<string, unknown> | null>(null);
  const [preflightLoading, setPreflightLoading] = useState(false);
  const [saveScenarioOpen, setSaveScenarioOpen] = useState(false);
  const [saveScenarioName, setSaveScenarioName] = useState("");
  const [saveScenarioDesc, setSaveScenarioDesc] = useState("");
  const [saveScenarioCategory, setSaveScenarioCategory] = useState("custom");
  const [saveScenarioLoading, setSaveScenarioLoading] = useState(false);
  const [saveScenarioSuccess, setSaveScenarioSuccess] = useState(false);

  const stepId = STEPS[stepIndex].id;

  useEffect(() => {
    let cancelled = false;
    setPacksLoading(true);
    setPacksError(null);
    fetchPacks()
      .then((data) => { if (!cancelled) setPacks(data); })
      .catch((e) => { if (!cancelled) setPacksError(e instanceof Error ? e.message : "Failed to load packs"); setPacks([]); })
      .finally(() => { if (!cancelled) setPacksLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setScenariosLoading(true);
    fetchScenarios()
      .then((d) => { if (!cancelled) setScenarios(d.scenarios ?? []); })
      .catch(() => { if (!cancelled) setScenarios([]); })
      .finally(() => { if (!cancelled) setScenariosLoading(false); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (packFromUrl && packs.some((p) => p.id === packFromUrl)) {
      setConfig({ pack: packFromUrl, customSchemaId: null });
      setSchemaSource("pack");
    }
  }, [packFromUrl, packs, setConfig]);

  useEffect(() => {
    if (schemaSource !== "custom") return;
    let cancelled = false;
    setCustomSchemasLoading(true);
    setCustomSchemasError(null);
    fetchCustomSchemas()
      .then((data) => { if (!cancelled) setCustomSchemas(data); })
      .catch((e) => { if (!cancelled) setCustomSchemasError(e instanceof Error ? e.message : "Failed to load custom schemas"); setCustomSchemas([]); })
      .finally(() => { if (!cancelled) setCustomSchemasLoading(false); });
    return () => { cancelled = true; };
  }, [schemaSource]);

  // Load scenario from ?scenario=<id>
  useEffect(() => {
    if (!scenarioIdFromUrl) return;
    fetchScenario(scenarioIdFromUrl)
      .then((s) => {
        if (!s?.config) return;
        const cfg = s.config as Record<string, unknown>;
        const masked = Object.values(cfg).some((v) => v === MASKED);
        if (masked) return; // Skip prefilling if credentials were masked
        const wizardFields = scenarioConfigToWizardConfig(cfg);
        setConfig(wizardFields);
        setLoadedScenario(s);
        setEntryMode("scenario");
      })
      .catch(() => setError("Failed to load scenario"));
  }, [scenarioIdFromUrl, setConfig]);

  const hasAdvancedOnly = loadedScenario?.config ? scenarioHasAdvancedOnlySettings(loadedScenario.config as Record<string, unknown>) : false;

  const handleSelectScenario = (s: ScenarioRecord) => {
    const cfg = (s.config || {}) as Record<string, unknown>;
    const wizardFields = scenarioConfigToWizardConfig(cfg);
    setConfig(wizardFields);
    setLoadedScenario(s);
    setEntryMode("scenario");
  };

  const handleStartFromScratch = () => {
    reset();
    setLoadedScenario(null);
    setEntryMode("scratch");
    setSchemaSource("pack");
  };

  const runPreflightCheck = async () => {
    setPreflightLoading(true);
    setPreflight(null);
    try {
      const payload: Record<string, unknown> = {
        pack: config.pack,
        custom_schema_id: config.customSchemaId,
        schema_path: config.schemaPath,
        scale: config.scale,
        messiness: config.messiness,
        mode: config.mode,
        layer: config.layer,
        export_format: config.exportFormat,
        load_target: config.loadTarget,
        export_ge: config.exportGe,
        export_airflow: config.exportAirflow,
        export_dbt: config.exportDbt,
        contracts: config.contracts,
      };
      const data = await runPreflight(payload as Record<string, unknown>);
      setPreflight(data);
      setError(null);
    } catch (e) {
      setPreflight({ valid: false, blockers: [e instanceof Error ? e.message : "Preflight failed"] });
    } finally {
      setPreflightLoading(false);
    }
  };

  useEffect(() => {
    if (stepId === "review" && (config.pack || config.customSchemaId)) {
      runPreflightCheck();
    } else if (stepId !== "review") {
      setPreflight(null);
    }
  }, [stepId]);

  const wizardConfigToApiConfig = (): Record<string, unknown> => ({
    pack: config.pack,
    custom_schema_id: config.customSchemaId,
    schema_path: config.schemaPath,
    seed: config.seed,
    scale: config.scale,
    messiness: config.messiness,
    mode: config.mode,
    layer: config.layer,
    privacy_mode: config.privacyMode,
    export_format: config.exportFormat,
    load_target: config.loadTarget,
    include_anomalies: config.include_anomalies,
    anomaly_ratio: config.anomaly_ratio,
    export_ge: config.exportGe,
    export_airflow: config.exportAirflow,
    export_dbt: config.exportDbt,
    contracts: config.contracts,
  });

  const handleSaveScenario = async () => {
    const name = saveScenarioName.trim();
    if (!name) { setError("Scenario name is required"); return; }
    setSaveScenarioLoading(true);
    setError(null);
    try {
      await createScenario({
        name,
        description: saveScenarioDesc.trim(),
        category: saveScenarioCategory,
        config: wizardConfigToApiConfig(),
        created_from_scenario_id: loadedScenario?.id,
      });
      setSaveScenarioSuccess(true);
      setSaveScenarioOpen(false);
      setTimeout(() => setSaveScenarioSuccess(false), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save scenario");
    } finally {
      setSaveScenarioLoading(false);
    }
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        pack: config.pack,
        custom_schema_id: config.customSchemaId,
        schema_path: config.schemaPath,
        seed: config.seed,
        scale: config.scale,
        messiness: config.messiness,
        mode: config.mode,
        layer: config.layer,
        privacy_mode: config.privacyMode,
        export_format: config.exportFormat,
        load_target: config.loadTarget,
        include_anomalies: config.include_anomalies,
        anomaly_ratio: config.anomaly_ratio,
        export_ge: config.exportGe,
        export_airflow: config.exportAirflow,
        export_dbt: config.exportDbt,
        contracts: config.contracts,
      };
      const res = await startRunGenerate(payload);
      router.push(`/runs/${res.run_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Create Dataset</h1>
        <p className="text-slate-600 mt-1">Guided setup for synthetic data generation</p>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-2">
        {STEPS.map((s, i) => (
          <button
            key={s.id}
            onClick={() => setStepIndex(i)}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors",
              i === stepIndex
                ? "bg-slate-900 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            )}
          >
            {s.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-red-800 text-sm">
          {error}
        </div>
      )}

      {loadedScenario && (
        <Card className="border-[var(--brand-teal)]/30 bg-slate-50/50">
          <CardContent className="py-4">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="font-medium text-slate-900">Loaded from scenario: {loadedScenario.name}</p>
                <p className="text-sm text-slate-600 mt-1">
                  {loadedScenario.category} {loadedScenario.source_pack && `· Pack: ${loadedScenario.source_pack}`}
                </p>
                {hasAdvancedOnly && (
                  <p className="text-sm text-amber-700 mt-2">
                    This scenario includes pipeline simulation, benchmark, or other advanced settings that are not fully editable in the wizard. Use Advanced Config for full control.
                  </p>
                )}
              </div>
              <Link href={`/create/advanced?scenario=${loadedScenario.id}`}>
                <Button variant="outline" size="sm">Open in Advanced Config</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{STEPS[stepIndex].label}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {stepId === "input" && (
            <>
              <div className="flex gap-3 mb-4">
                <button
                  onClick={handleStartFromScratch}
                  className={cn(
                    "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                    entryMode === "scratch"
                      ? "bg-slate-900 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  )}
                >
                  Start from scratch
                </button>
                <button
                  onClick={() => setEntryMode("scenario")}
                  className={cn(
                    "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                    entryMode === "scenario"
                      ? "bg-slate-900 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  )}
                >
                  Use a saved scenario
                </button>
              </div>

              {entryMode === "scenario" ? (
                scenariosLoading ? (
                  <div className="h-32 rounded-lg border border-slate-200 bg-slate-50 animate-pulse" />
                ) : scenarios.length === 0 ? (
                  <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-amber-800 text-sm">
                    No saved scenarios yet. Save one from Advanced config or create from a run.
                    <div className="mt-3">
                      <Link href="/create/advanced"><Button variant="outline" size="sm">Go to Advanced</Button></Link>
                      <Link href="/scenarios" className="ml-2 inline-block"><Button variant="outline" size="sm">Scenario library</Button></Link>
                    </div>
                  </div>
                ) : (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {scenarios.map((s) => (
                      <button
                        key={s.id}
                        onClick={() => handleSelectScenario(s)}
                        className={cn(
                          "text-left p-4 rounded-lg border-2 transition-colors",
                          loadedScenario?.id === s.id
                            ? "border-slate-900 bg-slate-50"
                            : "border-slate-200 hover:border-slate-300"
                        )}
                      >
                        <p className="font-medium text-slate-900">{s.name}</p>
                        <p className="text-sm text-slate-600 mt-1">{s.category} {s.source_pack && `· ${s.source_pack}`}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {s.uses_pipeline_simulation && <Badge variant="category" className="text-xs">Simulation</Badge>}
                          {s.uses_benchmark && <Badge variant="category" className="text-xs">Benchmark</Badge>}
                        </div>
                      </button>
                    ))}
                  </div>
                )
              ) : (
                <>
                  <div className="flex gap-3 mb-4">
                    <button
                      onClick={() => { setSchemaSource("pack"); setConfig({ pack: config.pack, customSchemaId: null }); }}
                      className={cn(
                        "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                        schemaSource === "pack"
                          ? "bg-slate-900 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      )}
                    >
                      Domain Pack
                    </button>
                    <button
                      onClick={() => { setSchemaSource("custom"); setConfig({ customSchemaId: config.customSchemaId, pack: null }); }}
                      className={cn(
                        "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                        schemaSource === "custom"
                          ? "bg-slate-900 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      )}
                    >
                      Custom Schema
                    </button>
                  </div>
                  {schemaSource === "pack" && (
                  <p className="text-sm text-slate-600">Choose a domain pack to get started quickly.</p>
                  )}
                  {schemaSource === "custom" && (
                  <p className="text-sm text-slate-600">Choose a custom schema from Schema Studio. <Link href="/schema/studio" className="text-[var(--brand-teal)] hover:underline">Create or edit schemas →</Link></p>
                  )}
                  {schemaSource === "pack" && packsLoading ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {[1, 2].map((i) => (
                    <div key={i} className="h-24 rounded-lg border border-slate-200 bg-slate-50 animate-pulse" />
                  ))}
                </div>
              ) : packsError ? (
                <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-amber-800 text-sm">
                  <p>Could not load domain packs. Ensure the API is running.</p>
                  <Button variant="outline" size="sm" className="mt-2" onClick={() => window.location.reload()}>
                    Retry
                  </Button>
                </div>
              ) : packs.length === 0 ? (
                <div className="text-slate-500 text-sm">No domain packs available. Add schemas to the backend.</div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2">
                  {packs.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => setConfig({ pack: p.id, schemaPath: null })}
                      className={cn(
                        "text-left p-4 rounded-lg border-2 transition-colors",
                        config.pack === p.id
                          ? "border-slate-900 bg-slate-50"
                          : "border-slate-200 hover:border-slate-300"
                      )}
                    >
                      <p className="font-medium text-slate-900">{formatPackLabel(p.id)}</p>
                      <p className="text-sm text-slate-600 mt-1">{p.description}</p>
                      {p.tables_count != null && (
                        <p className="text-xs text-slate-500 mt-1">{p.tables_count} table{p.tables_count !== 1 ? "s" : ""}</p>
                      )}
                    </button>
                  ))}
                </div>
              )}
                  {schemaSource === "custom" && (
                    customSchemasLoading ? (
                      <div className="grid gap-4 sm:grid-cols-2">
                        {[1, 2].map((i) => (
                          <div key={i} className="h-24 rounded-lg border border-slate-200 bg-slate-50 animate-pulse" />
                        ))}
                      </div>
                    ) : customSchemasError ? (
                      <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-amber-800 text-sm">
                        <p>Could not load custom schemas. Ensure the API is running.</p>
                        <Button variant="outline" size="sm" className="mt-2" onClick={() => setSchemaSource("custom")}>
                          Retry
                        </Button>
                      </div>
                    ) : customSchemas.length === 0 ? (
                      <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-amber-800 text-sm">
                        No custom schemas yet. Create one in Schema Studio.
                        <div className="mt-3">
                          <Link href="/schema/studio"><Button variant="outline" size="sm">Open Schema Studio</Button></Link>
                        </div>
                      </div>
                    ) : (
                      <div className="grid gap-4 sm:grid-cols-2">
                        {customSchemas.map((s) => (
                          <button
                            key={s.id}
                            onClick={() => setConfig({ customSchemaId: s.id, pack: null })}
                            className={cn(
                              "text-left p-4 rounded-lg border-2 transition-colors",
                              config.customSchemaId === s.id
                                ? "border-slate-900 bg-slate-50"
                                : "border-slate-200 hover:border-slate-300"
                            )}
                          >
                            <p className="font-medium text-slate-900">{s.name}</p>
                            <p className="text-sm text-slate-600 mt-1">{s.description || "No description"}</p>
                            {s.version != null && (
                              <p className="text-xs text-slate-500 mt-1">v{s.version}</p>
                            )}
                          </button>
                        ))}
                      </div>
                    )
                  )}
              </>
            )}
          </>
        )}

          {stepId === "usecase" && (
            <>
              <p className="text-sm text-slate-600">Select a preset or customize below.</p>
              <div className="grid gap-3 sm:grid-cols-2">
                {USE_CASES.map((u) => (
                  <button
                    key={u.id}
                    onClick={() =>
                      setConfig({
                        useCase: u.id,
                        scale: u.scale,
                        messiness: u.messiness,
                      })
                    }
                    className={cn(
                      "text-left p-4 rounded-lg border transition-colors",
                      config.useCase === u.id
                        ? "border-slate-900 bg-slate-50"
                        : "border-slate-200 hover:border-slate-300"
                    )}
                  >
                    <p className="font-medium text-slate-900">{u.label}</p>
                    <p className="text-sm text-slate-600">
                      Scale: {u.scale} · {u.messiness}
                    </p>
                  </button>
                ))}
              </div>
            </>
          )}

          {stepId === "realism" && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Scale (base row count)</label>
                <input
                  type="number"
                  value={config.scale}
                  onChange={(e) => setConfig({ scale: parseInt(e.target.value, 10) || 1000 })}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2"
                  min={1}
                  max={1000000}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Messiness</label>
                <select
                  value={config.messiness}
                  onChange={(e) => setConfig({ messiness: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2"
                >
                  <option value="clean">Clean</option>
                  <option value="realistic">Realistic</option>
                  <option value="chaotic">Chaotic</option>
                </select>
                <p className="text-xs text-slate-500 mt-1">
                  Clean = minimal nulls/duplicates. Chaotic = messy source simulation.
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Mode</label>
                <select
                  value={config.mode}
                  onChange={(e) => setConfig({ mode: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2"
                >
                  <option value="full_snapshot">Full snapshot</option>
                  <option value="incremental">Incremental</option>
                  <option value="cdc">CDC</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Layer</label>
                <select
                  value={config.layer}
                  onChange={(e) => setConfig({ layer: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2"
                >
                  <option value="bronze">Bronze</option>
                  <option value="silver">Silver</option>
                  <option value="gold">Gold</option>
                  <option value="all">All (bronze + silver + gold)</option>
                </select>
              </div>
            </div>
          )}

          {stepId === "export" && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Export format</label>
                <select
                  value={config.exportFormat}
                  onChange={(e) => setConfig({ exportFormat: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-4 py-2"
                >
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                  <option value="jsonl">JSONL</option>
                  <option value="parquet">Parquet</option>
                  <option value="sql">SQL</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Integrations</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.exportGe}
                      onChange={(e) => setConfig({ exportGe: e.target.checked })}
                      className="rounded"
                    />
                    <span>Export Great Expectations suites</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.exportAirflow}
                      onChange={(e) => setConfig({ exportAirflow: e.target.checked })}
                      className="rounded"
                    />
                    <span>Export Airflow DAG templates</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.exportDbt}
                      onChange={(e) => setConfig({ exportDbt: e.target.checked })}
                      className="rounded"
                    />
                    <span>Export dbt seeds</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.contracts}
                      onChange={(e) => setConfig({ contracts: e.target.checked })}
                      className="rounded"
                    />
                    <span>Generate OpenAPI contract fixtures</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {stepId === "review" && (
            <div className="space-y-4 text-sm">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="font-medium text-slate-700 mb-2">Schema source</p>
                <p>
                  {config.customSchemaId ? (
                    <>
                      <span className="text-slate-600">Custom schema: </span>
                      <span className="font-medium">
                        {customSchemas.find((s) => s.id === config.customSchemaId)?.name ?? config.customSchemaId}
                      </span>
                    </>
                  ) : config.pack ? (
                    <>
                      <span className="text-slate-600">Domain pack: </span>
                      <span className="font-medium">{formatPackLabel(config.pack)}</span>
                    </>
                  ) : (
                    <span className="text-amber-700">— Select a schema source in step 1</span>
                  )}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <span className="text-slate-500">Scale</span>
                <span>{config.scale}</span>
                <span className="text-slate-500">Messiness</span>
                <span>{config.messiness}</span>
                <span className="text-slate-500">Mode</span>
                <span>{config.mode}</span>
                <span className="text-slate-500">Layer</span>
                <span>{config.layer}</span>
                <span className="text-slate-500">Format</span>
                <span>{config.exportFormat}</span>
              </div>
              {preflightLoading && (
                <p className="text-slate-500">Running preflight checks…</p>
              )}
              {preflight && !preflightLoading && (
                <div className="space-y-3">
                  {(preflight.blockers as string[])?.length > 0 && (
                    <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3">
                      <p className="font-medium text-red-800">Blockers</p>
                      <ul className="list-disc list-inside text-red-700 text-sm mt-1">
                        {(preflight.blockers as string[]).map((b, i) => (
                          <li key={i}>{b}</li>
                        ))}
                      </ul>
                      {config.customSchemaId && (preflight.blockers as string[]).some((b) => /custom schema|schema not found|schema.*invalid/i.test(b)) && (
                        <Link href="/schema/studio" className="inline-block mt-2 text-sm text-[var(--brand-teal)] hover:underline">Open Schema Studio to fix →</Link>
                      )}
                    </div>
                  )}
                  {(preflight.warnings as string[])?.length > 0 && (
                    <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3">
                      <p className="font-medium text-amber-800">Warnings</p>
                      <ul className="list-disc list-inside text-amber-700 text-sm mt-1">
                        {(preflight.warnings as string[]).map((w, i) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {(preflight.recommendations as string[])?.length > 0 && (
                    <div className="rounded-lg bg-slate-50 border border-slate-200 px-4 py-3">
                      <p className="font-medium text-slate-700">Recommendations</p>
                      <ul className="list-disc list-inside text-slate-600 text-sm mt-1">
                        {(preflight.recommendations as string[]).map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {preflight.estimated_rows != null && (
                    <p className="text-slate-600">Est. rows: {String(preflight.estimated_rows)}</p>
                  )}
                  {preflight.estimated_memory_mb != null && (
                    <p className="text-slate-600">Est. memory: ~{String(preflight.estimated_memory_mb)} MB</p>
                  )}
                  <Button variant="ghost" size="sm" onClick={runPreflightCheck} disabled={preflightLoading}>
                    Refresh preflight
                  </Button>
                </div>
              )}
              <p className="text-slate-600">
                {preflight?.valid === false && (preflight.blockers as string[])?.length
                  ? "Fix blockers before running."
                  : "Ready to generate. Click Run to execute the pipeline."}
              </p>
              {hasAdvancedOnly && (
                <p className="text-amber-700 text-sm">This scenario includes pipeline simulation, benchmark, or other settings not editable in the wizard. Save as scenario will store current wizard values only.</p>
              )}
              {saveScenarioSuccess && <p className="text-green-700 text-sm">Scenario saved. You can find it in the Scenario library.</p>}
              <div className="flex flex-wrap gap-2 items-center pt-2">
                <Button variant="outline" size="sm" onClick={() => setSaveScenarioOpen(!saveScenarioOpen)}>
                  {saveScenarioOpen ? "Cancel" : "Save as scenario"}
                </Button>
                {saveScenarioOpen && (
                  <>
                    <input
                      type="text"
                      value={saveScenarioName}
                      onChange={(e) => setSaveScenarioName(e.target.value)}
                      placeholder="Scenario name"
                      className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm w-48"
                    />
                    <input
                      type="text"
                      value={saveScenarioDesc}
                      onChange={(e) => setSaveScenarioDesc(e.target.value)}
                      placeholder="Description (optional)"
                      className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm w-48"
                    />
                    <select
                      value={saveScenarioCategory}
                      onChange={(e) => setSaveScenarioCategory(e.target.value)}
                      className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
                    >
                      <option value="custom">Custom</option>
                      <option value="quick_start">Quick start</option>
                      <option value="testing">Testing</option>
                      <option value="pipeline_simulation">Pipeline simulation</option>
                      <option value="warehouse_benchmark">Warehouse benchmark</option>
                    </select>
                    <Button size="sm" onClick={handleSaveScenario} disabled={saveScenarioLoading}>
                      {saveScenarioLoading ? "Saving…" : "Save"}
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button
          variant="outline"
          disabled={stepIndex === 0}
          onClick={() => setStepIndex((i) => Math.max(0, i - 1))}
        >
          Back
        </Button>
        {stepIndex < STEPS.length - 1 ? (
          <Button
            disabled={stepId === "input" && (entryMode === "scratch" ? !config.pack && !config.customSchemaId : !loadedScenario)}
            onClick={() => setStepIndex((i) => Math.min(STEPS.length - 1, i + 1))}
          >
            Next
          </Button>
        ) : (
          <Button
            onClick={handleRun}
            disabled={loading || (preflight?.valid === false && (preflight?.blockers as string[])?.length > 0)}
          >
            {loading ? "Running…" : "Run"}
          </Button>
        )}
      </div>
    </div>
  );
}

export default function WizardPage() {
  return (
    <Suspense fallback={<div className="p-8 text-slate-500">Loading…</div>}>
      <WizardContent />
    </Suspense>
  );
}
