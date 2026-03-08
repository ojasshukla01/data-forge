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

export const useWizardStore = create<{
  config: WizardConfig;
  setConfig: (c: Partial<WizardConfig>) => void;
  reset: () => void;
}>((set) => ({
  config: defaultConfig,
  setConfig: (c) => set((s) => ({ config: { ...s.config, ...c } })),
  reset: () => set({ config: defaultConfig }),
}));
