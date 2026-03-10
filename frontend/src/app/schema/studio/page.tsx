"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import {
  fetchCustomSchemas,
  fetchCustomSchema,
  createCustomSchema,
  updateCustomSchema,
  type CustomSchemaSummary,
  type CustomSchemaDetail,
} from "@/lib/api";

function SchemaList({
  schemas,
  onSelect,
}: {
  schemas: CustomSchemaSummary[];
  onSelect: (id: string) => void;
}) {
  if (schemas.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-sm text-slate-600">
          No custom schemas yet. Create one to start designing your own data model.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Custom schemas</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {schemas.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onSelect(s.id)}
            className="w-full text-left px-3 py-2 rounded-lg border border-slate-200 hover:border-[var(--brand-teal)]/50 hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-slate-900 truncate">{s.name}</span>
              <span className="text-xs text-slate-500 font-mono">v{s.version}</span>
            </div>
            {s.description && (
              <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">{s.description}</p>
            )}
          </button>
        ))}
      </CardContent>
    </Card>
  );
}

function SchemaEditor({
  schema,
  onChange,
  onSave,
  saving,
}: {
  schema: CustomSchemaDetail | null;
  onChange: (next: CustomSchemaDetail) => void;
  onSave: () => void;
  saving: boolean;
}) {
  const [jsonText, setJsonText] = useState<string>(() =>
    schema ? JSON.stringify(schema.schema, null, 2) : "{\n  \"name\": \"example\",\n  \"tables\": [],\n  \"relationships\": []\n}",
  );
  const [jsonError, setJsonError] = useState<string | null>(null);

  useEffect(() => {
    if (schema) {
      setJsonText(JSON.stringify(schema.schema, null, 2));
      setJsonError(null);
    }
  }, [schema?.id]);

  const safeParse = () => {
    try {
      const parsed = JSON.parse(jsonText) as Record<string, unknown>;
      if (!schema) return;
      onChange({ ...schema, schema: parsed });
      setJsonError(null);
      return true;
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : "Invalid JSON");
      return false;
    }
  };

  return (
    <Card className="flex-1">
      <CardHeader>
        <CardTitle>Schema editor</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {schema && (
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Name</label>
              <input
                type="text"
                value={schema.name}
                onChange={(e) => onChange({ ...schema, name: e.target.value })}
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
                placeholder="e.g. Customer 360"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Tags (comma separated)</label>
              <input
                type="text"
                value={(schema.tags ?? []).join(", ")}
                onChange={(e) =>
                  onChange({
                    ...schema,
                    tags: e.target.value
                      .split(",")
                      .map((t) => t.trim())
                      .filter(Boolean),
                  })
                }
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
                placeholder="analytics, customer"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-slate-700 mb-1">Description</label>
              <input
                type="text"
                value={schema.description ?? ""}
                onChange={(e) => onChange({ ...schema, description: e.target.value })}
                className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
                placeholder="Short description of this schema"
              />
            </div>
          </div>
        )}
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Schema JSON (tables, columns, relationships)
          </label>
          <textarea
            value={jsonText}
            onChange={(e) => setJsonText(e.target.value)}
            onBlur={safeParse}
            rows={18}
            className="w-full rounded border border-slate-300 px-3 py-2 text-xs font-mono resize-y"
          />
          {jsonError && <p className="mt-1 text-xs text-red-600">JSON error: {jsonError}</p>}
        </div>
        <div className="flex justify-end gap-2">
          <Link href="/create/advanced" className="text-xs text-slate-500 hover:text-slate-700">
            Use with Advanced config →
          </Link>
          <Button
            size="sm"
            onClick={() => {
              const ok = safeParse();
              if (ok) onSave();
            }}
            disabled={saving}
          >
            {saving ? "Saving…" : "Save schema"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function SchemaStudioPage() {
  const router = useRouter();
  const [schemas, setSchemas] = useState<CustomSchemaSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editing, setEditing] = useState<CustomSchemaDetail | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchCustomSchemas()
      .then(setSchemas)
      .catch((e) => {
        console.error(e);
        setSchemas([]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    setError(null);
    fetchCustomSchema(selectedId)
      .then((detail) => {
        if (!detail) return;
        setEditing(detail);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load schema"));
  }, [selectedId]);

  const handleCreateNew = () => {
    const blank: CustomSchemaDetail = {
      id: "",
      name: "New schema",
      description: "",
      tags: [],
      version: 1,
      schema: {
        name: "new_schema",
        tables: [],
        relationships: [],
      },
    };
    setSelectedId(null);
    setEditing(blank);
  };

  const handleSave = async () => {
    if (!editing) return;
    setSaving(true);
    setError(null);
    try {
      if (!editing.id) {
        const created = await createCustomSchema({
          name: editing.name,
          description: editing.description,
          tags: editing.tags,
          schema: editing.schema,
        });
        setSchemas((prev) => [created, ...prev]);
        setSelectedId(created.id);
        setEditing(created);
      } else {
        const updated = await updateCustomSchema(editing.id, {
          name: editing.name,
          description: editing.description,
          tags: editing.tags,
          schema: editing.schema,
        });
        setSchemas((prev) =>
          prev.map((s) => (s.id === updated.id ? { ...s, name: updated.name, description: updated.description, version: updated.version } : s)),
        );
        setEditing(updated);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save schema");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Schema Studio</h1>
          <p className="text-sm text-slate-600 mt-1">
            Design and manage custom relational schemas to use with Data Forge scenarios and runs.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => router.push("/templates")}>
            Browse domain packs
          </Button>
          <Button size="sm" onClick={handleCreateNew}>
            New schema
          </Button>
        </div>
      </div>
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}
      <div className="flex flex-col lg:flex-row gap-4 items-stretch">
        <div className="w-full lg:w-80 shrink-0 space-y-3">
          {loading ? (
            <Card>
              <CardContent className="py-8 text-sm text-slate-500">Loading schemas…</CardContent>
            </Card>
          ) : (
            <SchemaList schemas={schemas} onSelect={setSelectedId} />
          )}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">How this works</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-slate-600 space-y-1.5">
              <p>1. Define tables, columns, and relationships in the JSON editor.</p>
              <p>2. Save the schema; versions are tracked over time.</p>
              <p>3. Use the schema when configuring scenarios in Advanced config.</p>
            </CardContent>
          </Card>
        </div>
        <SchemaEditor schema={editing} onChange={setEditing} onSave={handleSave} saving={saving} />
      </div>
    </div>
  );
}

