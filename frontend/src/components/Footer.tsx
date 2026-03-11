"use client";

import Link from "next/link";

const productLinks = [
  { href: "/create/wizard", label: "Create" },
  { href: "/create/advanced", label: "Advanced" },
  { href: "/docs", label: "Docs" },
  { href: "/templates", label: "Templates" },
  { href: "/scenarios", label: "Scenarios" },
  { href: "/runs", label: "Runs" },
  { href: "/artifacts", label: "Artifacts" },
  { href: "/schema/studio", label: "Schema Studio" },
];

const resourceLinks = [
  { href: "/about", label: "About" },
  { href: "https://github.com/ojasshukla01/data-forge", label: "GitHub", external: true },
];

const contributeLinks = [
  { href: "https://github.com/ojasshukla01/data-forge/issues", label: "Report an issue", external: true },
  { href: "https://github.com/ojasshukla01/data-forge/pulls", label: "Submit a PR", external: true },
  { href: "https://github.com/ojasshukla01/data-forge", label: "Contribute on GitHub", external: true },
];

const currentYear = new Date().getFullYear();

export function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-slate-50/30">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-10 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="font-semibold text-slate-900">Data Forge</p>
            <p className="mt-1 text-sm text-slate-600 max-w-xs leading-relaxed">
              Schema-aware synthetic data for databases, APIs, and pipelines. Realistic, relational, privacy-safe.
            </p>
            <p className="mt-3 text-xs text-slate-500">
              © {currentYear} Open source · Built by{" "}
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
          <div className="flex gap-12">
            <div>
              <p className="text-sm font-medium text-slate-900 mb-3">Product</p>
              <ul className="space-y-2">
                {productLinks.map((l) => (
                  <li key={l.href}>
                    <Link
                      href={l.href}
                      className="text-sm text-slate-600 hover:text-[var(--brand-teal)]"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900 mb-3">Resources</p>
              <ul className="space-y-2">
                {resourceLinks.map((l) => (
                  <li key={l.href}>
                    {l.external ? (
                      <a
                        href={l.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-slate-600 hover:text-[var(--brand-teal)] inline-flex items-center gap-1"
                      >
                        {l.label}
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    ) : (
                      <Link
                        href={l.href}
                        className="text-sm text-slate-600 hover:text-[var(--brand-teal)]"
                      >
                        {l.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-900 mb-3">Contribute</p>
              <ul className="space-y-2">
                {contributeLinks.map((l) => (
                  <li key={l.href}>
                    <a
                      href={l.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-slate-600 hover:text-[var(--brand-teal)] inline-flex items-center gap-1"
                    >
                      {l.label}
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
