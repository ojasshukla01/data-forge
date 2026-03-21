"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
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
} from "reactflow";
import "reactflow/dist/style.css";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { fetchPacks, fetchCustomSchemas, fetchSchemaVisualization, fetchSchemaVisualizationCustomSchema } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { CustomSchemaSummary } from "@/lib/api";

interface ApiNode {
  id: string;
  type: string;
  data: { label: string; columns?: { name: string; type: string; nullable: boolean; pk: boolean }[]; primaryKey?: string[]; sourceType?: "pack" | "custom" };
  position: { x: number; y: number };
}

interface ApiEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

function TableNode({ data }: { data: { label: string; columns?: { name: string; type: string; pk: boolean }[]; sourceType?: "pack" | "custom" } }) {
  const cols = data.columns ?? [];
  const isCustom = data.sourceType === "custom";
  return (
    <div className={cn("rounded-lg border-2 shadow-md min-w-[200px] overflow-hidden", isCustom ? "border-amber-400 bg-amber-50/30" : "border-slate-200 bg-white")}>
      <div className={cn("text-white px-3 py-2 font-semibold font-mono flex items-center justify-between gap-2", isCustom ? "bg-amber-600" : "bg-[var(--brand-teal)]")}>
        <span>{data.label}</span>
        {isCustom && <span className="text-[10px] uppercase tracking-wider opacity-90">Custom</span>}
      </div>
      <div className="divide-y divide-slate-200 border-t border-slate-200">
        {cols.slice(0, 8).map((c) => (
          <div key={c.name} className="px-3 py-1.5 text-sm flex justify-between gap-4 border-b border-slate-100 last:border-0">
            <span className={c.pk ? "font-medium text-[var(--brand-teal)]" : "text-slate-700"}>
              {c.name}{c.pk ? " 🔑" : ""}
            </span>
            <span className="text-slate-500 text-xs font-mono">{c.type}</span>
          </div>
        ))}
        {cols.length > 8 && <div className="px-3 py-1 text-xs text-slate-500">+{cols.length - 8} more</div>}
      </div>
    </div>
  );
}

const nodeTypes = { table: TableNode };

type SchemaSource = { type: "pack"; id: string } | { type: "custom"; id: string };

