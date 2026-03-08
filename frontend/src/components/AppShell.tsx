"use client";

import { TopNav } from "./TopNav";
import { Footer } from "./Footer";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <TopNav />
      <main className="flex-1 mx-auto w-full min-w-0 max-w-7xl px-4 py-8 sm:px-6 lg:px-8 overflow-x-hidden">
        {children}
      </main>
      <Footer />
    </div>
  );
}
