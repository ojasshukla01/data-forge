"use client";

import { cn } from "@/lib/utils";

/**
 * Tabs — Horizontal tab switcher. Use for Validation (schema/ge/reconcile) or section switching.
 * activeId controls selection; onSelect called when tab clicked.
 */
interface Tab {
  id: string;
  label: string;
  desc?: string;
}

interface TabsProps {
  tabs: Tab[];
  activeId: string;
  onSelect: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeId, onSelect, className }: TabsProps) {
  return (
    <div className={cn("flex gap-1 border-b border-slate-200", className)}>
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onSelect(t.id)}
          className={cn(
            "px-4 py-2 text-sm font-medium rounded-t-lg transition-all duration-200",
            activeId === t.id
              ? "bg-white text-slate-900 border-b-2 border-[var(--brand-teal)] -mb-px text-[var(--brand-teal)]"
              : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
