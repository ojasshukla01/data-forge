import { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none",
        {
          "bg-[var(--brand-teal)] text-white hover:bg-[var(--brand-deep-blue)] focus:ring-[var(--brand-teal)]": variant === "primary",
          "bg-slate-100 text-slate-900 hover:bg-slate-200 focus:ring-slate-400": variant === "secondary",
          "border border-slate-300 bg-transparent hover:bg-slate-50 focus:ring-slate-400": variant === "outline",
          "hover:bg-slate-100 focus:ring-slate-400": variant === "ghost",
        },
        {
          "px-3 py-1.5 text-sm": size === "sm",
          "px-4 py-2 text-sm": size === "md",
          "px-6 py-3 text-base": size === "lg",
        },
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";
