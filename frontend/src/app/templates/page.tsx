"use client";

import { useCallback, useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import {
  fetchTemplates,
  fetchPacks,
  fetchCustomSchemas,
  addTemplateFromPack,
  addTemplateFromSchema,
  removeTemplate,
  fetchHiddenTemplates,
  unhideTemplate,
  type PackInfo,
} from "@/lib/api";

function normalizeCategory(c?: string): string {
  if (!c) return "";
  return c.trim().toLowerCase().replace(/\s+/g, "");
}

export default function TemplatesPage() {
  const [packs, setPacks] = useState<PackInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [addModal, setAddModal] = useState<"pack" | "schema" | null>(null);
  const [addDropdownOpen, setAddDropdownOpen] = useState(false);
  const [packOptions, setPackOptions] = useState<PackInfo[]>([]);
  const [schemaOptions, setSchemaOptions] = useState<{ id: string; name: string }[]>([]);
  const [hiddenIds, setHiddenIds] = useState<string[]>([]);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadTemplates = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchTemplates()
      .then(setPacks)
      .catch((e) => {
        setPacks([]);
        setError(e instanceof Error ? e.message : "Failed to load templates");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  useEffect(() => {
    fetchHiddenTemplates().then(setHiddenIds).catch(() => setHiddenIds([]));
  }, [packs]);

  const filteredPacks = useMemo(() => {
    if (!categoryFilter) return packs;
    const norm = normalizeCategory(categoryFilter);
    return packs.filter((p) => normalizeCategory(p.category) === norm || p.category?.toLowerCase() === categoryFilter.toLowerCase());
  }, [packs, categoryFilter]);

  const uniqueCategories = useMemo(() => {
    const seen = new Set<string>();
    packs.forEach((p) => { if (p.category) seen.add(p.category); });
    return Array.from(seen).sort();
  }, [packs]);

  const openAddFromPack = () => {
    setAddModal("pack");
    fetchPacks().then(setPackOptions).catch(() => setPackOptions([]));
  };

  const openAddFromSchema = () => {
    setAddModal("schema");
    fetchCustomSchemas().then((list) => setSchemaOptions(list.map((s) => ({ id: s.id, name: s.name })))).catch(() => setSchemaOptions([]));
  };

  const handleAddFromPack = async (packId: string) => {
    setActionLoading(packId);
    setError(null);
    try {
      await addTemplateFromPack(packId);
      setAddModal(null);
      loadTemplates();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add template");
    } finally {
      setActionLoading(null);
    }
  };

  const handleAddFromSchema = async (schemaId: string) => {
    setActionLoading(schemaId);
    setError(null);
    try {
      await addTemplateFromSchema(schemaId);
      setAddModal(null);
      loadTemplates();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add template");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRemove = async (id: string) => {
    const t = packs.find((x) => x.id === id);
    const label = t?.name ?? id.replace(/_/g, " ");
    if (!window.confirm(t?.source === "user" ? `Remove template "${label}" from list?` : `Hide template "${label}" from your list?`)) return;
    setActionLoading(id);
    setError(null);
    try {
      await removeTemplate(id);
      loadTemplates();
      if (hiddenIds.length > 0) fetchHiddenTemplates().then(setHiddenIds);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remove");
    } finally {
      setActionLoading(null);
    }
  };

  const handleUnhide = async (id: string) => {
    setActionLoading(id);
    setError(null);
    try {
      await unhideTemplate(id);
      setHiddenIds((prev) => prev.filter((x) => x !== id));
      loadTemplates();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to restore");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Templates</h1>
          <p className="mt-1.5 text-slate-600 text-sm sm:text-base">Domain packs and your custom templates. Add, edit, or remove to match your needs.</p>
        </div>
        <div className="flex gap-2 shrink-0">
          <div className="relative">
            <Button size="sm" onClick={() => setAddDropdownOpen((v) => !v)}>Add template</Button>
            {addDropdownOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setAddDropdownOpen(false)} aria-hidden />
                <div className="absolute right-0 mt-1 w-48 rounded-lg border border-slate-200 bg-white shadow-lg py-1 z-20">
                  <button type="button" onClick={() => { openAddFromPack(); setAddDropdownOpen(false); }} className="block w-full text-left px-3 py-2 text-sm hover:bg-slate-50">From domain pack</button>
                  <button type="button" onClick={() => { openAddFromSchema(); setAddDropdownOpen(false); }} className="block w-full text-left px-3 py-2 text-sm hover:bg-slate-50">From Schema Studio</button>
                </div>
              </>
            )}
          </div>
          <Link href="/schema/studio"><Button variant="outline" size="sm">Schema Studio</Button></Link>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">{error}</div>
      )}

      {addModal === "pack" && (
        <Card>
          <CardHeader className="flex flex-row justify-between">
            <CardTitle className="text-base">Add template from domain pack</CardTitle>
            <button type="button" onClick={() => setAddModal(null)} className="text-slate-500 hover:text-slate-700">×</button>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600 mb-3">Clone a built-in pack to your templates. You can then edit it in Schema Studio.</p>
            <div className="flex flex-wrap gap-2">
              {packOptions.filter((p) => !packs.some((t) => t.id === p.id && t.source === "user")).map((p) => (
                <Button key={p.id} size="sm" variant="outline" onClick={() => handleAddFromPack(p.id)} disabled={!!actionLoading}>
                  {actionLoading === p.id ? "Adding…" : p.name ?? p.id}
                </Button>
              ))}
              {packOptions.length === 0 && <p className="text-sm text-slate-500">No packs available.</p>}
            </div>
          </CardContent>
        </Card>
      )}

      {addModal === "schema" && (
        <Card>
          <CardHeader className="flex flex-row justify-between">
            <CardTitle className="text-base">Add template from Schema Studio</CardTitle>
            <button type="button" onClick={() => setAddModal(null)} className="text-slate-500 hover:text-slate-700">×</button>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-600 mb-3">Add an existing custom schema as a template.</p>
            <div className="flex flex-wrap gap-2">
              {schemaOptions.filter((s) => !packs.some((t) => t.id === s.id && t.source === "user")).map((s) => (
                <Button key={s.id} size="sm" variant="outline" onClick={() => handleAddFromSchema(s.id)} disabled={!!actionLoading}>
                  {actionLoading === s.id ? "Adding…" : s.name}
                </Button>
              ))}
              {schemaOptions.length === 0 && <p className="text-sm text-slate-500">No custom schemas. Create one in Schema Studio first.</p>}
            </div>
          </CardContent>
        </Card>
      )}

      {hiddenIds.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm">
          <span className="text-amber-800">Hidden templates: </span>
          {hiddenIds.map((id) => (
            <button key={String(id)} type="button" onClick={() => handleUnhide(String(id))} disabled={!!actionLoading} className="mr-2 text-[var(--brand-teal)] hover:underline">
              {actionLoading === id ? "Restoring…" : String(id).replace(/_/g, " ")}
            </button>
          ))}
        </div>
      )}

      {!loading && packs.length > 0 && (
        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-sm text-slate-500">Filter by category:</span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono"
          >
            <option value="">All categories</option>
            {uniqueCategories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          {categoryFilter && (
            <button type="button" onClick={() => setCategoryFilter("")} className="text-xs text-slate-500 hover:text-slate-700">Clear</button>
          )}
        </div>
      )}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-40 rounded-xl border border-slate-200 bg-slate-50 animate-pulse" />
          ))}
        </div>
      ) : packs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-slate-600">Could not load templates.</p>
            <p className="text-sm text-slate-500 mt-2">Ensure the API is running at <code className="bg-slate-100 px-1.5 py-0.5 rounded font-mono text-xs">http://localhost:8000</code></p>
          </CardContent>
        </Card>
      ) : filteredPacks.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-slate-600">No templates match the selected category.</p>
            <button type="button" onClick={() => setCategoryFilter("")} className="text-[var(--brand-teal)] hover:underline mt-2 text-sm">Clear filter</button>
          </CardContent>
        </Card>
      ) : (
        <>
          <p className="text-sm text-slate-500">
            Showing {filteredPacks.length} of {packs.length} template{filteredPacks.length !== 1 ? "s" : ""}
            {categoryFilter ? ` in ${categoryFilter}` : ""}
          </p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredPacks.map((p) => (
              <Card key={p.id} className="h-full flex flex-col">
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <Link href={`/templates/${p.id}`} className="flex-1 min-w-0">
                      <CardTitle className="capitalize text-lg hover:text-[var(--brand-teal)] transition-colors">{p.name ?? p.id.replace(/_/g, " ")}</CardTitle>
                    </Link>
                    <div className="flex gap-1 shrink-0">
                      {p.source === "user" ? (
                        <>
                          <Link href={`/schema/studio?schema=${p.id}`}><Button variant="ghost" size="sm">Edit</Button></Link>
                          <Button variant="ghost" size="sm" className="text-red-600 hover:bg-red-50" onClick={() => handleRemove(p.id)} disabled={!!actionLoading}>Remove</Button>
                        </>
                      ) : (
                        <Button variant="ghost" size="sm" className="text-slate-600" onClick={() => handleRemove(p.id)} disabled={!!actionLoading} title="Hide from list">Hide</Button>
                      )}
                    </div>
                  </div>
                  {p.category && (
                    <span className="inline-block mt-1 px-2 py-0.5 rounded-md text-xs font-medium bg-[var(--brand-teal)]/10 text-[var(--brand-teal)] w-fit">{p.category}</span>
                  )}
                </CardHeader>
                <CardContent className="flex-1 flex flex-col">
                  <Link href={`/templates/${p.id}`} className="flex-1">
                    <p className="text-sm text-slate-600 line-clamp-3">{p.description}</p>
                    <div className="flex flex-wrap gap-x-3 gap-y-1 mt-3 text-xs text-slate-500">
                      {p.tables_count != null && <span>{p.tables_count} tables</span>}
                      {p.relationships_count != null && <span>· {p.relationships_count} relationships</span>}
                      {p.key_entities && p.key_entities.length > 0 && (
                        <span>· {p.key_entities.slice(0, 3).join(", ")}{p.key_entities.length > 3 ? "…" : ""}</span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-[var(--brand-teal)] mt-3">View template →</p>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
