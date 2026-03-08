"use client";

import Link from "next/link";

const quickLinks = [
  { href: "/create/wizard", label: "Create" },
  { href: "/templates", label: "Templates" },
  { href: "/runs", label: "Runs" },
  { href: "/docs", label: "Docs" },
  { href: "/about", label: "About" },
];

export function Footer() {
  return (
    <footer className="mt-16 border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="font-semibold text-slate-900">Data Forge</p>
            <p className="mt-1 text-sm text-slate-600 max-w-xs">
              Schema-aware synthetic data platform for databases, APIs, and pipelines.
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Open source · Built by{" "}
              <a
                href="https://github.com/ojasshukla01"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[var(--brand-teal)] hover:underline"
              >
                Ojas Shukla
              </a>
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-900 mb-3">Quick links</p>
            <ul className="space-y-2">
              {quickLinks.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="text-sm text-slate-600 hover:text-[var(--brand-teal)]">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
            <a
              href="https://github.com/ojasshukla01/data-forge"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 mt-4 text-sm text-slate-600 hover:text-[var(--brand-teal)]"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
              GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
