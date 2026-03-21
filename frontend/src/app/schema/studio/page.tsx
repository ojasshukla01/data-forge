"use client";

import { useCallback, useEffect, useRef, useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Tabs } from "@/components/ui/Tabs";
import {
  fetchCustomSchemas,
  fetchCustomSchema,
  createCustomSchema,
  updateCustomSchema,
  deleteCustomSchema,
  fetchSchemaPreview,
  fetchSchemaToSql,
  validateCustomSchema,
  fetchCustomSchemaVersions,
  fetchCustomSchemaDiff,
  restoreSchemaVersion,
  type CustomSchemaSummary,
  type CustomSchemaDetail,
  type CustomSchemaValidateResponse,
  type CustomSchemaVersionsResponse,
  type CustomSchemaDiffResponse,
} from "@/lib/api";
import { SchemaFormEditor } from "./components/SchemaFormEditor";
import { SchemaCanvasEditor } from "./components/SchemaCanvasEditor";
import { cn } from "@/lib/utils";

function VersionHistoryCard({
  schemaId,
  onRestore,
}: {
  schemaId: string;
  onRestore?: (detail: CustomSchemaDetail) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [versionsData, setVersionsData] = useState<CustomSchemaVersionsResponse | null>(null);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [leftVer, setLeftVer] = useState<number>(1);
  const [rightVer, setRightVer] = useState<number>(1);
  const [diffData, setDiffData] = useState<CustomSchemaDiffResponse | null>(null);
  const [diffLoading, setDiffLoading] = useState(false);
  const [restoringVer, setRestoringVer] = useState<number | null>(null);

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

  const handleRestore = async (version: number) => {
    if (!onRestore) return;
    setRestoringVer(version);
    try {
      const detail = await restoreSchemaVersion(schemaId, version);
      onRestore(detail);
      setExpanded(false);
    } finally {
      setRestoringVer(null);
    }
  };

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
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <span className="text-sm text-slate-600">Restore version as new:</span>
                {versions.map((v) => (
                  <button
                    key={v.version}
                    type="button"
                    onClick={() => handleRestore(v.version)}
                    disabled={restoringVer !== null || v.version === currentVersion}
                    className="text-xs px-2 py-1 rounded border border-slate-300 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    v{v.version}{v.version === currentVersion ? " (current)" : ""}
                    {restoringVer === v.version ? " …" : ""}
                  </button>
                ))}
              </div>
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

const HOW_IT_WORKS_LINK = { href: "/docs#schema-studio", label: "How it works (detailed guide)" };

function SchemaList({
  schemas,
  selectedId,
  onSelect,
  onDelete,
}: {
  schemas: CustomSchemaSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
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
                <div
                  key={s.id}
                  className={cn(
                    "flex items-center gap-2 rounded-lg border transition-colors",
                    selectedId === s.id ? "border-[var(--brand-teal)] bg-teal-50/50" : "border-slate-200 hover:border-[var(--brand-teal)]/50 hover:bg-slate-50"
                  )}
                >
                  <button
                    type="button"
                    onClick={() => onSelect(s.id)}
                    className="flex-1 min-w-0 text-left px-3 py-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-slate-900 truncate">{s.name}</span>
                      <span className="text-xs text-slate-500 font-mono shrink-0">v{s.version}</span>
                    </div>
                    {s.description && (
                      <p className="text-xs text-slate-600 mt-0.5 line-clamp-2">{s.description}</p>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); onDelete(s.id); }}
                    title="Delete schema"
                    className="shrink-0 p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-r-lg transition-colors"
                    aria-label={`Delete ${s.name}`}
                  >
                    <span aria-hidden>🗑</span>
                  </button>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">How it works</CardTitle>
        </CardHeader>
        <CardContent>
          <Link href={HOW_IT_WORKS_LINK.href} className="text-sm text-[var(--brand-teal)] hover:underline">
            → {HOW_IT_WORKS_LINK.label}
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}

function SchemaSqlView({
  schema,
  onValidate,
  validateLoading,
  active,
}: {
  schema: CustomSchemaDetail | null;
  onValidate?: () => void;
  validateLoading?: boolean;
  active?: boolean;
}) {
  const [sql, setSql] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!active || !schema?.schema) {
      if (!active) return;
      setSql("");
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetchSchemaToSql(schema.schema as Record<string, unknown>)
      .then((r) => setSql(r.sql))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to generate SQL"))
      .finally(() => setLoading(false));
  }, [active, schema?.id, schema?.schema]);

  if (!schema) {
    return (
      <Card className="flex-1">
        <CardContent className="py-12 text-center text-slate-500">Choose or create a schema first.</CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex-1">
      <CardHeader className="flex flex-row justify-between items-center">
        <CardTitle className="text-base">SQL DDL</CardTitle>
        {onValidate && (
          <Button size="sm" variant="outline" onClick={onValidate} disabled={validateLoading}>
            {validateLoading ? "Validating…" : "Validate schema"}
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <p className="text-xs text-slate-600 mb-2">Generated from your schema. Copy to use in your database.</p>
        {loading && <p className="text-sm text-slate-500">Generating SQL…</p>}
        {error && <p className="text-sm text-red-600">{error}</p>}
        {!loading && !error && (
          <div className="space-y-2">
            <div className="flex justify-end">
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigator.clipboard.writeText(sql)}
              >
                Copy SQL
              </Button>
            </div>
            <textarea
              readOnly
              value={sql}
              rows={20}
              className="w-full rounded border border-slate-300 px-3 py-2 text-xs font-mono bg-slate-50 resize-y"
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SchemaEditorWithMode({
  editing,
  setEditing,
  onSave,
  saving,
  saveDisabled,
  onValidate,
  validateLoading,
  validationResult,
}: {
  editing: CustomSchemaDetail | null;
  setEditing: (next: CustomSchemaDetail) => void;
  onSave: (schemaOverride?: CustomSchemaDetail) => void;
  saving: boolean;
  saveDisabled?: boolean;
  onValidate: () => void;
  validateLoading: boolean;
  validationResult: CustomSchemaValidateResponse | null;
}) {
  const [editorMode, setEditorMode] = useState<"form" | "json" | "visual" | "sql">("visual");
  return (
    <div className="flex-1 space-y-2">
      <Tabs
        tabs={[
          { id: "visual", label: "Visual" },
          { id: "form", label: "Form" },
          { id: "json", label: "JSON" },
          { id: "sql", label: "SQL" },
        ]}
        activeId={editorMode}
        onSelect={(id) => setEditorMode(id as "form" | "json" | "visual" | "sql")}
      />
      {validationResult && (
        <div
          role="status"
          aria-live="polite"
          className={
            validationResult.valid
              ? "rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800"
              : "rounded-lg border-2 border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          }
        >
          <p className="font-semibold">{validationResult.valid ? "✓ Schema valid" : "✗ Validation failed"}</p>
          {validationResult.valid ? (
            <p className="mt-0.5">You can save and use this schema for generation.</p>
          ) : (
            <div className="mt-2 space-y-2">
              <p className="font-medium">Fix these {(validationResult.errors?.length ?? 0)} error{(validationResult.errors?.length ?? 0) !== 1 ? "s" : ""} before saving:</p>
              <ul className="space-y-1.5 list-none pl-0">
                {(validationResult.errors ?? []).map((e, i) => {
                  const parts = e.split(" → ");
                  const msg = parts[0];
                  const rec = parts[1];
                  return (
                    <li key={i} className="flex flex-col gap-0.5 py-1.5 px-2 rounded bg-red-100/50 border-l-2 border-red-400">
                      <span>{msg}</span>
                      {rec && <span className="text-red-700 font-medium text-xs">→ {rec}</span>}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
          {(validationResult.warnings?.length ?? 0) > 0 && (
            <div className="mt-3 pt-3 border-t border-amber-200">
              <p className="font-medium text-amber-800">{validationResult.warnings!.length} warning{validationResult.warnings!.length !== 1 ? "s" : ""} (optional to fix)</p>
              <ul className="list-disc list-inside mt-1 space-y-0.5 text-amber-700">
                {validationResult.warnings!.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      {editorMode === "visual" ? (
        <SchemaCanvasEditor
          schema={editing}
          onChange={setEditing}
          onSave={onSave}
          saving={saving}
          saveDisabled={saveDisabled}
          onValidate={onValidate}
          validateLoading={validateLoading}
        />
      ) : editorMode === "form" ? (
        <SchemaFormEditor
          schema={editing}
          onChange={setEditing}
          onSave={onSave}
          saving={saving}
          saveDisabled={saveDisabled}
          validationErrors={validationResult && !validationResult.valid ? validationResult.errors : []}
          onValidate={onValidate}
          validateLoading={validateLoading}
        />
      ) : editorMode === "sql" ? (
        <SchemaSqlView schema={editing} onValidate={onValidate} validateLoading={validateLoading} active={editorMode === "sql"} />
      ) : (
        <SchemaEditor
          schema={editing}
          onChange={setEditing}
          onSave={onSave}
          saving={saving}
          saveDisabled={saveDisabled}
          onValidate={onValidate}
          validateLoading={validateLoading}
          editorMode={editorMode}
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
  saveDisabled,
  onValidate,
  validateLoading,
  editorMode,
}: {
  schema: CustomSchemaDetail | null;
  onChange: (next: CustomSchemaDetail) => void;
  onSave: (schemaOverride?: CustomSchemaDetail) => void;
  saving: boolean;
  saveDisabled?: boolean;
  onValidate?: () => void;
  validateLoading?: boolean;
  editorMode?: "form" | "json" | "visual" | "sql";
}) {
  const [jsonText, setJsonText] = useState<string>(() =>
    schema ? JSON.stringify(schema.schema, null, 2) : "{\n  \"name\": \"example\",\n  \"tables\": [],\n  \"relationships\": []\n}",
  );
  const [jsonError, setJsonError] = useState<string | null>(null);

  useEffect(() => {
    if (schema && editorMode === "json") {
      setJsonText(JSON.stringify(schema.schema, null, 2));
      setJsonError(null);
    }
  }, [schema?.id, editorMode, schema?.schema]);

  const safeParse = (): CustomSchemaDetail | null => {
    try {
      const parsed = JSON.parse(jsonText) as Record<string, unknown>;
      if (!schema) return null;
      const merged = { ...schema, schema: parsed };
      onChange(merged);
      setJsonError(null);
      return merged;
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : "Invalid JSON");
      return null;
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
              const merged = safeParse();
              if (merged) onSave(merged);
            }}
            disabled={saving || saveDisabled}
          >
            {saving ? "Saving…" : "Save schema"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function SchemaStudioContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [schemas, setSchemas] = useState<CustomSchemaSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editing, setEditing] = useState<CustomSchemaDetail | null>(null);
  const editingRef = useRef<CustomSchemaDetail | null>(null);
  useEffect(() => {
    editingRef.current = editing;
  }, [editing]);
  const [saving, setSaving] = useState(false);
  const [previewData, setPreviewData] = useState<Record<string, Record<string, unknown>[]> | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [validationResult, setValidationResult] = useState<CustomSchemaValidateResponse | null>(null);
  const [validateLoading, setValidateLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [editingLoading, setEditingLoading] = useState(false);
  const [previewTableFilter, setPreviewTableFilter] = useState<string | "all">("all");
  const [previewRowsPerTable, setPreviewRowsPerTable] = useState(5);

  const loadSchemas = useCallback(() => {
    setLoading(true);
    setError(null);
    fetchCustomSchemas()
      .then(setSchemas)
      .catch((e) => {
        console.error(e);
        setSchemas([]);
        setError(e instanceof Error ? e.message : "Failed to load custom schemas");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadSchemas();
  }, [loadSchemas]);

  const schemaParam = searchParams.get("schema");
  useEffect(() => {
    if (schemaParam && schemas.some((s) => s.id === schemaParam)) {
      setSelectedId(schemaParam);
    }
  }, [schemaParam, schemas]);

  useEffect(() => {
    if (!selectedId) {
      setEditingLoading(false);
      return;
    }
    setError(null);
    setEditingLoading(true);
    setValidationResult(null);
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
    setValidationResult(null);
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
    setValidationResult(null);
  };

  const handleSetEditing = useCallback((next: CustomSchemaDetail) => {
    setEditing(next);
    setValidationResult(null);
  }, []);

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

  const handleSave = async (schemaOverride?: CustomSchemaDetail) => {
    const toSave = schemaOverride ?? editingRef.current ?? editing;
    if (!toSave) return;
    const raw = toSave.schema as Record<string, unknown> | undefined;
    const schemaBody =
      raw && typeof raw === "object"
        ? raw
        : { name: "schema", tables: [] as unknown[], relationships: [] as unknown[] };
    setError(null);
    setValidationResult(null);
    setValidateLoading(true);
    try {
      const result = await validateCustomSchema(schemaBody);
      setValidationResult(result);
      if (!result.valid) {
        return;
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed");
      return;
    } finally {
      setValidateLoading(false);
    }
    setSaving(true);
    try {
      if (!toSave.id) {
        const created = await createCustomSchema({
          name: toSave.name,
          description: toSave.description,
          tags: toSave.tags,
          schema: schemaBody,
        });
        setSchemas((prev) => [created, ...prev]);
        setSelectedId(created.id);
        setEditing(created);
      } else {
        const updated = await updateCustomSchema(toSave.id, {
          name: toSave.name,
          description: toSave.description,
          tags: toSave.tags,
          schema: schemaBody,
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

  const handleDelete = async (schemaId: string) => {
    if (!window.confirm(`Delete schema "${schemas.find((s) => s.id === schemaId)?.name ?? schemaId}"? This cannot be undone.`)) return;
    try {
      await deleteCustomSchema(schemaId);
      setSchemas((prev) => prev.filter((s) => s.id !== schemaId));
      if (selectedId === schemaId) {
        setSelectedId(null);
        setEditing(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete schema");
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
            <>
              <Button variant="outline" size="sm" onClick={handleDuplicate}>
                Duplicate
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDelete(editing.id)}
                className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
              >
                Delete
              </Button>
            </>
          )}
          <Button size="sm" onClick={handleCreateNew}>
            New schema
          </Button>
        </div>
      </div>
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          <div className="flex items-center justify-between gap-3">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={loadSchemas}>
              Retry
            </Button>
          </div>
        </div>
      )}
      {saveSuccess && (
        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-2 text-sm text-green-700">
          <div className="flex items-center justify-between gap-3">
            <span>Schema saved successfully.</span>
            {editing?.id && (
              <Link href="/create/wizard" className="text-[var(--brand-teal)] hover:underline">
                Use in Create Wizard
              </Link>
            )}
          </div>
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
            <SchemaList schemas={schemas} selectedId={selectedId} onSelect={setSelectedId} onDelete={handleDelete} />
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
                setEditing={handleSetEditing}
                onSave={handleSave}
                saving={saving}
                saveDisabled={validationResult != null && !validationResult.valid}
                onValidate={handleValidate}
                validateLoading={validateLoading}
                validationResult={validationResult}
              />
              {editing?.id && (
                <VersionHistoryCard
                  schemaId={editing.id}
                  onRestore={(detail) => {
                    setEditing(detail);
                    setSchemas((prev) =>
                      prev.map((s) =>
                        s.id === detail.id
                          ? { ...s, version: detail.version }
                          : s
                      )
                    );
                  }}
                />
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

export default function SchemaStudioPage() {
  return (
    <Suspense fallback={<div className="p-8 text-slate-500">Loading…</div>}>
      <SchemaStudioContent />
    </Suspense>
  );
}
