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
  const psSummary = (result?.pipeline_simulation_summary ?? result?.simulation_summary) as Record<string, unknown> | undefined;
  if (!sim.enabled && !result?.event_stream_count && !psSummary) return null;

  const eventCount = (result?.event_stream_count as number) ?? psSummary?.event_stream_count as number;
  const linkedCount = psSummary?.linked_unstructured_count as number | undefined;
  const coverageRatio = psSummary?.linked_unstructured_coverage_ratio as number | undefined;
  const orphanLinks = psSummary?.linked_unstructured_orphan_links as number | undefined;
  const timeWindow = psSummary?.time_window as Record<string, string> | undefined;
  const timeStart = (result?.time_window_start as string) ?? timeWindow?.start;
  const timeEnd = (result?.time_window_end as string) ?? timeWindow?.end;
  const pattern = (sim.event_pattern as string) ?? (result?.event_pattern as string) ?? psSummary?.event_pattern as string;
  const replay = (sim.replay_mode as string) ?? (result?.replay_mode as string) ?? psSummary?.replay_mode as string;
  const lateRatio = (sim.late_arrival_ratio as number) ?? (result?.late_arrival_ratio as number) ?? psSummary?.late_arrival_ratio as number;
  const streams = (sim.parallel_streams as number) ?? (result?.parallel_streams as number);
  const stages = stageProgress ?? (config?.stage_progress ?? result?.stage_progress) as { name: string; status: string }[] | undefined;
  const eventStreamArtifacts = artifacts?.filter((a) => a.type === "event_stream" || a.path?.includes("event_stream") || a.path?.endsWith("events.jsonl")) ?? [];
  const unstructuredArtifacts = artifacts?.filter((a) => a.type === "unstructured" || a.path?.includes("unstructured") || a.path?.includes("support_tickets")) ?? [];

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
        {linkedCount != null && linkedCount > 0 && (
          <StatCard label="Linked notes" value={linkedCount.toLocaleString()} />
        )}
        {coverageRatio != null && (
          <StatCard label="Link coverage" value={`${(coverageRatio * 100).toFixed(1)}%`} />
        )}
        {orphanLinks != null && orphanLinks > 0 && (
          <StatCard label="Orphan links" value={String(orphanLinks)} />
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
      <div className="flex flex-wrap gap-2">
        {eventStreamArtifacts.length > 0 && runId && (
          <Link href={`/artifacts?run=${runId}&type=event_stream`}>
            <Button variant="outline" size="sm">View event streams</Button>
          </Link>
        )}
        {unstructuredArtifacts.length > 0 && runId && (
          <Link href={`/artifacts?run=${runId}&type=unstructured`}>
            <Button variant="outline" size="sm">View linked notes</Button>
          </Link>
        )}
      </div>
    </div>
  );
}
