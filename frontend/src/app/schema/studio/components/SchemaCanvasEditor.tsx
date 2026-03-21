"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  BackgroundVariant,
  MarkerType,
  Handle,
  Position,
  Panel,
} from "reactflow";
import "reactflow/dist/style.css";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import type { CustomSchemaDetail } from "@/lib/api";

const DATA_TYPES = ["string", "integer", "bigint", "float", "boolean", "date", "datetime", "uuid", "email", "text", "json"];

interface TableColumn {
  name: string;
  data_type: string;
  nullable?: boolean;
  primary_key?: boolean;
}

interface TableDef {
  name: string;
  columns: TableColumn[];
  primary_key: string[];
}

interface RelationshipDef {
  name: string;
  from_table: string;
  from_columns: string[];
  to_table: string;
  to_columns: string[];
}

function toSchemaDef(detail: CustomSchemaDetail | null) {
  const s = detail?.schema;
  const tables = (s?.tables ?? []) as TableDef[];
  const relationships = (s?.relationships ?? []) as RelationshipDef[];
  return { tables, relationships };
}

interface TableNodeData {
  label: string;
  columns: TableColumn[];
  primaryKey: string[];
  tableIndex: number;
}

function EditableTableNode({ data, selected }: { data: TableNodeData; selected?: boolean }) {
  const cols = data.columns ?? [];
  const pk = data.primaryKey ?? [];
  return (
    <div
      className={cn(
        "rounded-lg border-2 shadow-lg min-w-[200px] max-w-[260px] overflow-hidden bg-white transition-shadow",
        selected ? "ring-2 ring-[var(--brand-teal)] ring-offset-2 border-[var(--brand-teal)]" : "border-slate-200 hover:border-slate-300"
      )}
    >
      <Handle type="target" position={Position.Left} className="!bg-[var(--brand-teal)] !w-3 !h-3 !border-2 !border-white" />
      <Handle type="source" position={Position.Right} className="!bg-[var(--brand-teal)] !w-3 !h-3 !border-2 !border-white" />
      <div className="bg-[var(--brand-teal)] text-white px-3 py-2 font-semibold font-mono flex items-center justify-between">
        <span className="truncate">{data.label}</span>
        <span className="text-[10px] opacity-80">drag to connect</span>
      </div>
      <div className="divide-y divide-slate-200 max-h-48 overflow-y-auto">
        {cols.slice(0, 10).map((c) => (
          <div key={c.name} className="px-3 py-1.5 text-sm flex justify-between gap-2 border-b border-slate-100 last:border-0">
            <span className={pk.includes(c.name) ? "font-medium text-[var(--brand-teal)]" : "text-slate-700"}>
              {c.name}
              {pk.includes(c.name) && " 🔑"}
            </span>
            <span className="text-slate-500 text-xs font-mono truncate">{c.data_type}</span>
          </div>
        ))}
        {cols.length > 10 && <div className="px-3 py-1 text-xs text-slate-500">+{cols.length - 10} more</div>}
        {cols.length === 0 && <div className="px-3 py-2 text-xs text-slate-400 italic">No columns</div>}
      </div>
    </div>
  );
}

const nodeTypes = { editableTable: EditableTableNode };

