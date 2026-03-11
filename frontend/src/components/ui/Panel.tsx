import { cn } from "@/lib/utils";

/**
 * Panel — Bordered container with optional title. Use for sidebars, form sections, or detail views.
 * sidebar=true adds a left accent border.
 */
interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  sidebar?: boolean;
}

export function Panel({ title, sidebar, className, children, ...props }: PanelProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden",
        sidebar && "border-l-4 border-l-[var(--brand-teal)]",
        className
      )}
      {...props}
    >
      {title && (
        <div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
          <h3 className="text-sm font-medium text-slate-900">{title}</h3>
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}
