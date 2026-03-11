"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Tabs } from "@/components/ui/Tabs";
import type { CustomSchemaDetail } from "@/lib/api";

function parseValidationHighlights(errors: string[]): {
  tableErrors: Set<string>;
  columnErrors: Map<string, Set<string>>;
} {
  const tableErrors = new Set<string>();
  const columnErrors = new Map<string, Set<string>>();
  for (const e of errors) {
    const tableMatch = e.match(/Table ['"]([^'"]+)['"]/);
    if (tableMatch) {
      const t = tableMatch[1];
      tableErrors.add(t);
      const colMatch = e.match(/column ['"]([^'"]+)['"]/);
      if (colMatch) {
        const c = colMatch[1];
        if (!columnErrors.has(t)) columnErrors.set(t, new Set());
        columnErrors.get(t)!.add(c);
      }
    }
  }
  return { tableErrors, columnErrors };
}

const DATA_TYPES = [
  "string",
  "text",
  "integer",
  "bigint",
  "float",
  "decimal",
  "boolean",
  "date",
  "datetime",
  "timestamp",
  "uuid",
  "email",
  "phone",
  "url",
  "json",
  "enum",
  "currency",
  "percent",
];

const RULE_TYPES = ["faker", "uuid", "sequence", "range", "static", "weighted_choice"] as const;
const FAKER_PROVIDERS = ["name", "email", "phone", "company", "address", "city", "country", "url", "uuid"];

interface ColGenerationRule {
  rule_type: string;
  params: Record<string, unknown>;
}

interface TableColumn {
  name: string;
  data_type: string;
  nullable?: boolean;
  primary_key?: boolean;
  description?: string;
  display_name?: string;
  generation_rule?: ColGenerationRule;
}

interface TableDef {
  name: string;
  columns: TableColumn[];
  primary_key: string[];
  description?: string;
  tags?: string[];
}

interface RelationshipDef {
  name: string;
  from_table: string;
  from_columns: string[];
  to_table: string;
  to_columns: string[];
  cardinality?: string;
}

