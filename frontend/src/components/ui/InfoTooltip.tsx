"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface InfoTooltipProps {
  content: string;
  className?: string;
  size?: "sm" | "md";
}

export function InfoTooltip({ content, className, size = "sm" }: InfoTooltipProps) {
  const [visible, setVisible] = useState(false);

  const show = () => setVisible(true);
  const hide = () => setVisible(false);
  const toggle = () => setVisible((v) => !v);

  return (
    <span
      className={cn("relative inline-flex align-middle", className)}
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggle();
      }}
    >
      <span
        className={cn(
          "inline-flex items-center justify-center rounded-full bg-slate-300/80 text-slate-600 hover:bg-slate-400/90 transition-colors cursor-help",
          size === "sm" ? "w-4 h-4 text-[10px]" : "w-5 h-5 text-xs"
        )}
        aria-label={content}
        role="img"
      >
        i
      </span>
      {visible && (
        <span
          className={cn(
            "absolute z-50 left-1/2 -translate-x-1/2 bottom-full mb-2 px-3 py-2 text-xs font-normal text-slate-800 bg-slate-900 text-white rounded-lg shadow-lg whitespace-normal max-w-[280px] sm:max-w-[320px]",
            "after:absolute after:left-1/2 after:-translate-x-1/2 after:top-full after:border-4 after:border-transparent after:border-t-slate-900"
          )}
        >
          {content}
        </span>
      )}
    </span>
  );
}
