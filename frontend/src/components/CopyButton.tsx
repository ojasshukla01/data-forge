"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface CopyButtonProps {
  text: string;
  label?: string;
  size?: "sm" | "md";
  variant?: "icon" | "text";
  className?: string;
  title?: string;
}

export function CopyButton({
  text,
  label = "Copy",
  size = "sm",
  variant = "text",
  className,
  title,
}: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleClick = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      title={title ?? `Copy ${label}`}
      className={cn(
        "inline-flex items-center gap-1.5 transition-colors",
        size === "sm" && "text-xs",
        size === "md" && "text-sm",
        "text-slate-500 hover:text-slate-700 font-mono",
        className
      )}
    >
      {variant === "icon" && <span className="sr-only">{copied ? "Copied" : label}</span>}
      {variant === "text" && (copied ? "Copied" : label)}
      <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    </button>
  );
}
