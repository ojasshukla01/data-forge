"use client";

import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

export interface LogEvent {
  level: string;
  message: string;
  ts?: number;
}

interface LogPanelProps {
  events: LogEvent[];
  className?: string;
}

const LEVEL_COLORS: Record<string, string> = {
  info: "text-blue-400",
  warn: "text-amber-400",
  warning: "text-amber-400",
  error: "text-red-400",
  debug: "text-slate-500",
};

export function LogPanel({ events, className }: LogPanelProps) {
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events, autoScroll]);

  const handleCopy = () => {
    const text = events
      .map((e) => {
        const ts = e.ts ? new Date(e.ts * 1000).toISOString().slice(11, 23) : "";
        return `[${ts}] ${(e.level ?? "info").toUpperCase()} ${e.message}`;
      })
      .join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className={cn("rounded-lg border border-slate-200 bg-slate-900 overflow-hidden", className)}>
      <div className="flex items-center justify-between px-3 py-2 border-b border-slate-700 bg-slate-800/50">
        <span className="text-xs text-slate-400 font-mono">Logs</span>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-xs text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded border-slate-500"
            />
            Auto-scroll
          </label>
          <button
            onClick={handleCopy}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors font-mono"
          >
            {copied ? "Copied" : "Copy logs"}
          </button>
        </div>
      </div>
      <div
        ref={containerRef}
        className="space-y-0.5 max-h-64 overflow-y-auto p-3 font-mono text-xs text-code"
      >
        {events.map((e, i) => (
          <div key={i} className="flex gap-3 flex-wrap">
            {e.ts != null && (
              <span className="text-slate-500 shrink-0 tabular-nums">
                {new Date(e.ts * 1000).toISOString().slice(11, 23)}
              </span>
            )}
            <span
              className={cn(
                "shrink-0 w-14 uppercase font-medium",
                LEVEL_COLORS[e.level?.toLowerCase() ?? ""] ?? "text-slate-400"
              )}
            >
              {e.level ?? "info"}
            </span>
            <span className="text-slate-200 break-words">{e.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
