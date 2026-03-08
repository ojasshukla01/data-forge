"use client";

export interface PipelineStage {
  id: string;
  label: string;
  status?: "pending" | "running" | "completed" | "skipped" | "failed";
}

interface PipelineFlowGraphProps {
  stages?: PipelineStage[];
  /** If true, shows simulation-style flow */
  simulation?: boolean;
  className?: string;
}

const DEFAULT_STAGES: PipelineStage[] = [
  { id: "generation", label: "Generation" },
  { id: "transform", label: "Transform" },
  { id: "validate", label: "Validate" },
  { id: "export", label: "Export" },
  { id: "load", label: "Load" },
  { id: "complete", label: "Complete" },
];

const SIMULATION_STAGES: PipelineStage[] = [
  { id: "source_events", label: "Source events" },
  { id: "transform", label: "Transformation" },
  { id: "validate", label: "Validation" },
  { id: "warehouse", label: "Warehouse" },
];

export function PipelineFlowGraph({ stages, simulation, className }: PipelineFlowGraphProps) {
  const list = stages?.length
    ? stages
    : simulation
      ? SIMULATION_STAGES
      : DEFAULT_STAGES;

  return (
    <div className={className}>
      <div className="flex flex-wrap items-center gap-2">
        {list.map((stage, idx) => {
          const isLast = idx === list.length - 1;
          const status = stage.status ?? "pending";
          const dotColor =
            status === "completed"
              ? "bg-green-500"
              : status === "running"
                ? "bg-blue-500 animate-pulse"
                : status === "failed"
                  ? "bg-red-500"
                  : status === "skipped"
                    ? "bg-slate-300"
                    : "bg-slate-300";
          return (
            <span key={stage.id} className="flex items-center gap-1.5">
              <span className="flex items-center gap-1.5">
                <span className={`inline-block w-2 h-2 rounded-full shrink-0 ${dotColor}`} aria-hidden />
                <span
                  className={`text-sm font-medium ${
                    status === "completed"
                      ? "text-slate-900"
                      : status === "running"
                        ? "text-blue-700"
                        : status === "failed"
                          ? "text-red-700"
                          : "text-slate-500"
                  }`}
                >
                  {stage.label}
                </span>
              </span>
              {!isLast && (
                <span className="text-slate-300 text-sm mx-0.5" aria-hidden>
                  →
                </span>
              )}
            </span>
          );
        })}
      </div>
    </div>
  );
}
