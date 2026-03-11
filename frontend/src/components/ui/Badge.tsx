import { cn } from "@/lib/utils";

/**
 * Badge — Status/category chips. Variants: success, warning, error, info, category, benchmark.
 * Use for run status, pack categories, feature tags.
 */
type BadgeVariant = "category" | "success" | "warning" | "error" | "benchmark" | "info";

const variantStyles: Record<BadgeVariant, string> = {
  category: "bg-[var(--brand-teal)]/10 text-[var(--brand-teal)]",
  success: "bg-emerald-500/10 text-emerald-700",
  warning: "bg-amber-500/10 text-amber-700",
  error: "bg-red-500/10 text-red-700",
  benchmark: "bg-[var(--brand-accent)]/10 text-[var(--brand-accent)]",
  info: "bg-slate-500/10 text-slate-700",
};

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({ variant = "category", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
}