export function SchemaCanvasEditor({
  schema,
  onChange,
  onSave,
  saving,
  saveDisabled,
  onValidate,
  validateLoading,
}: {
  schema: CustomSchemaDetail | null;
  onChange: (next: CustomSchemaDetail) => void;
  onSave: () => void;
  saving: boolean;
  saveDisabled?: boolean;
  onValidate?: () => void;
  validateLoading?: boolean;
}) {
  const { tables, relationships } = toSchemaDef(schema);
  const [selectedTableName, setSelectedTableName] = useState<string | null>(null);
  const [newColName, setNewColName] = useState("");
  const [newColType, setNewColType] = useState("string");

  const updateSchema = useCallback(
    (tablesNext: TableDef[], relationshipsNext: RelationshipDef[]) => {
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
    },
    [schema, onChange]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState<Node<TableNodeData>>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const tablesKey = useMemo(() => tables.map((t) => t.name).join(","), [tables]);
  const relsKey = useMemo(() => relationships.map((r) => `${r.from_table}-${r.to_table}-${r.name}`).join("|"), [relationships]);

  useEffect(() => {
    const prevNodes = nodes;
    const byId = new Map(prevNodes.map((n) => [n.id, n]));
    const nextNodes: Node<TableNodeData>[] = tables.map((t, i) => {
      const existing = byId.get(t.name);
      const pos = existing?.position ?? { x: (i % 4) * 280, y: Math.floor(i / 4) * 220 };
      return {
        id: t.name,
        type: "editableTable",
        position: pos,
        data: {
          label: t.name,
          columns: t.columns ?? [],
          primaryKey: t.primary_key ?? [],
          tableIndex: i,
        },
      };
    });
    setNodes(nextNodes as never);
    setEdges(
      relationships.map((r, i) => ({
        id: `rel-${i}-${r.from_table}-${r.to_table}`,
        source: r.from_table,
        target: r.to_table,
        label: r.name || `${(r.from_columns ?? []).join(",") || "?"} → ${(r.to_columns ?? []).join(",") || "?"}`,
        type: "smoothstep",
        style: { stroke: "#0d9488", strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "#0d9488" },
      }))
    );
  }, [tablesKey, relsKey, setNodes, setEdges]);

  const addTable = useCallback(() => {
    const name = `table_${tables.length + 1}`;
    const tablesNext = [...tables, { name, columns: [], primary_key: [] }];
    updateSchema(tablesNext, relationships);
    setSelectedTableName(name);
  }, [tables, relationships, updateSchema]);

  const removeTable = useCallback(
    (tableName: string) => {
      const tablesNext = tables.filter((x) => x.name !== tableName);
      const relationshipsNext = relationships.filter((r) => r.from_table !== tableName && r.to_table !== tableName);
      updateSchema(tablesNext, relationshipsNext);
      if (selectedTableName === tableName) setSelectedTableName(null);
    },
    [tables, relationships, selectedTableName, updateSchema]
  );

  const onConnect = useCallback(
    (conn: Connection) => {
      if (!conn.source || !conn.target) return;
      const fromTable = tables.find((t) => t.name === conn.source);
      const toTable = tables.find((t) => t.name === conn.target);
      const fromCols = fromTable?.primary_key?.length ? fromTable.primary_key : fromTable?.columns?.[0] ? [fromTable.columns[0].name] : ["id"];
      const toCols = toTable?.primary_key?.length ? toTable.primary_key : toTable?.columns?.[0] ? [toTable.columns[0].name] : ["id"];
      const relationshipsNext = [
        ...relationships,
        {
          name: `${conn.source}_to_${conn.target}`,
          from_table: conn.source,
          from_columns: fromCols,
          to_table: conn.target,
          to_columns: toCols,
        },
      ];
      updateSchema(tables, relationshipsNext);
      setEdges((eds) =>
        addEdge(
          {
            ...conn,
            type: "smoothstep",
            style: { stroke: "#0d9488", strokeWidth: 2 },
            markerEnd: { type: MarkerType.ArrowClosed, color: "#0d9488" },
          } as Connection,
          eds
        )
      );
    },
    [tables, relationships, updateSchema, setEdges]
  );

  const onEdgesDelete = useCallback(
    (toRemove: Edge[]) => {
      const removeIds = new Set(toRemove.map((e) => e.id));
      const relationshipsNext = relationships.filter((_, i) => !removeIds.has(`rel-${i}-${relationships[i].from_table}-${relationships[i].to_table}`));
      updateSchema(tables, relationshipsNext);
    },
    [tables, relationships, updateSchema]
  );

  const selectedTableIndex = tables.findIndex((t) => t.name === selectedTableName);
  const selectedTable = selectedTableIndex >= 0 ? tables[selectedTableIndex] : null;

  const addColumn = useCallback(() => {
    if (!selectedTable || selectedTableIndex < 0) return;
    const colName = newColName.trim() || `col_${(selectedTable.columns?.length ?? 0) + 1}`;
    const tablesNext = [...tables];
    tablesNext[selectedTableIndex] = {
      ...tablesNext[selectedTableIndex],
      columns: [...(tablesNext[selectedTableIndex].columns ?? []), { name: colName, data_type: newColType, nullable: true }],
    };
    updateSchema(tablesNext, relationships);
    setNewColName("");
  }, [selectedTable, selectedTableIndex, tables, relationships, newColName, newColType, updateSchema]);

  const removeColumn = useCallback(
    (colIdx: number) => {
      if (!selectedTable || selectedTableIndex < 0) return;
      const t = selectedTable;
      const col = t.columns[colIdx];
      const columns = t.columns.filter((_, i) => i !== colIdx);
      const primary_key = (t.primary_key ?? []).filter((pk) => pk !== col.name);
      const tablesNext = [...tables];
      tablesNext[selectedTableIndex] = { ...tablesNext[selectedTableIndex], columns, primary_key };
      updateSchema(tablesNext, relationships);
    },
    [selectedTable, selectedTableIndex, tables, relationships, updateSchema]
  );

  const togglePrimaryKey = useCallback(
    (colName: string) => {
      if (!selectedTable || selectedTableIndex < 0) return;
      const t = selectedTable;
      const pk = t.primary_key ?? [];
      const next = pk.includes(colName) ? pk.filter((p) => p !== colName) : [...pk, colName];
      const tablesNext = [...tables];
      tablesNext[selectedTableIndex] = { ...tablesNext[selectedTableIndex], primary_key: next };
      updateSchema(tablesNext, relationships);
    },
    [selectedTable, selectedTableIndex, tables, relationships, updateSchema]
  );

  const updateColumn = useCallback(
    (colIdx: number, updates: Partial<TableColumn>) => {
      if (!selectedTable || selectedTableIndex < 0) return;
      const t = selectedTable;
      const columns = [...(t.columns ?? [])];
      columns[colIdx] = { ...columns[colIdx], ...updates };
      const tablesNext = [...tables];
      tablesNext[selectedTableIndex] = { ...tablesNext[selectedTableIndex], columns };
      updateSchema(tablesNext, relationships);
    },
    [selectedTable, selectedTableIndex, tables, relationships, updateSchema]
  );

  const updateTableName = useCallback(
    (newName: string) => {
      if (!selectedTable || selectedTableIndex < 0) return;
      const oldName = selectedTable.name;
      const tablesNext = tables.map((t) => (t.name === oldName ? { ...t, name: newName } : t));
      const relationshipsNext = relationships.map((r) => ({
        ...r,
        from_table: r.from_table === oldName ? newName : r.from_table,
        to_table: r.to_table === oldName ? newName : r.to_table,
      }));
      updateSchema(tablesNext, relationshipsNext);
      setSelectedTableName(newName);
    },
    [selectedTable, selectedTableIndex, tables, relationships, updateSchema]
  );

  const nodesWithSelection = nodes.map((n) => ({
    ...n,
    selected: n.id === selectedTableName,
    data: {
      ...n.data,
      tableIndex: tables.findIndex((t) => t.name === n.id),
      columns: tables.find((t) => t.name === n.id)?.columns ?? (n.data as unknown as TableNodeData).columns,
      primaryKey: tables.find((t) => t.name === n.id)?.primary_key ?? (n.data as unknown as TableNodeData).primaryKey,
    },
  }));

  if (!schema) {
    return (
      <Card className="flex-1">
        <CardContent className="py-12 text-center text-slate-500">
          Choose or create a schema first to use the visual editor.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex-1 overflow-hidden flex flex-col min-h-0">
      <CardHeader className="shrink-0 flex flex-row justify-between items-center">
        <CardTitle className="text-base">Visual schema designer</CardTitle>
        <div className="flex gap-2">
          {onValidate && (
            <Button size="sm" variant="outline" onClick={onValidate} disabled={validateLoading}>
              {validateLoading ? "Validating…" : "Validate"}
            </Button>
          )}
          <Button size="sm" onClick={onSave} disabled={saving || saveDisabled}>
            {saving ? "Saving…" : "Save"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex gap-4 min-h-0 p-0">
        <div className="flex-1 min-h-[400px] rounded-br-lg border-r border-b border-slate-200">
          <ReactFlow
            nodes={nodesWithSelection}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onEdgesDelete={onEdgesDelete}
            onNodeClick={(_, node) => setSelectedTableName(node.id)}
            nodeTypes={nodeTypes}
            fitView
            className="bg-slate-50"
          >
            <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
            <Controls />
            <Panel position="top-left" className="m-2">
              <Button size="sm" onClick={addTable} className="shadow-md">
                + Add table
              </Button>
              <p className="text-[10px] text-slate-500 mt-1">Drag from one table to another to create relationships</p>
            </Panel>
          </ReactFlow>
        </div>
        <div className="w-80 shrink-0 border-l border-slate-200 overflow-y-auto">
          {selectedTable ? (
            <div className="p-4 space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-600">Table name</label>
                <input
                  type="text"
                  value={selectedTable.name}
                  onChange={(e) => updateTableName(e.target.value)}
                  className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm font-mono"
                />
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => removeTable(selectedTable.name)}
                className="text-red-600 border-red-200 hover:bg-red-50 w-full"
              >
                Delete table
              </Button>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-700">Columns</span>
                  <div className="flex gap-1 flex-wrap">
                    <input
                      type="text"
                      placeholder="Column"
                      value={newColName}
                      onChange={(e) => setNewColName(e.target.value)}
                      className="w-20 rounded border border-slate-300 px-2 py-0.5 text-xs"
                    />
                    <select
                      value={newColType}
                      onChange={(e) => setNewColType(e.target.value)}
                      className="rounded border border-slate-300 px-2 py-0.5 text-xs"
                    >
                      {DATA_TYPES.map((dt) => (
                        <option key={dt} value={dt}>{dt}</option>
                      ))}
                    </select>
                    <Button size="sm" variant="outline" onClick={addColumn} className="text-xs px-1.5">
                      +
                    </Button>
                  </div>
                </div>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {(selectedTable.columns ?? []).map((col, j) => (
                    <div key={j} className="flex items-center gap-2 p-2 rounded border border-slate-200 bg-white text-sm">
                      <input
                        type="text"
                        value={col.name}
                        onChange={(e) => updateColumn(j, { name: e.target.value })}
                        className="flex-1 min-w-0 rounded border border-slate-300 px-2 py-0.5 text-xs"
                      />
                      <select
                        value={col.data_type ?? "string"}
                        onChange={(e) => updateColumn(j, { data_type: e.target.value })}
                        className="w-20 rounded border border-slate-300 px-1 py-0.5 text-xs"
                      >
                        {DATA_TYPES.map((dt) => (
                          <option key={dt} value={dt}>{dt}</option>
                        ))}
                      </select>
                      <label className="flex items-center gap-0.5 text-xs shrink-0" title="Primary key">
                        <input
                          type="checkbox"
                          checked={(selectedTable.primary_key ?? []).includes(col.name)}
                          onChange={() => togglePrimaryKey(col.name)}
                        />
                        PK
                      </label>
                      <button
                        type="button"
                        onClick={() => removeColumn(j)}
                        className="text-red-500 hover:text-red-700 text-xs px-1"
                        aria-label="Remove column"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                  {(selectedTable.columns ?? []).length === 0 && (
                    <p className="text-xs text-slate-500 py-2">No columns. Add one above.</p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-6 text-center text-slate-500 text-sm">
              <p>Click a table on the canvas to edit its columns.</p>
              <p className="mt-2 text-xs">Or add a new table and start building your schema visually.</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}