function ColumnRuleEditor({
  rule,
  onChange,
  onClear,
}: {
  rule: ColGenerationRule;
  onChange: (next: ColGenerationRule) => void;
  onClear: () => void;
}) {
  const rt = rule.rule_type || "faker";
  const params = rule.params || {};
  return (
    <div className="mt-2 pl-4 border-l-2 border-slate-200 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-slate-600">Generation rule</span>
        <select
          value={rt}
          onChange={(e) => onChange({ rule_type: e.target.value, params: rt === e.target.value ? params : {} })}
          className="rounded border border-slate-300 px-2 py-0.5 text-xs"
        >
          {RULE_TYPES.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
        <button type="button" onClick={onClear} className="text-xs text-red-600 hover:underline">Remove</button>
      </div>
      {rt === "faker" && (
        <div>
          <label className="text-xs text-slate-500">Provider</label>
          <select
            value={(params.provider as string) || "name"}
            onChange={(e) => onChange({ ...rule, params: { ...params, provider: e.target.value } })}
            className="block w-full mt-0.5 rounded border border-slate-300 px-2 py-0.5 text-xs"
          >
            {FAKER_PROVIDERS.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
      )}
      {rt === "static" && (
        <div>
          <label className="text-xs text-slate-500">Value</label>
          <input
            type="text"
            value={(params.value as string) ?? ""}
            onChange={(e) => onChange({ ...rule, params: { ...params, value: e.target.value } })}
            className="block w-full mt-0.5 rounded border border-slate-300 px-2 py-0.5 text-xs"
            placeholder="e.g. pending"
          />
        </div>
      )}
      {rt === "sequence" && (
        <div className="flex gap-3">
          <div>
            <label className="text-xs text-slate-500">Start</label>
            <input
              type="number"
              value={(params.start as number) ?? 1}
              onChange={(e) => onChange({ ...rule, params: { ...params, start: parseInt(e.target.value, 10) || 1 } })}
              className="block w-20 mt-0.5 rounded border border-slate-300 px-2 py-0.5 text-xs"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500">Step</label>
            <input
              type="number"
              value={(params.step as number) ?? 1}
              onChange={(e) => onChange({ ...rule, params: { ...params, step: parseInt(e.target.value, 10) || 1 } })}
              className="block w-20 mt-0.5 rounded border border-slate-300 px-2 py-0.5 text-xs"
            />
          </div>
        </div>
      )}
      {rt === "range" && (
        <div className="flex gap-3">
          <div>
            <label className="text-xs text-slate-500">Min</label>
            <input
              type="number"
              value={(params.min as number) ?? 0}
              onChange={(e) => onChange({ ...rule, params: { ...params, min: parseFloat(e.target.value) || 0 } })}
              className="block w-20 mt-0.5 rounded border border-slate-300 px-2 py-0.5 text-xs"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500">Max</label>
            <input
              type="number"
              value={(params.max as number) ?? 100}
              onChange={(e) => onChange({ ...rule, params: { ...params, max: parseFloat(e.target.value) || 100 } })}
              className="block w-20 mt-0.5 rounded border border-slate-300 px-2 py-0.5 text-xs"
            />
          </div>
        </div>
      )}
      {rt === "weighted_choice" && (
        <div className="space-y-2">
          <div>
            <label className="text-xs text-slate-500">Choices (comma-separated)</label>
            <input
              type="text"
              value={Array.isArray(params.choices) ? (params.choices as string[]).join(", ") : String(params.choices ?? "")}
              onChange={(e) => {
                const choices = e.target.value.split(",").map((s) => s.trim()).filter(Boolean);
                onChange({ ...rule, params: { ...params, choices } });
              }}
              className="block w-full mt-0.5 rounded border border-slate-300 px-2 py-0.5 text-xs"
              placeholder="e.g. active, inactive, pending"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500">Weights (optional, comma-separated)</label>
            <input
              type="text"
              value={Array.isArray(params.weights) ? (params.weights as number[]).join(", ") : String(params.weights ?? "")}
              onChange={(e) => {
                const weights = e.target.value.split(",").map((s) => parseFloat(s.trim())).filter((n) => !Number.isNaN(n));
                onChange({ ...rule, params: { ...params, weights: weights.length ? weights : undefined } });
              }}
              className="block w-full mt-0.5 rounded border border-slate-300 px-2 py-0.5 text-xs"
              placeholder="e.g. 0.5, 0.3, 0.2"
            />
          </div>
        </div>
      )}
    </div>
  );
}

function toSchemaDef(detail: CustomSchemaDetail | null): { tables: TableDef[]; relationships: RelationshipDef[] } {
  const s = detail?.schema;
  const tables = (s?.tables ?? []) as TableDef[];
  const relationships = (s?.relationships ?? []) as RelationshipDef[];
  return { tables, relationships };
}

export function SchemaFormEditor({
  schema,
  onChange,
  onSave,
  saving,
  validationErrors = [],
  onValidate,
  validateLoading = false,
}: {
  schema: CustomSchemaDetail | null;
  onChange: (next: CustomSchemaDetail) => void;
  onSave: () => void;
  saving: boolean;
  validationErrors?: string[];
  onValidate?: () => void;
  validateLoading?: boolean;
}) {
  const [activePanel, setActivePanel] = useState<"tables" | "columns" | "relationships">("tables");
  const [selectedTableIndex, setSelectedTableIndex] = useState<number>(0);
  const { tables, relationships } = toSchemaDef(schema);

  const updateSchema = (tablesNext: TableDef[], relationshipsNext: RelationshipDef[]) => {
    if (!schema) return;
    onChange({
      ...schema,
      schema: {
        ...schema.schema,
        name: (schema.schema as { name?: string })?.name ?? "schema",
        tables: tablesNext,
        relationships: relationshipsNext,
      },
    });
  };

  const addTable = () => {
    const name = `table_${tables.length + 1}`;
    const tablesNext = [...tables, { name, columns: [], primary_key: [] }];
    updateSchema(tablesNext, relationships);
    setSelectedTableIndex(tablesNext.length - 1);
    setActivePanel("columns");
  };

  const removeTable = (idx: number) => {
    const t = tables[idx];
    const tablesNext = tables.filter((_, i) => i !== idx);
    const relationshipsNext = relationships.filter((r) => r.from_table !== t.name && r.to_table !== t.name);
    updateSchema(tablesNext, relationshipsNext);
    setSelectedTableIndex(Math.max(0, idx - 1));
  };

  const updateTable = (idx: number, updates: Partial<TableDef>) => {
    const tablesNext = [...tables];
    tablesNext[idx] = { ...tablesNext[idx], ...updates };
    updateSchema(tablesNext, relationships);
  };

  const addColumn = (tableIdx: number) => {
    const t = tables[tableIdx];
    const colName = `col_${(t.columns?.length ?? 0) + 1}`;
    const columns: TableColumn[] = [...(t.columns ?? []), { name: colName, data_type: "string", nullable: true }];
    updateTable(tableIdx, { columns });
  };

  const setColumnRule = (tableIdx: number, colIdx: number, rule: ColGenerationRule | undefined) => {
    updateColumn(tableIdx, colIdx, { generation_rule: rule });
  };

  const removeColumn = (tableIdx: number, colIdx: number) => {
    const t = tables[tableIdx];
    const col = t.columns[colIdx];
    const columns = t.columns.filter((_, i) => i !== colIdx);
    const primary_key = (t.primary_key ?? []).filter((pk) => pk !== col.name);
    updateTable(tableIdx, { columns, primary_key });
  };

  const updateColumn = (tableIdx: number, colIdx: number, updates: Record<string, unknown>) => {
    const t = tables[tableIdx];
    const columns = [...(t.columns ?? [])];
    columns[colIdx] = { ...columns[colIdx], ...updates };
    updateTable(tableIdx, { columns });
  };

  const togglePrimaryKey = (tableIdx: number, colName: string) => {
    const t = tables[tableIdx];
    const pk = t.primary_key ?? [];
    const next = pk.includes(colName) ? pk.filter((p) => p !== colName) : [...pk, colName];
    updateTable(tableIdx, { primary_key: next });
  };

  const addRelationship = () => {
    const from = tables[0]?.name ?? "table_1";
    const to = tables[1]?.name ?? tables[0]?.name ?? "table_2";
    const relationshipsNext = [
      ...relationships,
      {
        name: `rel_${relationships.length + 1}`,
        from_table: from,
        from_columns: ["id"],
        to_table: to,
        to_columns: ["id"],
        cardinality: "many-to-one",
      },
    ];
    updateSchema(tables, relationshipsNext);
  };

  const removeRelationship = (idx: number) => {
    const relationshipsNext = relationships.filter((_, i) => i !== idx);
    updateSchema(tables, relationshipsNext);
  };

  const updateRelationship = (idx: number, updates: Partial<RelationshipDef>) => {
    const relationshipsNext = [...relationships];
    relationshipsNext[idx] = { ...relationshipsNext[idx], ...updates };
    updateSchema(tables, relationshipsNext);
  };

  const selectedTable = tables[selectedTableIndex];
  const { tableErrors, columnErrors } = parseValidationHighlights(validationErrors);

  return (
    <Card className="flex-1">
      <CardHeader>
        <CardTitle>Schema editor (form mode)</CardTitle>
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
                    tags: e.target.value.split(",").map((t) => t.trim()).filter(Boolean),
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
        <Tabs
          tabs={[
            { id: "tables", label: "Tables" },
            { id: "columns", label: "Columns" },
            { id: "relationships", label: "Relationships" },
          ]}
          activeId={activePanel}
          onSelect={(id) => setActivePanel(id as "tables" | "columns" | "relationships")}
        />

        {activePanel === "tables" && (
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-slate-600">Define tables for your schema</span>
              <Button size="sm" variant="outline" onClick={addTable}>
                Add table
              </Button>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {tables.map((t, i) => (
                <div
                  key={i}
                  className={`flex flex-col gap-2 p-3 rounded-lg border ${
                    tableErrors.has(t.name)
                      ? "border-red-400 bg-red-50/50"
                      : selectedTableIndex === i
                        ? "border-[var(--brand-teal)] bg-slate-50"
                        : "border-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedTableIndex(i)}
                      className="flex-1 text-left text-sm font-medium"
                    >
                      {t.name}
                    </button>
                    <input
                      type="text"
                      value={t.name}
                      onChange={(e) => updateTable(i, { name: e.target.value })}
                      className="flex-1 rounded border border-slate-300 px-2 py-1 text-sm"
                      placeholder="Table name"
                    />
                    <Button size="sm" variant="outline" onClick={() => removeTable(i)} className="text-red-600 shrink-0">
                      Remove
                    </Button>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={t.description ?? ""}
                      onChange={(e) => updateTable(i, { description: e.target.value || undefined })}
                      className="flex-1 rounded border border-slate-300 px-2 py-1 text-xs"
                      placeholder="Description (optional)"
                    />
                    <input
                      type="text"
                      value={(t.tags ?? []).join(", ")}
                      onChange={(e) =>
                        updateTable(i, {
                          tags: e.target.value
                            .split(",")
                            .map((x) => x.trim())
                            .filter(Boolean),
                        })
                      }
                      className="flex-1 rounded border border-slate-300 px-2 py-1 text-xs"
                      placeholder="Tags (comma-separated)"
                    />
                  </div>
                </div>
              ))}
              {tables.length === 0 && (
                <p className="text-sm text-slate-500 py-4">No tables yet. Click &quot;Add table&quot; to start.</p>
              )}
            </div>
          </div>
        )}

        {activePanel === "columns" && (
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <select
                value={selectedTableIndex}
                onChange={(e) => setSelectedTableIndex(Number(e.target.value))}
                className="rounded border border-slate-300 px-3 py-2 text-sm"
              >
                {tables.map((t, i) => (
                  <option key={i} value={i}>
                    {t.name}
                  </option>
                ))}
              </select>
              {selectedTable && (
                <Button size="sm" variant="outline" onClick={() => addColumn(selectedTableIndex)}>
                  Add column
                </Button>
              )}
            </div>
            {selectedTable && (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {selectedTable.columns.map((col, j) => (
                  <div
                    key={j}
                    className={`p-3 rounded border ${
                      columnErrors.get(selectedTable.name)?.has(col.name) ? "border-red-400 bg-red-50/50" : "border-slate-200"
                    }`}
                  >
                    <div className="grid grid-cols-12 gap-2 items-center">
                      <input
                        type="text"
                        value={col.name}
                        onChange={(e) => updateColumn(selectedTableIndex, j, { name: e.target.value })}
                        className="col-span-3 rounded border border-slate-300 px-2 py-1 text-sm"
                        placeholder="Column name"
                      />
                      <input
                        type="text"
                        value={col.display_name ?? ""}
                        onChange={(e) => updateColumn(selectedTableIndex, j, { display_name: e.target.value || undefined })}
                        className="col-span-2 rounded border border-slate-300 px-2 py-1 text-sm"
                        placeholder="Display name"
                      />
                      <select
                        value={col.data_type ?? "string"}
                        onChange={(e) => updateColumn(selectedTableIndex, j, { data_type: e.target.value })}
                        className="col-span-2 rounded border border-slate-300 px-2 py-1 text-sm"
                      >
                        {DATA_TYPES.map((dt) => (
                          <option key={dt} value={dt}>{dt}</option>
                        ))}
                      </select>
                      <label className="col-span-2 flex items-center gap-1 text-xs">
                        <input
                          type="checkbox"
                          checked={col.nullable ?? true}
                          onChange={(e) => updateColumn(selectedTableIndex, j, { nullable: e.target.checked })}
                        />
                        nullable
                      </label>
                      <label className="col-span-2 flex items-center gap-1 text-xs">
                        <input
                          type="checkbox"
                          checked={(selectedTable.primary_key ?? []).includes(col.name)}
                          onChange={() => togglePrimaryKey(selectedTableIndex, col.name)}
                        />
                        PK
                      </label>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => removeColumn(selectedTableIndex, j)}
                        className="col-span-1 text-red-600"
                      >
                        ×
                      </Button>
                    </div>
                    {col.generation_rule ? (
                      <ColumnRuleEditor
                        rule={col.generation_rule}
                        onChange={(r) => setColumnRule(selectedTableIndex, j, r)}
                        onClear={() => setColumnRule(selectedTableIndex, j, undefined)}
                      />
                    ) : (
                      <div className="mt-2">
                        <button
                          type="button"
                          onClick={() => setColumnRule(selectedTableIndex, j, { rule_type: "faker", params: { provider: "name" } })}
                          className="text-xs text-slate-500 hover:text-[var(--brand-teal)]"
                        >
                          + Add generation rule
                        </button>
                      </div>
                    )}
                  </div>
                ))}
                {selectedTable.columns.length === 0 && (
                  <p className="text-sm text-slate-500 py-4">No columns yet. Click &quot;Add column&quot;.</p>
                )}
              </div>
            )}
            {tables.length === 0 && (
              <p className="text-sm text-slate-500 py-4">Add a table first from the Tables panel.</p>
            )}
          </div>
        )}

        {activePanel === "relationships" && (
          <div className="space-y-3">
            <div className="flex justify-end">
              <Button size="sm" variant="outline" onClick={addRelationship}>
                Add relationship
              </Button>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {relationships.map((r, i) => (
                <div key={i} className="p-3 rounded border border-slate-200 grid grid-cols-12 gap-2">
                  <input
                    type="text"
                    value={r.name}
                    onChange={(e) => updateRelationship(i, { name: e.target.value })}
                    className="col-span-2 rounded border border-slate-300 px-2 py-1 text-sm"
                    placeholder="Name"
                  />
                  <select
                    value={r.from_table}
                    onChange={(e) => updateRelationship(i, { from_table: e.target.value })}
                    className="col-span-2 rounded border border-slate-300 px-2 py-1 text-sm"
                  >
                    {tables.map((t) => (
                      <option key={t.name} value={t.name}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={(r.from_columns ?? []).join(", ")}
                    onChange={(e) =>
                      updateRelationship(i, { from_columns: e.target.value.split(",").map((c) => c.trim()) })
                    }
                    className="col-span-2 rounded border border-slate-300 px-2 py-1 text-sm"
                    placeholder="from_cols"
                  />
                  <span className="col-span-1 text-center text-slate-400">→</span>
                  <select
                    value={r.to_table}
                    onChange={(e) => updateRelationship(i, { to_table: e.target.value })}
                    className="col-span-2 rounded border border-slate-300 px-2 py-1 text-sm"
                  >
                    {tables.map((t) => (
                      <option key={t.name} value={t.name}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={(r.to_columns ?? []).join(", ")}
                    onChange={(e) =>
                      updateRelationship(i, { to_columns: e.target.value.split(",").map((c) => c.trim()) })
                    }
                    className="col-span-2 rounded border border-slate-300 px-2 py-1 text-sm"
                    placeholder="to_cols"
                  />
                  <Button size="sm" variant="outline" onClick={() => removeRelationship(i)} className="col-span-1 text-red-600">
                    ×
                  </Button>
                </div>
              ))}
              {relationships.length === 0 && (
                <p className="text-sm text-slate-500 py-4">No relationships yet. Click &quot;Add relationship&quot;.</p>
              )}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2 border-t border-slate-200">
          {onValidate && (
            <Button size="sm" variant="outline" onClick={onValidate} disabled={validateLoading}>
              {validateLoading ? "Validating…" : "Validate"}
            </Button>
          )}
          <Button size="sm" onClick={onSave} disabled={saving}>
            {saving ? "Saving…" : "Save schema"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
