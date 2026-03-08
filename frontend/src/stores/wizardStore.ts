import { create } from "zustand";

export interface WizardConfig {
  pack: string | null;
  schemaPath: string | null;
  useCase: string;
  scale: number;
  messiness: string;
  mode: string;
  layer: string;
  privacyMode: string;
  exportFormat: string;
  loadTarget: string | null;
  include_anomalies: boolean;
  anomaly_ratio: number;
  exportGe: boolean;
  exportAirflow: boolean;
  exportDbt: boolean;
  contracts: boolean;
  seed: number;
}

const defaultConfig: WizardConfig = {
  pack: null,
  schemaPath: null,
  useCase: "demo",
  scale: 1000,
  messiness: "clean",
  mode: "full_snapshot",
  layer: "bronze",
  privacyMode: "warn",
  exportFormat: "parquet",
  loadTarget: null,
  include_anomalies: false,
  anomaly_ratio: 0.02,
  exportGe: false,
  exportAirflow: false,
  exportDbt: false,
  contracts: false,
  seed: 42,
};

export function scenarioConfigToWizardConfig(scenarioConfig: Record<string, unknown>): Partial<WizardConfig> {
  const c = scenarioConfig || {};
  const out: Partial<WizardConfig> = {};
  if (c.pack != null) out.pack = String(c.pack);
  if (c.schema_path != null) out.schemaPath = String(c.schema_path);
  if (c.scale != null) out.scale = Number(c.scale) || 1000;
  if (c.messiness != null) out.messiness = String(c.messiness);
  if (c.mode != null) out.mode = String(c.mode);
  if (c.layer != null) out.layer = String(c.layer);
  if (c.privacy_mode != null) out.privacyMode = String(c.privacy_mode);
  if (c.export_format != null) out.exportFormat = String(c.export_format);
  if (c.load_target != null) out.loadTarget = String(c.load_target);
  if (c.export_ge != null) out.exportGe = Boolean(c.export_ge);
  if (c.export_airflow != null) out.exportAirflow = Boolean(c.export_airflow);
  if (c.export_dbt != null) out.exportDbt = Boolean(c.export_dbt);
  if (c.contracts != null) out.contracts = Boolean(c.contracts);
  if (c.seed != null) out.seed = Number(c.seed) || 42;
  if (c.include_anomalies != null) out.include_anomalies = Boolean(c.include_anomalies);
  if (c.anomaly_ratio != null) out.anomaly_ratio = Number(c.anomaly_ratio) ?? 0.02;
  // Infer useCase from scale/messiness
  const scale = Number(out.scale ?? c.scale ?? 1000) || 1000;
  const messiness = String(out.messiness ?? c.messiness ?? "clean");
  if (scale <= 100) out.useCase = "unit";
  else if (scale <= 500) out.useCase = "demo";
  else if (scale <= 1000 && messiness === "realistic") out.useCase = "integration";
  else if (scale <= 2000) out.useCase = "etl";
  else out.useCase = "load";
  return out;
}

/** Detect if scenario has advanced-only settings wizard cannot edit */
export function scenarioHasAdvancedOnlySettings(config: Record<string, unknown>): boolean {
  const ps = (config?.pipeline_simulation as Record<string, unknown>) ?? {};
  const bench = (config?.benchmark as Record<string, unknown>) ?? {};
  const drift = config?.drift_profile as string | undefined;
  return (
    ps.enabled === true ||
    bench.enabled === true ||
    !!config?.rules_path ||
    (!!drift && drift !== "none")
  );
}

export const useWizardStore = create<{
  config: WizardConfig;
  setConfig: (c: Partial<WizardConfig>) => void;
  reset: () => void;
}>((set) => ({
  config: defaultConfig,
  setConfig: (c) => set((s) => ({ config: { ...s.config, ...c } })),
  reset: () => set({ config: defaultConfig }),
}));
