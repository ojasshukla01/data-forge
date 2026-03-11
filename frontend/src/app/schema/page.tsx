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
import { fetchPacks, fetchSchemaVisualization } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ApiNode {
  id: string;
  type: string;
  data: { label: string; columns?: { name: string; type: string; nullable: boolean; pk: boolean }[]; primaryKey?: string[] };
  position: { x: number; y: number };
}

interface ApiEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

function TableNode({ data }: { data: { label: string; columns?: { name: string; type: string; pk: boolean }[] } }) {
  const cols = data.columns ?? [];
  return (
    <div className="rounded-lg border-2 border-slate-200 bg-white shadow-md min-w-[200px] overflow-hidden">
      <div className="bg-[var(--brand-teal)] text-white px-3 py-2 font-semibold font-mono">{data.label}</div>
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

function SchemaContent() {
  const searchParams = useSearchParams();
  const packParam = searchParams.get("pack");
  const [packs, setPacks] = useState<{ id: string; description: string }[]>([]);
  const [selectedPack, setSelectedPack] = useState<string>(packParam ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [search, setSearch] = useState("");
  const [sidePanel, setSidePanel] = useState<ApiNode | null>(null);

  const loadSchema = useCallback(async (packId: string) => {
    if (!packId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSchemaVisualization(packId);
      const apiNodes = (data.nodes ?? []) as ApiNode[];
      const apiEdges = (data.edges ?? []) as ApiEdge[];
      const flowNodes: Node[] = apiNodes.map((n) => ({
        id: n.id,
        type: "table",
        position: n.position ?? { x: 0, y: 0 },
        data: n.data,
      }));
      const flowEdges: Edge[] = apiEdges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label,
        style: { stroke: "#06b6d4", strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "#06b6d4" },
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
  }, []);
  useEffect(() => {
    if (packParam) setSelectedPack(packParam);
  }, [packParam]);

  useEffect(() => {
    if (selectedPack) loadSchema(selectedPack);
  }, [selectedPack, loadSchema]);

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
        <div className="flex gap-3 items-center">
          <select
            value={selectedPack}
            onChange={(e) => setSelectedPack(e.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">Select pack</option>
            {packs.map((p) => (
              <option key={p.id} value={p.id}>{p.id}</option>
            ))}
          </select>
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
          ) : !selectedPack ? (
            <div className="h-full flex items-center justify-center text-slate-500">Select a domain pack to visualize</div>
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