function SchemaContent() {
  const searchParams = useSearchParams();
  const packParam = searchParams.get("pack");
  const customParam = searchParams.get("custom");
  const [packs, setPacks] = useState<{ id: string; description: string }[]>([]);
  const [customSchemas, setCustomSchemas] = useState<CustomSchemaSummary[]>([]);
  const [selected, setSelected] = useState<SchemaSource>(
    customParam ? { type: "custom", id: customParam } : packParam ? { type: "pack", id: packParam } : { type: "pack", id: "" }
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [search, setSearch] = useState("");
  const [sidePanel, setSidePanel] = useState<ApiNode | null>(null);

  const loadSchema = useCallback(async (source: SchemaSource) => {
    if (!source.id) return;
    setLoading(true);
    setError(null);
    try {
      const data = source.type === "pack"
        ? await fetchSchemaVisualization(source.id)
        : await fetchSchemaVisualizationCustomSchema(source.id);
      const apiNodes = (data.nodes ?? []) as ApiNode[];
      const apiEdges = (data.edges ?? []) as ApiEdge[];
      const flowNodes: Node[] = apiNodes.map((n) => ({
        id: n.id,
        type: "table",
        position: n.position ?? { x: 0, y: 0 },
        data: { ...n.data, sourceType: data.source_type ?? "pack" },
      }));
      const edgeColor = data.source_type === "custom" ? "#d97706" : "#06b6d4";
      const flowEdges: Edge[] = apiEdges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        style: { stroke: edgeColor, strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: edgeColor },
        type: "smoothstep",
      }));
      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load schema");
      setNodes([]);
      setEdges([]);
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    fetchPacks().then(setPacks).catch(() => setPacks([]));
    fetchCustomSchemas().then(setCustomSchemas).catch(() => setCustomSchemas([]));
  }, []);
  useEffect(() => {
    if (customParam) setSelected({ type: "custom", id: customParam });
    else if (packParam) setSelected({ type: "pack", id: packParam });
  }, [packParam, customParam]);

  useEffect(() => {
    if (selected.id) loadSchema(selected);
  }, [selected.type, selected.id, loadSchema]);

  const onConnect = useCallback(
    (conn: Connection) => setEdges((eds) => addEdge(conn, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    const apiNode = nodes.find((n) => n.id === node.id);
    if (apiNode) setSidePanel({ id: apiNode.id, type: "table", data: apiNode.data, position: apiNode.position });
  }, [nodes]);

  const filteredNodes = search
    ? nodes.filter((n) => (n.data?.label as string)?.toLowerCase().includes(search.toLowerCase()))
    : null;

  const highlightNodeIds = filteredNodes ? new Set(filteredNodes.map((n) => n.id)) : null;

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Schema Visualizer</h1>
          <p className="text-slate-600 text-sm">Explore table structure and relationships</p>
        </div>
        <div className="flex gap-4 items-end flex-wrap">
          <div className="flex flex-col gap-1">
            <label htmlFor="pack-select" className="text-xs font-medium text-slate-600">Domain pack</label>
            <select
              id="pack-select"
              value={selected.type === "pack" ? selected.id : ""}
              onChange={(e) => {
                const id = e.target.value;
                setSelected({ type: "pack", id: id || "" });
              }}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm min-w-[180px]"
            >
              <option value="">Select pack…</option>
              {packs.map((p) => (
                <option key={p.id} value={p.id}>{p.id}</option>
              ))}
              {packs.length === 0 && <option disabled>No packs</option>}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="custom-select" className="text-xs font-medium text-slate-600">Custom schema</label>
            <select
              id="custom-select"
              value={selected.type === "custom" ? selected.id : ""}
              onChange={(e) => {
                const id = e.target.value;
                setSelected({ type: "custom", id: id || "" });
              }}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm min-w-[180px]"
            >
              <option value="">Select custom…</option>
              {customSchemas.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
              {customSchemas.length === 0 && <option disabled>None — create in Schema Studio</option>}
            </select>
          </div>
          <Link href="/schema/studio"><Button variant="ghost" size="sm">Schema Studio</Button></Link>
          <input
            type="text"
            placeholder="Search table"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm w-40"
          />
          <Link href="/templates"><Button variant="ghost" size="sm">Templates</Button></Link>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
      )}

      <div className="flex-1 flex gap-4 min-h-0">
        <div className="flex-1 rounded-xl border border-slate-200 bg-slate-50 overflow-hidden">
          {loading ? (
            <div className="h-full flex items-center justify-center text-slate-500">Loading…</div>
          ) : !selected.id ? (
            <div className="h-full flex items-center justify-center text-slate-500">Select a domain pack or custom schema above</div>
          ) : nodes.length === 0 ? (
            <div className="h-full flex items-center justify-center text-slate-500">No schema data</div>
          ) : (
            <ReactFlow
              nodes={nodes.map((n) => ({
                ...n,
                className: highlightNodeIds && !highlightNodeIds.has(n.id) ? "opacity-40" : undefined,
              }))}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              nodeTypes={nodeTypes}
              fitView
            >
              <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
              <Controls />
            </ReactFlow>
          )}
        </div>
        {sidePanel && (
          <Card className="w-80 shrink-0">
            <CardHeader className="flex flex-row justify-between items-center py-3">
              <CardTitle className="text-base">{sidePanel.data?.label}</CardTitle>
              <button onClick={() => setSidePanel(null)} className="text-slate-400 hover:text-slate-600">×</button>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-slate-500 mb-2">Columns</p>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {(sidePanel.data?.columns ?? []).map((c) => (
                  <div key={c.name} className="flex justify-between text-sm py-1 border-b border-slate-100">
                    <span>{c.name}{c.pk ? " (PK)" : ""}</span>
                    <span className="text-slate-500">{c.type}</span>
                  </div>
                ))}
              </div>
              {sidePanel.data?.primaryKey?.length ? (
                <p className="text-xs text-slate-500 mt-3">Primary key: {sidePanel.data.primaryKey.join(", ")}</p>
              ) : null}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default function SchemaPage() {
  return (
    <Suspense fallback={<div className="p-8 text-slate-500">Loading…</div>}>
      <SchemaContent />
    </Suspense>
  );
}
