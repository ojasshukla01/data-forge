import { cn } from "@/lib/utils";

/**
 * EmptyState — Shown when no data. Use title, description, optional action (Button) and icon.
 * Use in runs list, artifacts, templates when empty.
 */
interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

export function EmptyState({ title = "No data", description, action, icon, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-12 px-6 text-center",
        className
      )}
    >
      {icon && <div className="mb-4 text-slate-400">{icon}</div>}
      <p className="text-slate-900 font-medium">{title}</p>
      {description && (
        <p className="mt-2 text-sm text-slate-600 max-w-sm">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
