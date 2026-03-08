import { cn } from "@/lib/utils";

/**
 * Divider — Horizontal rule. Use label for "or" or section breaks. Omit label for simple hr.
 */
interface DividerProps {
  className?: string;
  label?: string;
}

export function Divider({ className, label }: DividerProps) {
  if (label) {
    return (
      <div className={cn("flex items-center gap-4 my-4", className)}>
        <div className="flex-1 h-px bg-slate-200" />
        <span className="text-sm text-slate-500">{label}</span>
        <div className="flex-1 h-px bg-slate-200" />
      </div>
    );
  }
  return <hr className={cn("border-0 border-t border-slate-200", className)} />;
}
