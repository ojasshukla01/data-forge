import { forwardRef } from "react";
import { cn } from "@/lib/utils";

/**
 * Button — Primary actions (primary), secondary (outline), or low-emphasis (ghost).
 * Use size sm/md/lg for hierarchy. Always use for CTAs and form submissions.
 */
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white disabled:opacity-50 disabled:pointer-events-none",
        {
          "bg-[var(--brand-teal)] text-white hover:bg-[var(--brand-deep-blue)] focus:ring-[var(--brand-teal)] border border-transparent": variant === "primary",
          "bg-slate-100 text-slate-900 hover:bg-slate-200 focus:ring-slate-300 border border-transparent": variant === "secondary",
          "border border-slate-300 text-slate-700 bg-white hover:bg-slate-50 focus:ring-slate-300": variant === "outline",
          "text-slate-700 hover:bg-slate-100 focus:ring-slate-300": variant === "ghost",
        },
        {
          "px-3 py-1.5 text-sm min-h-[32px]": size === "sm",
          "px-4 py-2 text-sm min-h-[40px]": size === "md",
          "px-6 py-3 text-base min-h-[48px]": size === "lg",
        },
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
