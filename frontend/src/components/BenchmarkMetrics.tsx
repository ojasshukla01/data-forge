"use client";

import { StatCard } from "@/components/ui/StatCard";
import { BenchmarkBarChart } from "@/components/BenchmarkBarChart";

export interface BenchmarkData {
  total_rows_generated?: number;
  rows_generated?: number;
  duration?: number;
  throughput?: number;
  throughput_rows_per_second?: number;
  memory_estimate?: number;
  peak_memory_mb_estimate?: number;
  generation_seconds?: number;
  export_seconds?: number;
  load_seconds?: number;
  profile_used?: string;
  scale_preset_used?: string;
  parallel_tables_used?: number;
  batch_size_used?: number;
  write_strategy_used?: string;
  rows_per_second_generation?: number;
  rows_per_second_load?: number;
}

interface BenchmarkMetricsProps {
  data: BenchmarkData;
}

export function BenchmarkMetrics({ data }: BenchmarkMetricsProps) {
  const rows = data.total_rows_generated ?? data.rows_generated ?? 0;
  const duration = data.duration ?? 0;
  const throughput = data.throughput ?? data.throughput_rows_per_second ?? 0;
  const memory = data.memory_estimate ?? data.peak_memory_mb_estimate ?? 0;
  const genSec = data.generation_seconds ?? 0;
  const exportSec = data.export_seconds ?? 0;

  const bars = [
    throughput > 0 && { label: "rows/s", value: throughput, max: Math.max(throughput, 1000) },
    genSec > 0 && { label: "gen (s)", value: genSec, max: Math.max(genSec, 10) },
    exportSec > 0 && { label: "export (s)", value: exportSec, max: Math.max(exportSec, 5) },
    memory > 0 && {
      label: "mem (MB)",
      value: memory,
      max: Math.max(memory, 100),
    },
  ].filter(Boolean) as { label: string; value: number; max: number }[];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Rows" value={rows > 0 ? rows.toLocaleString() : "—"} />
        <StatCard label="Duration" value={duration > 0 ? `${duration}s` : "—"} />
        <StatCard label="Throughput" value={throughput > 0 ? `${throughput} rows/s` : "—"} />
        <StatCard label="Memory est." value={memory > 0 ? `${memory} MB` : "—"} />
      </div>
      {(data.profile_used || data.scale_preset_used || data.write_strategy_used || data.parallel_tables_used) && (
        <div className="flex flex-wrap gap-4 text-sm text-slate-600">
          {data.profile_used && <span>Profile: <strong>{data.profile_used}</strong></span>}
          {data.scale_preset_used && <span>Scale: <strong>{data.scale_preset_used}</strong></span>}
          {data.write_strategy_used && <span>Write: <strong>{data.write_strategy_used}</strong></span>}
          {data.parallel_tables_used != null && <span>Parallel tables: <strong>{data.parallel_tables_used}</strong></span>}
        </div>
      )}
      {bars.length > 0 && (
        <div className="pt-4 border-t border-slate-200">
          <p className="text-sm font-medium text-slate-700 mb-3">Visualization</p>
          <div className="space-y-3">
            <BenchmarkBarChart bars={bars} />
          </div>
        </div>
      )}
    </div>
  );
}
