"use client";

import { StatCard } from "@/components/ui/StatCard";
import { PipelineFlowGraph } from "@/components/PipelineFlowGraph";
import Link from "next/link";
import { Button } from "@/components/ui/Button";

export interface PipelineSimulationData {
  event_stream_count?: number;
  time_window_start?: string;
  time_window_end?: string;
  event_pattern?: string;
  replay_mode?: string;
  late_arrival_ratio?: number;
  parallel_streams?: number;
  stage_progress?: { name: string; status: string }[];
}

interface PipelineSimulationSectionProps {
  config?: Record<string, unknown>;
  result?: Record<string, unknown>;
  runId?: string;
  artifacts?: { type?: string; name: string; path: string }[];
  stageProgress?: { name: string; status: string }[];
}

export function PipelineSimulationSection({
  config,
  result,
  runId,
  artifacts,
  stageProgress,
}: PipelineSimulationSectionProps) {
  const sim = (config?.pipeline_simulation as Record<string, unknown>) || {};
  if (!sim.enabled && !result?.event_stream_count && !result?.simulation_summary) return null;

  const eventCount = (result?.event_stream_count as number) ?? (result?.simulation_summary as Record<string, unknown>)?.event_stream_count;
  const timeStart = (result?.time_window_start as string) ?? (result?.simulation_summary as Record<string, unknown>)?.time_window_start;
  const timeEnd = (result?.time_window_end as string) ?? (result?.simulation_summary as Record<string, unknown>)?.time_window_end;
  const pattern = (sim.event_pattern as string) ?? (result?.event_pattern as string);
  const replay = (sim.replay_mode as string) ?? (result?.replay_mode as string);
  const lateRatio = (sim.late_arrival_ratio as number) ?? (result?.late_arrival_ratio as number);
  const streams = (sim.parallel_streams as number) ?? (result?.parallel_streams as number);
  const stages = stageProgress ?? (config?.stage_progress ?? result?.stage_progress) as { name: string; status: string }[] | undefined;
  const eventStreamArtifacts = artifacts?.filter((a) => a.type === "event_stream" || a.path?.includes("event_stream") || a.path?.endsWith("events.jsonl")) ?? [];

  const flowStages = stages?.map((s) => ({
    id: s.name,
    label: s.name.replace(/_/g, " "),
    status: s.status as "pending" | "running" | "completed" | "skipped" | "failed",
  }));

  return (
    <div className="space-y-4">
      <PipelineFlowGraph stages={flowStages} simulation />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {eventCount != null && (
          <StatCard label="Event count" value={typeof eventCount === "number" ? eventCount.toLocaleString() : String(eventCount)} />
        )}
        {pattern && <StatCard label="Event pattern" value={pattern} />}
        {replay && <StatCard label="Replay mode" value={replay} />}
        {lateRatio != null && lateRatio > 0 && (
          <StatCard label="Late arrival ratio" value={lateRatio.toFixed(2)} />
        )}
        {streams != null && streams > 1 && (
          <StatCard label="Parallel streams" value={String(streams)} />
        )}
      </div>
      {(timeStart || timeEnd) && (
        <p className="text-sm text-slate-600">
          Time window: {timeStart ?? "—"} → {timeEnd ?? "—"}
        </p>
      )}
      {eventStreamArtifacts.length > 0 && runId && (
        <Link href={`/artifacts?run=${runId}&type=event_stream`}>
          <Button variant="outline" size="sm">View event streams</Button>
        </Link>
      )}
    </div>
  );
}
