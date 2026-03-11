"use client";

interface BarData {
  label: string;
  value: number;
  max: number;
  color?: string;
}

export function BenchmarkBarChart({ bars }: { bars: BarData[] }) {
  const maxVal = Math.max(...bars.map((b) => b.max), 1);
  return (
    <div className="space-y-3">
      {bars.map((b) => (
        <div key={b.label} className="flex items-center gap-3">
          <span className="text-xs text-slate-500 w-24 shrink-0">{b.label}</span>
          <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${Math.min(100, (b.value / maxVal) * 100)}%`,
                backgroundColor: b.color ?? "var(--brand-teal)",
              }}
            />
          </div>
          <span className="text-xs font-mono tabular-nums text-slate-700 w-16 text-right">
            {b.value}
          </span>
        </div>
      ))}
    </div>
  );
}
