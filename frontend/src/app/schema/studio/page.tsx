"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Tabs } from "@/components/ui/Tabs";
import {
  fetchCustomSchemas,
  fetchCustomSchema,
  createCustomSchema,
  updateCustomSchema,
  fetchSchemaPreview,
  validateCustomSchema,
  fetchCustomSchemaVersions,
  fetchCustomSchemaDiff,
  type CustomSchemaSummary,
  type CustomSchemaDetail,
  type CustomSchemaValidateResponse,
  type CustomSchemaVersionsResponse,
  type CustomSchemaDiffResponse,
} from "@/lib/api";
import { SchemaFormEditor } from "./components/SchemaFormEditor";

function VersionHistoryCard({ schemaId }: { schemaId: string }) {
  const [expanded, setExpanded] = useState(false);
  const [versionsData, setVersionsData] = useState<CustomSchemaVersionsResponse | null>(null);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [leftVer, setLeftVer] = useState<number>(1);
  const [rightVer, setRightVer] = useState<number>(1);
  const [diffData, setDiffData] = useState<CustomSchemaDiffResponse | null>(null);
  const [diffLoading, setDiffLoading] = useState(false);

  useEffect(() => {
    if (!expanded || !schemaId) return;
    setVersionsLoading(true);
    fetchCustomSchemaVersions(schemaId)
      .then((d) => {
        setVersionsData(d);
        if (d?.versions?.length) {
          const cur = d.current_version;
          setLeftVer((prev) => (prev === 1 && cur > 1 ? Math.max(1, cur - 1) : prev));
          setRightVer(cur);
        }
      })
      .catch(() => setVersionsData(null))
      .finally(() => setVersionsLoading(false));
  }, [expanded, schemaId]);

  useEffect(() => {
    if (!schemaId || leftVer === rightVer) {
      setDiffData(null);
      return;
    }
    setDiffLoading(true);
    fetchCustomSchemaDiff(schemaId, leftVer, rightVer)
      .then(setDiffData)
      .catch(() => setDiffData(null))
      .finally(() => setDiffLoading(false));
  }, [schemaId, leftVer, rightVer]);

  const versions = versionsData?.versions ?? [];
  const currentVersion = versionsData?.current_version ?? 1;

  return (
    <Card>
      <CardHeader>
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-between w-full text-left"
        >
          <CardTitle className="text-base">Version history</CardTitle>
          <span className="text-slate-500 text-sm">{expanded ? "▼" : "▶"}</span>
        </button>
      </CardHeader>
      {expanded && (
        <CardContent className="space-y-4 pt-0">
          {versionsLoading ? (
            <p className="text-sm text-slate-500">Loading versions…</p>
          ) : versions.length <= 1 ? (
            <p className="text-sm text-slate-500">No version history yet. Save changes to create versions.</p>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-sm text-slate-600">Compare:</span>
                <select
                  value={leftVer}
                  onChange={(e) => setLeftVer(Number(e.target.value))}
                  className="rounded border border-slate-300 px-2 py-1 text-sm"
                >
                  {versions.map((v) => (
                    <option key={v.version} value={v.version}>
                      v{v.version} {v.version === currentVersion ? "(current)" : ""}
                    </option>
                  ))}
                </select>
                <span className="text-slate-400">→</span>
                <select
                  value={rightVer}
                  onChange={(e) => setRightVer(Number(e.target.value))}
                  className="rounded border border-slate-300 px-2 py-1 text-sm"
                >
                  {versions.map((v) => (
                    <option key={v.version} value={v.version}>
                      v{v.version} {v.version === currentVersion ? "(current)" : ""}
                    </option>
                  ))}
                </select>
              </div>
              {diffLoading ? (
                <p className="text-sm text-slate-500">Loading diff…</p>
              ) : diffData ? (
                <div className="rounded border border-slate-200 bg-slate-50 p-4 text-sm space-y-3">
                  <p className="font-medium text-slate-700">
                    Diff: v{diffData.left_version} → v{diffData.right_version}
                  </p>
                  {diffData.tables_added && diffData.tables_added.length > 0 && (
                    <div>
                      <span className="text-green-700 font-medium">Tables added:</span>{" "}
                      {diffData.tables_added.join(", ")}
                    </div>
                  )}
                  {diffData.tables_removed && diffData.tables_removed.length > 0 && (
                    <div>
                      <span className="text-red-700 font-medium">Tables removed:</span>{" "}
                      {diffData.tables_removed.join(", ")}
                    </div>
                  )}
                  {diffData.tables_modified && diffData.tables_modified.length > 0 && (
                    <div>
                      <span className="text-amber-700 font-medium">Tables modified:</span>
                      <ul className="list-disc list-inside mt-1 ml-2 space-y-1">
                        {diffData.tables_modified.map((m, i) => (
                          <li key={i}>
                            <span className="font-mono">{m.table}</span>:
                            {m.columns_added?.length ? ` +${m.columns_added.join(", ")}` : ""}
                            {m.columns_removed?.length ? ` -${m.columns_removed.join(", ")}` : ""}
                            {m.columns_modified?.length ? ` ~${m.columns_modified.join(", ")}` : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {(!diffData.tables_added || diffData.tables_added.length === 0) &&
                    (!diffData.tables_removed || diffData.tables_removed.length === 0) &&
                    (!diffData.tables_modified || diffData.tables_modified.length === 0) && (
                      <p className="text-slate-500">No structural changes between these versions.</p>
                    )}
                </div>
              ) : null}
            </>
          )}
        </CardContent>
      )}
    </Card>
  );
}

const HOW_IT_WORKS = (
  <>
    <p className="font-medium text-slate-800">Step 1: Choose or create a schema</p>
    <p className="text-slate-600 mt-0.5">Select an existing schema from the list above, or click &quot;New schema&quot; in the top bar. You must have a schema open before adding tables.</p>
    <p className="font-medium text-slate-800 mt-3">Step 2: Add tables and columns</p>
    <p className="text-slate-600 mt-0.5">Use the Tables tab to add tables. Then use the Columns tab to add columns to each table—set data type, nullable, primary key, and optional generation rules (faker, sequence, uuid).</p>
    <p className="font-medium text-slate-800 mt-3">Step 3: Define relationships</p>
    <p className="text-slate-600 mt-0.5">Use the Relationships tab to add foreign keys (from_table/from_columns → to_table/to_columns).</p>
    <p className="font-medium text-slate-800 mt-3">Step 4: Validate and save</p>
    <p className="text-slate-600 mt-0.5">Click Validate to check structure and rules. Fix any errors, then Save. Versions are tracked—use Version history to compare changes.</p>
    <p className="font-medium text-slate-800 mt-3">Step 5: Use in runs</p>
    <p className="text-slate-600 mt-0.5">Use with Create wizard (custom schema) or Advanced config. Your saved schema appears in the dropdown.</p>
  </>
);

function SchemaList({
  schemas,
  onSelect,
}: {
  schemas: CustomSchemaSummary[];
  onSelect: (id: string) => void;
}) {
  return (
    <div className="space-y-3">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Custom schemas</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="max-h-[min(320px,40vh)] overflow-y-auto px-4 pb-4 space-y-3">
            {schemas.length === 0 ? (
              <p className="text-sm text-slate-600 py-6">No custom schemas yet. Click &quot;New schema&quot; above to create one.</p>
            ) : (
              schemas.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => onSelect(s.id)}
                  className="w-full text-left px-3 py-2 rounded-lg border border-slate-200 hover:border-[var(--brand-teal)]/50 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-slate-900 truncate">{s.name}</span>
                    <span className="text-xs text-slate-500 font-mono shrink-0">v{s.version}</span>
                  </div>
                  {s.description && (
                    <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">{s.description}</p>
                  )}
                </button>
              ))
            )}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">How it works</CardTitle>
        </CardHeader>
        <CardContent className="text-xs text-slate-600 space-y-2">
          {HOW_IT_WORKS}
          <Link href="/create/wizard" className="block mt-3 text-[var(--brand-teal)] hover:underline">→ Start a run with this schema</Link>
        </CardContent>
      </Card>
    </div>
  );
}

function SchemaEditorWithMode({
  editing,
  setEditing,
  onSave,
  saving,
  onValidate,
  validateLoading,
  validationResult,
}: {
  editing: CustomSchemaDetail | null;
  setEditing: (next: CustomSchemaDetail) => void;
  onSave: () => void;
  saving: boolean;
  onValidate: () => void;
  validateLoading: boolean;
  validationResult: CustomSchemaValidateResponse | null;
}) {
  const [editorMode, setEditorMode] = useState<"form" | "json">("form");
  return (
    <div className="flex-1 space-y-2">
      <Tabs
        tabs={[{ id: "form", label: "Form" }, { id: "json", label: "JSON" }]}
        activeId={editorMode}
        onSelect={(id) => setEditorMode(id as "form" | "json")}
      />
      {validationResult && (
        <div
          role="status"
          aria-live="polite"
          className={
            validationResult.valid
              ? "rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800"
              : "rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          }
        >
          <p className="font-medium">Validation summary</p>
          {validationResult.valid ? (
            <p className="mt-0.5">Schema is valid. You can save and use it for generation.</p>
          ) : (
            <div className="mt-1">
              <p>{validationResult.errors.length} error{validationResult.errors.length !== 1 ? "s" : ""} found. Fix before saving.</p>
              <ul className="list-disc list-inside mt-2 space-y-0.5">
                {validationResult.errors.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      {editorMode === "form" ? (
        <SchemaFormEditor
          schema={editing}
          onChange={setEditing}
          onSave={onSave}
          saving={saving}
          validationErrors={validationResult && !validationResult.valid ? validationResult.errors : []}
          onValidate={onValidate}
          validateLoading={validateLoading}
        />
      ) : (
        <SchemaEditor
          schema={editing}
          onChange={setEditing}
          onSave={onSave}
          saving={saving}
          onValidate={onValidate}
          validateLoading={validateLoading}
        />
      )}
    </div>
  );
}

function SchemaEditor({
  schema,
  onChange,
  onSave,
  saving,
  onValidate,
  validateLoading,
}: {
  schema: CustomSchemaDetail | null;
  onChange: (next: CustomSchemaDetail) => void;
  onSave: () => void;
  saving: boolean;
  onValidate?: () => void;
  validateLoading?: boolean;
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

  if (!schema) {
    return (
      <Card className="flex-1">
        <CardHeader>
          <CardTitle>Schema editor (JSON mode)</CardTitle>
        </CardHeader>
        <CardContent className="py-8">
          <div className="rounded-lg border-2 border-amber-200 bg-amber-50 p-6 text-center">
            <p className="font-medium text-amber-900">Choose or create a schema first</p>
            <p className="text-sm text-amber-800 mt-2">
              Select an existing schema from the list on the left, or click &quot;New schema&quot; to create one.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

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
          <Link href="/create/advanced" className="text-xs text-slate-500 hover:text-slate-700 mr-auto">
            Use with Advanced config →
          </Link>
          {onValidate && (
            <Button size="sm" variant="outline" onClick={onValidate} disabled={validateLoading}>
              {validateLoading ? "Validating…" : "Validate"}
            </Button>
          )}
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
  const [previewData, setPreviewData] = useState<Record<string, Record<string, unknown>[]> | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [validationResult, setValidationResult] = useState<CustomSchemaValidateResponse | null>(null);
  const [validateLoading, setValidateLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [editingLoading, setEditingLoading] = useState(false);
  const [previewTableFilter, setPreviewTableFilter] = useState<string | "all">("all");
  const [previewRowsPerTable, setPreviewRowsPerTable] = useState(5);

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
    if (!selectedId) {
      setEditingLoading(false);
      return;
    }
    setError(null);
    setEditingLoading(true);
    fetchCustomSchema(selectedId)
      .then((detail) => {
        if (!detail) return;
        setEditing(detail);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load schema"))
      .finally(() => setEditingLoading(false));
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

  const handleDuplicate = () => {
    if (!editing) return;
    const dup: CustomSchemaDetail = {
      id: "",
      name: `${editing.name} (copy)`,
      description: editing.description ? `${editing.description} — duplicated` : "Duplicated schema",
      tags: editing.tags ? [...editing.tags] : [],
      version: 1,
      schema: JSON.parse(JSON.stringify(editing.schema)),
    };
    setSelectedId(null);
    setEditing(dup);
  };

  const handleValidate = async () => {
    if (!editing?.schema) return;
    setValidateLoading(true);
    setValidationResult(null);
    setError(null);
    try {
      const result = await validateCustomSchema(editing.schema as Record<string, unknown>);
      setValidationResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed");
    } finally {
      setValidateLoading(false);
    }
  };

  const handlePreview = async () => {
    if (!editing?.schema) return;
    setPreviewLoading(true);
    setPreviewData(null);
    try {
      const data = await fetchSchemaPreview(editing.schema as Record<string, unknown>, previewRowsPerTable);
      setPreviewData(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Preview failed");
    } finally {
      setPreviewLoading(false);
    }
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
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e: unknown) {
      const err = e as { message?: string; detail?: { schema_errors?: string[] } };
      const msg = err?.detail?.schema_errors?.length
        ? `Validation: ${err.detail.schema_errors.join("; ")}`
        : (err?.message || "Failed to save schema");
      setError(msg);
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
          {editing?.id && (
            <Button variant="outline" size="sm" onClick={handleDuplicate}>
              Duplicate schema
            </Button>
          )}
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
      {saveSuccess && (
        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-2 text-sm text-green-700">
          Schema saved successfully.
        </div>
      )}
      <div className="flex flex-col lg:flex-row gap-4 items-stretch">
        <div className="w-full lg:w-80 shrink-0 space-y-3">
          {loading ? (
            <Card>
              <CardHeader>
                <div className="h-5 w-32 rounded bg-slate-200 animate-pulse" />
              </CardHeader>
              <CardContent className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-14 rounded-lg bg-slate-100 animate-pulse" />
                ))}
              </CardContent>
            </Card>
          ) : (
            <SchemaList schemas={schemas} onSelect={setSelectedId} />
          )}
        </div>
        <div className="flex-1 space-y-4">
          {editingLoading && selectedId ? (
            <Card>
              <CardContent className="py-12 space-y-4">
                <div className="h-6 w-48 rounded bg-slate-200 animate-pulse" />
                <div className="h-32 rounded bg-slate-100 animate-pulse" />
                <div className="h-24 rounded bg-slate-100 animate-pulse" />
              </CardContent>
            </Card>
          ) : (
            <>
              <SchemaEditorWithMode
                editing={editing}
                setEditing={setEditing}
                onSave={handleSave}
                saving={saving}
                onValidate={handleValidate}
                validateLoading={validateLoading}
                validationResult={validationResult}
              />
              {editing?.id && (
                <VersionHistoryCard schemaId={editing.id} />
              )}
            </>
          )}
          {editing && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Sample preview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap items-center gap-3">
                  <label className="flex items-center gap-2 text-sm text-slate-600">
                    Rows per table:
                    <input
                      type="number"
                      min={1}
                      max={20}
                      value={previewRowsPerTable}
                      onChange={(e) => setPreviewRowsPerTable(Math.min(20, Math.max(1, Number(e.target.value) || 5)))}
                      className="w-16 rounded border border-slate-300 px-2 py-1 text-sm"
                    />
                  </label>
                  <Button size="sm" variant="outline" onClick={handlePreview} disabled={previewLoading}>
                    {previewLoading ? "Generating…" : previewData ? "Regenerate preview" : "Generate sample rows"}
                  </Button>
                  {previewData && Object.keys(previewData).length > 1 && (
                    <select
                      value={previewTableFilter}
                      onChange={(e) => setPreviewTableFilter(e.target.value)}
                      className="rounded border border-slate-300 px-2 py-1 text-sm"
                    >
                      <option value="all">All tables</option>
                      {Object.keys(previewData).map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  )}
                </div>
                {!previewData && !previewLoading && editing?.schema && (
                  <p className="text-sm text-slate-500">Preview is in-memory only; not persisted. Click &quot;Generate sample rows&quot; to see sample data.</p>
                )}
                {previewData && Object.keys(previewData).length === 0 && (
                  <p className="text-sm text-slate-500">No tables to preview. Add tables to the schema first.</p>
                )}
                {previewData && Object.keys(previewData).length > 0 && (
                  <div className="mt-4 space-y-4">
                    {(previewTableFilter === "all"
                      ? Object.entries(previewData)
                      : Object.entries(previewData).filter(([t]) => t === previewTableFilter)
                    ).map(([tableName, rows]) => (
                      <div key={tableName}>
                        <p className="text-sm font-medium text-slate-700 mb-2">
                          {tableName} <span className="text-slate-500 font-normal">({rows.length} row{rows.length !== 1 ? "s" : ""})</span>
                        </p>
                        <div className="overflow-x-auto rounded border border-slate-200">
                          <table className="min-w-full text-xs">
                            <thead>
                              <tr className="bg-slate-50">
                                {rows[0] && Object.keys(rows[0]).map((col) => (
                                  <th key={col} className="px-3 py-2 text-left font-medium text-slate-700">{col}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {rows.map((row, i) => (
                                <tr key={i} className="border-t border-slate-100">
                                  {Object.values(row).map((v, j) => (
                                    <td key={j} className="px-3 py-2 text-slate-600">
                                      {String(v ?? "null")}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

