import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface RunRecord {
  id: string;
  timestamp: string;
  config: Record<string, unknown>;
  result: Record<string, unknown>;
}

/** Strip heavy fields to stay under localStorage quota (~5MB) */
function slimResult(result: Record<string, unknown>): Record<string, unknown> {
  const tables = (result.tables as { table_name: string; row_count?: number }[] | undefined) ?? [];
  return {
    success: result.success,
    duration_seconds: result.duration_seconds,
    output_dir: result.output_dir,
    export_paths: result.export_paths,
    performance_warnings: result.performance_warnings,
    timings: result.timings,
    tables: tables.map((t) => ({ table_name: t.table_name, row_count: t.row_count ?? 0 })),
    quality_report: result.quality_report ? { referential_integrity: (result.quality_report as Record<string, unknown>)?.referential_integrity } : undefined,
  };
}

export const useRunsStore = create<{
  runs: RunRecord[];
  addRun: (id: string, config: Record<string, unknown>, result: Record<string, unknown>) => void;
  getRun: (id: string) => RunRecord | undefined;
}>()(
  persist(
    (set, get) => ({
      runs: [],
      addRun: (id, config, result) =>
        set((s) => ({
          runs: [
            { id, timestamp: new Date().toISOString(), config, result: slimResult(result) },
            ...s.runs.slice(0, 19),
          ],
        })),
      getRun: (id) => get().runs.find((r) => r.id === id),
    }),
    { name: "data-forge-runs" }
  )
);
