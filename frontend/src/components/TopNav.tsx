"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import { Home, PlusCircle, FolderKanban, Play, FileOutput, BookOpen, Info, Settings, LayoutTemplate, Layers, FileCheck } from "lucide-react";
import { cn } from "@/lib/utils";

const mainNavItems: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/", label: "Home", icon: Home },
  { href: "/create/wizard", label: "Create", icon: PlusCircle },
  { href: "/scenarios", label: "Scenarios", icon: FolderKanban },
  { href: "/runs", label: "Runs", icon: Play },
  { href: "/artifacts", label: "Artifacts", icon: FileOutput },
  { href: "/docs", label: "Docs", icon: BookOpen },
  { href: "/about", label: "About", icon: Info },
];

const moreNavItems: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/create/advanced", label: "Advanced config", icon: Settings },
  { href: "/templates", label: "Templates", icon: LayoutTemplate },
  { href: "/schema/studio", label: "Schema Studio", icon: Layers },
  { href: "/schema", label: "Schema", icon: FileCheck },
  { href: "/validate", label: "Validate", icon: FileCheck },
];

function isActive(href: string, pathname: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(href + "/");
}

export function TopNav() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!moreOpen) return;
    const close = (e: MouseEvent) => {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) setMoreOpen(false);
    };
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [moreOpen]);

  const isMoreActive = moreNavItems.some((item) => isActive(item.href, pathname));

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/90">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 min-w-0">
        <Link href="/" className="flex items-center gap-2.5 font-semibold text-slate-900 group shrink-0 min-w-0" aria-label="Data Forge home">
          <Image src="/branding/logo-mark.svg" alt="" width={28} height={28} className="group-hover:opacity-90 shrink-0" />
          <span className="text-slate-900 truncate">Data Forge</span>
        </Link>
        <button
          type="button"
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 rounded-md text-slate-600 hover:bg-slate-100"
          aria-label="Toggle menu"
          aria-expanded={mobileOpen}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
            {mobileOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
        <nav className={cn(
          "items-center gap-0.5",
          mobileOpen ? "flex flex-col absolute top-14 left-0 right-0 py-4 bg-white border-b border-slate-200 shadow-md md:shadow-none md:relative md:top-0 md:flex-row md:py-0 md:border-b-0 md:bg-transparent" : "hidden md:flex"
        )}>
          {(mobileOpen ? [...mainNavItems, ...moreNavItems] : mainNavItems).map((item) => {
            const active = isActive(item.href, pathname);
            const IconComp = "icon" in item ? (item as { icon: LucideIcon }).icon : undefined;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "px-3 py-2 text-sm font-medium rounded-md transition-colors block md:inline-flex md:items-center gap-1.5",
                  active
                    ? "text-[var(--brand-teal)] bg-slate-100 ring-1 ring-[var(--brand-teal)]/20"
                    : "text-slate-600 hover:text-[var(--brand-teal)] hover:bg-slate-50"
                )}
                aria-current={active ? "page" : undefined}
              >
                {IconComp && <IconComp className="w-4 h-4 shrink-0 opacity-80" aria-hidden />}
                {item.label}
              </Link>
            );
          })}
          {!mobileOpen && (
            <div className="relative md:inline-block" ref={moreRef}>
              <button
                type="button"
                onClick={() => setMoreOpen(!moreOpen)}
                className={cn(
                  "px-3 py-2 text-sm font-medium rounded-md transition-colors inline-flex items-center gap-1",
                  (moreOpen || isMoreActive)
                    ? "text-[var(--brand-teal)] bg-slate-100 ring-1 ring-[var(--brand-teal)]/20"
                    : "text-slate-600 hover:text-[var(--brand-teal)] hover:bg-slate-50"
                )}
                aria-expanded={moreOpen}
                aria-haspopup="true"
              >
                More
                <svg className="w-4 h-4 ml-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {moreOpen && (
                <div className="absolute right-0 mt-1 w-52 py-1 bg-white border border-slate-200 rounded-lg shadow-lg z-50" role="menu">
                  {moreNavItems.map((item) => {
                    const active = isActive(item.href, pathname);
                    const IconComp = item.icon;
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setMoreOpen(false)}
                        className={cn(
                          "flex items-center gap-2 px-4 py-2 text-sm",
                          active ? "text-[var(--brand-teal)] bg-slate-50" : "text-slate-700 hover:bg-slate-50"
                        )}
                        role="menuitem"
                      >
                        <IconComp className="w-4 h-4 shrink-0 opacity-80" aria-hidden />
                        {item.label}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </nav>
        <a
          href="https://github.com/ojasshukla01/data-forge"
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-600 hover:text-slate-900 p-2 rounded-md hover:bg-slate-100"
          aria-label="GitHub repository"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden><path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/></svg>
        </a>
      </div>
    </header>
  );
}
