"use client";

/**
 * CodeBlock — Monospace code display with copy button. Uses JetBrains Mono (font-mono).
 * Use for JSON preview, manifest, CLI output. copyable shows Copy button.
 */
import { useState } from "react";
import { cn } from "@/lib/utils";

interface CodeBlockProps {
  children: string;
  language?: string;
  className?: string;
  copyable?: boolean;
}

export function CodeBlock({ children, language, className, copyable = true }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div
      className={cn(
        "relative rounded-lg border border-slate-200 bg-slate-900 overflow-hidden",
        className
      )}
    >
      {(language || copyable) && (
        <div className="flex items-center justify-between px-3 py-2 border-b border-slate-700 bg-slate-800/50">
          {language && <span className="text-xs text-slate-400 font-mono">{language}</span>}
          {copyable && (
            <button
              onClick={handleCopy}
              className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              {copied ? "Copied" : "Copy"}
            </button>
          )}
        </div>
      )}
      <pre className="p-4 overflow-x-auto overflow-y-auto max-h-96 font-mono text-sm text-slate-100 text-code">
        <code className="tabular-nums">{children}</code>
      </pre>
    </div>
  );
}
