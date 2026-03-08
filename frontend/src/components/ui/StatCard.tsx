import { cn } from "@/lib/utils";

/**
 * StatCard — Display a metric with label. Use for run summary, benchmarks, dashboards.
 * value can be string, number, or ReactNode (e.g. Badge). subvalue for units or context.
 */
interface StatCardProps {
  label: string;
  value: string | number | React.ReactNode;
  subvalue?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function StatCard({ label, value, subvalue, icon, className }: StatCardProps) {
  const isReactNode = typeof value !== "string" && typeof value !== "number";
  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 bg-white p-4 shadow-sm min-w-0 overflow-hidden",
        className
      )}
    >
      <p className="text-sm text-slate-500 truncate">{label}</p>
      <div className="mt-1 flex items-baseline gap-2 min-w-0">
        {icon && <span className="text-slate-400 shrink-0">{icon}</span>}
        <div className={cn(
          "text-xl font-semibold text-slate-900 tabular-nums min-w-0",
          !isReactNode && "truncate"
        )}>
          {value}
        </div>
        {subvalue && (
          <span className="text-sm text-slate-500 shrink-0 truncate">{subvalue}</span>
        )}
      </div>
    </div>
  );
}
