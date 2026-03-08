"use client";

import Link from "next/link";
import Image from "next/image";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/create/wizard", label: "Create" },
  { href: "/create/advanced", label: "Advanced" },
  { href: "/templates", label: "Templates" },
  { href: "/runs", label: "Runs" },
  { href: "/artifacts", label: "Artifacts" },
  { href: "/validate", label: "Validate" },
  { href: "/schema", label: "Schema" },
  { href: "/integrations", label: "Integrations" },
  { href: "/docs", label: "Docs" },
  { href: "/about", label: "About" },
];

export function TopNav() {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/90">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 font-semibold text-slate-900 group">
          <Image src="/branding/logo-mark.svg" alt="" width={28} height={28} className="group-hover:opacity-90" />
          <span className="text-slate-900">Data Forge</span>
        </Link>
        <nav className="hidden md:flex items-center gap-0.5">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-3 py-2 text-sm font-medium rounded-md text-slate-600 hover:text-[var(--brand-teal)] hover:bg-slate-50 transition-colors"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <a
          href="https://github.com/ojasshukla01/data-forge"
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-600 hover:text-slate-900 px-2 py-1 text-sm"
          aria-label="GitHub"
        >
          <span className="inline-flex items-center gap-1">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
            <span className="hidden sm:inline text-xs">Open source</span>
          </span>
        </a>
      </div>
    </header>
  );
}
