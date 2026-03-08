"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { runValidate, runValidateGe, runReconcile, fetchRuns } from "@/lib/api";
import { cn } from "@/lib/utils";
import Link from "next/link";

type TabId = "schema" | "ge" | "reconcile";

interface ValidationReport {
  referential_integrity?: boolean;
  rule_violations?: { total?: number };
  referential_errors?: string[];
}

interface ValidationResult {
  success?: boolean;
  report?: ValidationReport;
  ge_validation?: { passed?: number; failed?: number; failures?: { suite: string; reason: string }[] };
  missing_tables?: string[];
  row_count_diffs?: Record<string, unknown>;
  [key: string]: unknown;
}

const TABS: { id: TabId; label: string; desc: string }[] = [
  { id: "schema", label: "Schema & Rules", desc: "Validate data against schema and business rules. Checks column types, nullability, referential integrity, and rule violations." },
  { id: "ge", label: "Great Expectations", desc: "Run expectation suites against your data without full GE runtime. Validates row counts, nulls, uniqueness, value sets." },
  { id: "reconcile", label: "Manifest Reconciliation", desc: "Compare manifest expected row counts vs actual data. Find missing tables, row diffs, duplicate PKs." },
];

export default function ValidatePage() {
  const [tab, setTab] = useState<TabId>("schema");
  const [schemaPath, setSchemaPath] = useState("");
  const [dataPath, setDataPath] = useState("");
  const [rulesPath, setRulesPath] = useState("");
  const [privacyMode, setPrivacyMode] = useState("off");
  const [expectationsPath, setExpectationsPath] = useState("");
  const [manifestPath, setManifestPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recentRuns, setRecentRuns] = useState<{ id: string; outputId?: string; pack?: string }[]>([]);

  useEffect(() => {
    fetchRuns({ status: "succeeded", limit: 20 })
      .then((d) => {
        const runs = (d.runs ?? []).map((r) => ({
          id: r.id,
          outputId: (r.result_summary as { artifact_run_id?: string })?.artifact_run_id,
          pack: r.selected_pack,
        })).filter((r) => r.outputId);
        setRecentRuns(runs);
        if (runs.length > 0 && !dataPath) {
          const first = runs[0];
          setDataPath(`output/${first.outputId}`);
          setSchemaPath(first.pack ? `schemas/${first.pack}.sql` : "");
          setExpectationsPath(`output/${first.outputId}/great_expectations`);
          setManifestPath(`output/${first.outputId}/manifest.json`);
        }
      })
      .catch(() => {});
  }, []);

  const loadFromRun = (r: { outputId: string; pack?: string }) => {
    setDataPath(`output/${r.outputId}`);
    setSchemaPath(r.pack ? `schemas/${r.pack}.sql` : "");
    setRulesPath(r.pack ? `rules/${r.pack}.yaml` : "");
    setExpectationsPath(`output/${r.outputId}/great_expectations`);
    setManifestPath(`output/${r.outputId}/manifest.json`);
  };

  const runSchema = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const data = await runValidate({ schema_path: schemaPath, data_path: dataPath, rules_path: rulesPath || undefined, privacy_mode: privacyMode });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed");
    } finally {
      setLoading(false);
    }
  };

  const runGe = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const data = await runValidateGe({ expectations_path: expectationsPath, data_path: dataPath });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "GE validation failed");
    } finally {
      setLoading(false);
    }
  };

  const runRecon = async () => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const data = await runReconcile({ manifest_path: manifestPath, data_path: dataPath });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reconciliation failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRun = () => {
    if (tab === "schema") runSchema();
    else if (tab === "ge") runGe();
    else runRecon();
  };

  const downloadReport = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `validation-report-${tab}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Validation Center</h1>
        <p className="mt-1 text-slate-600">
          Validate existing datasets against schema, rules, GE expectations, manifests, and contracts.
        </p>
      </div>

      <div className="flex gap-2 border-b border-slate-200 pb-2">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => { setTab(t.id); setResult(null); setError(null); }}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium",
              tab === t.id ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{TABS.find((t) => t.id === tab)?.label}</CardTitle>
          <p className="text-sm text-slate-600 mt-1">{TABS.find((t) => t.id === tab)?.desc}</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {recentRuns.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Load paths from run</label>
              <select
                className="w-full max-w-md rounded-lg border border-slate-300 px-3 py-2 text-sm"
                onChange={(e) => {
                  const v = e.target.value;
                  if (v) {
                    const r = recentRuns.find((x) => `${x.outputId}` === v || x.id === v);
                    if (r?.outputId) loadFromRun({ outputId: r.outputId, pack: r.pack });
                  }
                }}
              >
                <option value="">Select a completed run…</option>
                {recentRuns.map((r) => (
                  <option key={r.id} value={r.outputId ?? r.id}>
                    {r.outputId} {r.pack ? `(${r.pack})` : ""}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Data path</label>
              <input
                type="text"
                value={dataPath}
                onChange={(e) => setDataPath(e.target.value)}
                placeholder="output/run_xxx or select from run above"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono"
              />
            </div>
            {tab === "schema" && (
              <>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Schema path</label>
                  <input
                    type="text"
                    value={schemaPath}
                    onChange={(e) => setSchemaPath(e.target.value)}
                    placeholder="schemas/saas_billing.sql"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Rules path (optional)</label>
                  <input
                    type="text"
                    value={rulesPath}
                    onChange={(e) => setRulesPath(e.target.value)}
                    placeholder="rules/saas_billing.yaml"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Privacy mode</label>
                  <select
                    value={privacyMode}
                    onChange={(e) => setPrivacyMode(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  >
                    <option value="off">Off</option>
                    <option value="warn">Warn</option>
                    <option value="strict">Strict</option>
                  </select>
                </div>
              </>
            )}
            {tab === "ge" && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Expectations path</label>
                <input
                  type="text"
                  value={expectationsPath}
                  onChange={(e) => setExpectationsPath(e.target.value)}
                  placeholder="output/run_xxx/great_expectations"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono"
                />
              </div>
            )}
            {tab === "reconcile" && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Manifest path</label>
                <input
                  type="text"
                  value={manifestPath}
                  onChange={(e) => setManifestPath(e.target.value)}
                  placeholder="output/run_xxx/manifest.json"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono"
                />
              </div>
            )}
          </div>
          <div className="flex gap-3">
            <Button onClick={handleRun} disabled={loading}>
              {loading ? "Validating…" : "Run Validation"}
            </Button>
            {result && (
              <Button variant="outline" size="sm" onClick={downloadReport}>Download JSON</Button>
            )}
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <p className="text-xs text-slate-500">Paths are relative to project root. Ensure a run has completed first or provide paths to existing data.</p>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {tab === "schema" && (
              <>
                <div className="flex gap-4 flex-wrap">
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-slate-100">
                    {result.success ? "Passed" : "Failed"}
                  </span>
                  {result.report && typeof result.report === "object" ? (
                    <>
                      {result.report?.referential_integrity !== undefined ? (
                        <span className={cn(
                          "px-3 py-1 rounded-full text-sm",
                          result.report.referential_integrity ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                        )}>
                          Ref integrity: {String(result.report.referential_integrity)}
                        </span>
                      ) : null}
                      {result.report.rule_violations && result.report.rule_violations.total !== undefined ? (
                        <span className="px-3 py-1 rounded-full text-sm bg-slate-100">
                          Rule violations: {result.report.rule_violations.total}
                        </span>
                      ) : null}
                    </>
                  ) : null}
                </div>
                {result.report?.referential_errors && Array.isArray(result.report.referential_errors) && (result.report.referential_errors as string[]).length > 0 ? (
                  <div className="text-sm">
                    <p className="font-medium text-slate-700 mb-2">Referential errors</p>
                    <ul className="list-disc list-inside text-red-600">{(result.report.referential_errors as string[]).slice(0, 10).map((e, i) => <li key={i}>{e}</li>)}</ul>
                  </div>
                ) : null}
              </>
            )}
            {tab === "ge" && result.ge_validation ? (
              <div className="space-y-2">
                <p className="text-sm">Suites: {(result.ge_validation as { passed?: number }).passed ?? 0} passed, {(result.ge_validation as { failed?: number }).failed ?? 0} failed</p>
                {(result.ge_validation as { failures?: { suite: string; reason: string }[] }).failures?.length ? (
                  <ul className="list-disc list-inside text-sm text-red-600">
                    {((result.ge_validation as { failures: { suite: string; reason: string }[] }).failures).slice(0, 10).map((f, i) => (
                      <li key={i}>{f.suite}: {f.reason}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
            {tab === "reconcile" ? (
              <div className="text-sm space-y-2">
                {result.missing_tables && (result.missing_tables as string[]).length > 0 ? (
                  <p className="text-red-600">Missing tables: {(result.missing_tables as string[]).join(", ")}</p>
                ) : null}
                {result.row_count_diffs && Object.keys(result.row_count_diffs as Record<string, unknown>).length > 0 ? (
                  <div>
                    <p className="font-medium mb-2">Row count diffs</p>
                    <pre className="p-3 bg-slate-50 rounded text-xs overflow-x-auto">{JSON.stringify(result.row_count_diffs, null, 2)}</pre>
                  </div>
                ) : null}
                {!result.missing_tables?.length && !(result.row_count_diffs && Object.keys(result.row_count_diffs as Record<string, unknown>).length) ? (
                  <p className="text-green-600">Manifest matches data.</p>
                ) : null}
              </div>
            ) : null}
            <pre className="p-4 bg-slate-50 rounded-lg text-xs overflow-x-auto max-h-64 overflow-y-auto font-mono">
              {JSON.stringify(result, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      <div className="flex gap-2">
        <Link href="/artifacts"><Button variant="ghost" size="sm">Browse artifacts</Button></Link>
        <Link href="/runs"><Button variant="ghost" size="sm">View runs</Button></Link>
      </div>
    </div>
  );
}
