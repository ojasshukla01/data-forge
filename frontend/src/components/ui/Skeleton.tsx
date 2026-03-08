import { cn } from "@/lib/utils";

/**
 * Skeleton — Loading placeholder. Variants: rect (default), text, circle.
 * Use while data loads (templates, runs, pack detail).
 */
interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "rect" | "circle";
}

export function Skeleton({ variant = "rect", className, ...props }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse bg-slate-200",
        variant === "text" && "h-4 rounded",
        variant === "rect" && "rounded-lg",
        variant === "circle" && "rounded-full",
        className
      )}
      {...props}
    />
  );
}
