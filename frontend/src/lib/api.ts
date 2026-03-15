import { API_BASE } from "./utils";

export interface PackInfo {
  id: string;
  name?: string;
  description: string;
  category?: string;
  tables_count?: number;
  relationships_count?: number;
  key_entities?: string[];
  recommended_use_cases?: string[];
  supported_features?: string[];
  supports_event_streams?: boolean;
  simulation_event_types?: string[];
  benchmark_relevance?: "low" | "medium" | "high";
}

export interface PackDetail {
  id: string;
  name: string;
  description: string;
  category?: string;
  tables: { name: string; columns: string[]; primary_key: string[] }[];
  relationships_count: number;
  key_entities?: string[];
  recommended_use_cases?: string[];
  supported_features?: string[];
  supports_event_streams?: boolean;
  simulation_event_types?: string[];
  benchmark_relevance?: "low" | "medium" | "high";
}

export async function fetchPacks(): Promise<PackInfo[]> {
  const res = await fetch(`${API_BASE}/api/domain-packs`);
  if (!res.ok) throw new Error("Failed to fetch packs");
  return res.json();
}

export async function fetchPack(id: string): Promise<PackDetail> {
  const res = await fetch(`${API_BASE}/api/domain-packs/${id}`);
  if (!res.ok) throw new Error("Failed to fetch pack");
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

export async function runGenerate(config: Record<string, unknown>) {
  const res = await fetch(`${API_BASE}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = Array.isArray(data.detail) ? data.detail.join("; ") : (data.detail || JSON.stringify(data.errors || "Generation failed"));
    throw new Error(msg);
  }
  return data;
}

export async function runPreflight(config: Record<string, unknown>) {
  const res = await fetch(`${API_BASE}/api/preflight`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Preflight failed");
  return data;
}

export async function runValidate(params: {
  schema_path: string;
  data_path: string;
  rules_path?: string;
  privacy_mode?: string;
}) {
  const res = await fetch(`${API_BASE}/api/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Validation failed");
  return data;
}

export async function fetchArtifacts(runId?: string, typeFilter?: string) {
  const q = new URLSearchParams();
  if (runId) q.set("run_id", runId);
  if (typeFilter && typeFilter !== "all") q.set("type_filter", typeFilter);
  const url = `${API_BASE}/api/artifacts${q.toString() ? "?" + q : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch artifacts");
  return res.json();
}

export async function runValidateGe(params: {
  expectations_path: string;
  data_path: string;
}) {
  const res = await fetch(`${API_BASE}/api/validate/ge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "GE validation failed");
  return data;
}

export async function runReconcile(params: {
  manifest_path: string;
  data_path: string;
  schema_path?: string;
}) {
  const res = await fetch(`${API_BASE}/api/reconcile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Reconciliation failed");
  return data;
}

export async function fetchSchemaVisualization(packId: string) {
  const res = await fetch(`${API_BASE}/api/schema/visualize?pack_id=${encodeURIComponent(packId)}`);
  if (!res.ok) throw new Error("Failed to fetch schema");
  return res.json();
}

export async function fetchSchemaPreview(schema: Record<string, unknown>, rowsPerTable = 3): Promise<Record<string, Record<string, unknown>[]>> {
  const res = await fetch(`${API_BASE}/api/schema/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ schema, rows_per_table: rowsPerTable }),
  });
  if (!res.ok) throw new Error("Failed to preview schema");
  return res.json();
}

export async function startRunGenerate(config: Record<string, unknown>) {
  const res = await fetch(`${API_BASE}/api/runs/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to start run");
  return data as { run_id: string; status: string };
}

export async function fetchRuns(params?: {
  status?: string;
  run_type?: string;
  pack?: string;
  mode?: string;
  layer?: string;
  source_scenario_id?: string;
  limit?: number;
  include_archived?: boolean;
}) {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.run_type) q.set("run_type", params.run_type);
  if (params?.pack) q.set("pack", params.pack);
  if (params?.mode) q.set("mode", params.mode);
  if (params?.layer) q.set("layer", params.layer);
  if (params?.source_scenario_id) q.set("source_scenario_id", params.source_scenario_id);
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.include_archived !== undefined) q.set("include_archived", String(params.include_archived));
  const url = `${API_BASE}/api/runs${q.toString() ? "?" + q : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch runs");
  return res.json() as Promise<{ runs: RunRecord[] }>;
}

export interface StorageUsage {
  runs_count: number;
  artifact_count: number;
  total_size_bytes: number;
  total_size_mb: number;
  by_run: { run_id: string; run_type?: string; status?: string; created_at?: number; size_bytes: number; pinned?: boolean; archived_at?: number }[];
}

export async function fetchStorageSummary(): Promise<StorageUsage> {
  const res = await fetch(`${API_BASE}/api/runs/storage/summary`);
  if (!res.ok) throw new Error("Failed to fetch storage summary");
  return res.json();
}

export interface CleanupPreview {
  dry_run: boolean;
  candidates: { run_id: string; run_type?: string; status?: string; created_at?: number; age_days?: number }[];
  policy: { retention_count: number; retention_days?: number };
}

export async function fetchCleanupPreview(params?: { retention_count?: number; retention_days?: number }): Promise<CleanupPreview> {
  const q = new URLSearchParams();
  if (params?.retention_count != null) q.set("retention_count", String(params.retention_count));
  if (params?.retention_days != null) q.set("retention_days", String(params.retention_days));
  const url = `${API_BASE}/api/runs/cleanup/preview${q.toString() ? "?" + q : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch cleanup preview");
  return res.json();
}

export async function executeCleanup(params?: { delete_artifacts?: boolean; retention_count?: number; retention_days?: number }) {
  const res = await fetch(`${API_BASE}/api/runs/cleanup/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params ?? {}),
  });
  if (!res.ok) throw new Error("Failed to execute cleanup");
  return res.json() as Promise<{ deleted_run_records: number; deleted_artifact_dirs: number; run_ids_affected?: string[] }>;
}

export async function archiveRun(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/archive`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to archive run");
  return res.json() as Promise<RunRecord>;
}

export async function unarchiveRun(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/unarchive`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to unarchive run");
  return res.json() as Promise<RunRecord>;
}

export async function deleteRun(runId: string, deleteArtifacts = false) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ delete_artifacts: deleteArtifacts }),
  });
  if (!res.ok) throw new Error("Failed to delete run");
  return res.json() as Promise<{ deleted: string }>;
}

export async function pinRun(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/pin`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to pin run");
  return res.json() as Promise<RunRecord>;
}

export async function unpinRun(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/unpin`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to unpin run");
  return res.json() as Promise<RunRecord>;
}

export async function fetchRunLogs(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/logs`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch logs");
  return res.json() as Promise<{ events: RunEvent[] }>;
}

export async function runBenchmark(params?: {
  pack?: string;
  scale?: number;
  scale_preset?: string;
  profile?: string;
  format?: string;
  iterations?: number;
}) {
  const res = await fetch(`${API_BASE}/api/benchmark`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params ?? {}),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Benchmark failed");
  return data;
}

export async function startBenchmarkRun(params?: {
  pack?: string;
  scale?: number;
  scale_preset?: string;
  profile?: string;
  format?: string;
  iterations?: number;
}) {
  const res = await fetch(`${API_BASE}/api/runs/benchmark`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params ?? {}),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to start benchmark");
  return data as { run_id: string; status: string };
}

export interface RunEvent {
  level: string;
  message: string;
  ts: number;
}

export async function fetchRunDetail(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch run");
  return res.json() as Promise<RunRecord>;
}

export async function fetchRunStatus(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/status`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
}

export async function rerunRun(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/rerun`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to rerun");
  return res.json() as Promise<{ run_id: string; status: string }>;
}

export async function cloneRunConfig(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/clone`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to clone config");
  return res.json() as Promise<{
    config: Record<string, unknown>;
    has_masked_sensitive_fields?: boolean;
    masked_fields?: string[];
  }>;
}

export interface RunArtifact {
  type?: string;
  name: string;
  path: string;
  size?: number;
  created_at?: number;
}

export interface ScenarioRecord {
  id: string;
  name: string;
  description?: string;
  category: string;
  tags?: string[];
  source_pack?: string;
  config: Record<string, unknown>;
  config_summary?: Record<string, unknown>;
  created_at?: number;
  updated_at?: number;
  created_from_run_id?: string;
  created_from_scenario_id?: string;
  key_features?: string[];
  uses_pipeline_simulation?: boolean;
  uses_benchmark?: boolean;
  has_masked_sensitive_fields?: boolean;
  masked_fields?: string[];
}

export async function fetchScenarios(params?: { category?: string; source_pack?: string; search?: string }) {
  const q = new URLSearchParams();
  if (params?.category) q.set("category", params.category);
  if (params?.source_pack) q.set("source_pack", params.source_pack);
  if (params?.search) q.set("search", params.search);
  const res = await fetch(`${API_BASE}/api/scenarios${q.toString() ? "?" + q : ""}`);
  if (!res.ok) throw new Error("Failed to fetch scenarios");
  return res.json() as Promise<{ scenarios: ScenarioRecord[] }>;
}

export async function fetchScenario(id: string) {
  const res = await fetch(`${API_BASE}/api/scenarios/${id}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch scenario");
  return res.json() as Promise<ScenarioRecord>;
}

export async function createScenario(payload: {
  name: string;
  description?: string;
  category?: string;
  tags?: string[];
  config: Record<string, unknown>;
  created_from_run_id?: string;
  created_from_scenario_id?: string;
}) {
  const res = await fetch(`${API_BASE}/api/scenarios`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to create scenario");
  return data as ScenarioRecord;
}

export async function updateScenario(id: string, payload: Partial<{ name: string; description: string; category: string; tags: string[]; config: Record<string, unknown> }>) {
  const res = await fetch(`${API_BASE}/api/scenarios/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to update scenario");
  return data as ScenarioRecord;
}

export async function deleteScenario(id: string) {
  const res = await fetch(`${API_BASE}/api/scenarios/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete scenario");
  return res.json();
}

export async function runFromScenario(scenarioId: string) {
  const res = await fetch(`${API_BASE}/api/scenarios/${scenarioId}/run`, { method: "POST" });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to run scenario");
  return data as { run_id: string; status: string };
}

export async function createScenarioFromRun(runId: string, payload?: { name?: string; description?: string; category?: string }) {
  const res = await fetch(`${API_BASE}/api/scenarios/from-run/${runId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload ?? {}),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to create scenario from run");
  return data as ScenarioRecord;
}

export async function importScenario(payload: { name: string; description?: string; category?: string; tags?: string[]; config: Record<string, unknown> }) {
  const res = await fetch(`${API_BASE}/api/scenarios/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to import scenario");
  return data as ScenarioRecord;
}

export async function exportScenario(id: string) {
  const res = await fetch(`${API_BASE}/api/scenarios/${id}/export`);
  if (!res.ok) throw new Error("Failed to export scenario");
  return res.json();
}

export async function fetchRunComparison(leftId: string, rightId: string) {
  const res = await fetch(`${API_BASE}/api/runs/compare?left=${encodeURIComponent(leftId)}&right=${encodeURIComponent(rightId)}`);
  if (!res.ok) throw new Error("Failed to compare runs");
  return res.json();
}

export interface RunMetricsSummary {
  total_runs: number;
  runs_by_type: Record<string, number>;
  runs_by_status: Record<string, number>;
  average_duration_seconds: number | null;
  total_rows_generated: number;
  artifact_count: number;
  storage_mb: number;
  cleanup_candidates_count: number;
  failure_categories: Record<string, number>;
}

export async function fetchRunMetrics(limit?: number): Promise<RunMetricsSummary> {
  const q = limit != null ? `?limit=${limit}` : "";
  const res = await fetch(`${API_BASE}/api/runs/metrics${q}`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export interface RunTimelineStage {
  name: string;
  duration_seconds: number;
  status?: string;
  message?: string;
}

export interface RunTimeline {
  run_id: string;
  status?: string;
  run_type?: string;
  total_duration_seconds?: number;
  started_at?: number;
  finished_at?: number;
  stages: RunTimelineStage[];
  stage_progress_full?: Record<string, unknown>[];
  events: { level: string; message: string; ts: number }[];
  slowest_stage?: string;
  slowest_stage_duration_seconds?: number;
  why_slow_hint?: string;
  error_message?: string;
}

export async function fetchRunTimeline(runId: string): Promise<RunTimeline | null> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/timeline`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch timeline");
  return res.json();
}

export interface RunRecord {
  id: string;
  status: string;
  created_at?: number;
  started_at?: number;
  finished_at?: number;
  duration_seconds?: number;
  run_type?: string;
  config_summary?: Record<string, unknown>;
  selected_pack?: string;
  source_scenario_id?: string;
  stage_progress?: { name: string; status: string; message?: string; duration_seconds?: number }[];
  warnings?: string[];
  error_message?: string;
  result_summary?: Record<string, unknown>;
  artifact_paths?: string[];
  artifacts?: RunArtifact[];
  output_dir?: string;
  events?: RunEvent[];
  pinned?: boolean;
  archived_at?: number;
}

// Scenario versioning
export interface ScenarioVersionInfo {
  version: number;
  updated_at?: number;
}

export interface ScenarioVersionsResponse {
  scenario_id: string;
  versions: ScenarioVersionInfo[];
  current_version: number;
}

export interface ScenarioVersionDetailResponse {
  scenario_id: string;
  version: number;
  config: Record<string, unknown>;
  updated_at?: number;
}

export interface ScenarioDiffChange {
  key: string;
  left: unknown;
  right: unknown;
}

export interface ScenarioDiffResponse {
  left_version: number;
  right_version: number;
  changed: ScenarioDiffChange[];
}

export async function fetchScenarioVersions(scenarioId: string): Promise<ScenarioVersionsResponse | null> {
  const res = await fetch(`${API_BASE}/api/scenarios/${scenarioId}/versions`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch scenario versions");
  return res.json();
}

export async function fetchScenarioVersionConfig(scenarioId: string, version: number): Promise<ScenarioVersionDetailResponse | null> {
  const res = await fetch(`${API_BASE}/api/scenarios/${scenarioId}/versions/${version}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch scenario version config");
  return res.json();
}

export async function fetchScenarioDiff(scenarioId: string, left: number, right: number): Promise<ScenarioDiffResponse | null> {
  const res = await fetch(`${API_BASE}/api/scenarios/${scenarioId}/diff?left=${left}&right=${right}`);
  if (res.status === 404 || res.status === 400) return null;
  if (!res.ok) throw new Error("Failed to fetch scenario diff");
  return res.json();
}

// Run lineage and manifest
export interface RunLineage {
  run_id: string;
  run_type?: string;
  scenario_id?: string;
  scenario?: { id: string; name?: string; version?: number };
  pack?: string;
  custom_schema_id?: string;
  custom_schema_version?: number;
  custom_schema_name?: string;
  schema_source_type?: "pack" | "custom_schema";
  /** True when run used a custom schema that has since been deleted. Metadata (name, id, version, snapshot) is preserved. */
  schema_missing?: boolean;
  custom_schema_snapshot_hash?: string;
  custom_schema_table_names?: string[];
  artifact_run_id?: string;
  output_dir?: string;
}

export interface RunManifest {
  run_id: string;
  output_run_id?: string;
  run_type?: string;
  scenario_id?: string;
  scenario_version?: number;
  config_schema_version?: number;
  seed?: number;
  pack?: string;
  custom_schema_id?: string;
  custom_schema_version?: number;
  custom_schema_name?: string;
  schema_source_type?: "pack" | "custom_schema";
  schema_missing?: boolean;
  custom_schema_snapshot_hash?: string;
  custom_schema_table_names?: string[];
  scale?: number;
  mode?: string;
  layer?: string;
  total_rows_generated?: number;
  duration_seconds?: number;
  storage_backend?: string;
  git_commit_sha?: string;
  platform?: string;
  python_version?: string;
  created_at?: number;
  manifest_version?: number;
}

export async function fetchRunLineage(runId: string): Promise<RunLineage | null> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/lineage`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch run lineage");
  return res.json();
}

export async function fetchRunManifest(runId: string): Promise<RunManifest | null> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/manifest`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch run manifest");
  return res.json();
}

// Custom Schema Studio

export interface CustomSchemaSummary {
  id: string;
  name: string;
  description?: string;
  tags?: string[];
  version: number;
  created_at?: number;
  updated_at?: number;
}

export interface CustomSchemaDetail {
  id: string;
  name: string;
  description?: string;
  tags?: string[];
  version: number;
  created_at?: number;
  updated_at?: number;
  schema: Record<string, unknown>;
}

export interface CustomSchemaVersionInfo {
  version: number;
  updated_at?: number;
}

export interface CustomSchemaVersionsResponse {
  schema_id: string;
  versions: CustomSchemaVersionInfo[];
  current_version: number;
}

export async function fetchCustomSchemas(): Promise<CustomSchemaSummary[]> {
  const res = await fetch(`${API_BASE}/api/custom-schemas`);
  if (!res.ok) throw new Error("Failed to fetch custom schemas");
  return res.json();
}

export async function fetchCustomSchema(id: string): Promise<CustomSchemaDetail | null> {
  const res = await fetch(`${API_BASE}/api/custom-schemas/${id}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch custom schema");
  return res.json();
}

export async function createCustomSchema(payload: {
  name: string;
  description?: string;
  tags?: string[];
  schema: Record<string, unknown>;
  created_from?: string;
}): Promise<CustomSchemaDetail> {
  const res = await fetch(`${API_BASE}/api/custom-schemas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    const err: Error & { detail?: { schema_errors?: string[] } } = new Error(
      typeof data.detail === "object" && data.detail?.schema_errors
        ? data.detail.schema_errors.join("; ")
        : (data.detail || "Failed to create custom schema")
    );
    err.detail = data.detail;
    throw err;
  }
  return data;
}

export async function updateCustomSchema(id: string, payload: Partial<{
  name: string;
  description: string;
  tags: string[];
  schema: Record<string, unknown>;
}>): Promise<CustomSchemaDetail> {
  const res = await fetch(`${API_BASE}/api/custom-schemas/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    const err: Error & { detail?: { schema_errors?: string[] } } = new Error(
      typeof data.detail === "object" && data.detail?.schema_errors
        ? data.detail.schema_errors.join("; ")
        : (data.detail || "Failed to update custom schema")
    );
    err.detail = data.detail;
    throw err;
  }
  return data;
}

export async function fetchCustomSchemaVersions(id: string): Promise<CustomSchemaVersionsResponse | null> {
  const res = await fetch(`${API_BASE}/api/custom-schemas/${id}/versions`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch custom schema versions");
  return res.json();
}

export interface CustomSchemaDiffResponse {
  schema_id: string;
  left_version: number;
  right_version: number;
  changed: { key: string; left: unknown; right: unknown }[];
  tables_added?: string[];
  tables_removed?: string[];
  tables_modified?: { table: string; columns_added: string[]; columns_removed: string[]; columns_modified: string[] }[];
  summary?: { tables_added: number; tables_removed: number; tables_modified: number };
}

export async function fetchCustomSchemaDiff(id: string, left: number, right: number): Promise<CustomSchemaDiffResponse | null> {
  const res = await fetch(`${API_BASE}/api/custom-schemas/${id}/diff?left=${left}&right=${right}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to diff custom schema versions");
  return res.json();
}

export async function restoreSchemaVersion(schemaId: string, version: number): Promise<CustomSchemaDetail> {
  const res = await fetch(`${API_BASE}/api/custom-schemas/${schemaId}/versions/${version}/restore`, {
    method: "POST",
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Failed to restore version");
  return data;
}

export interface CustomSchemaValidateResponse {
  valid: boolean;
  errors: string[];
  warnings?: string[];
}

export async function validateCustomSchema(schema: Record<string, unknown>): Promise<CustomSchemaValidateResponse> {
  const res = await fetch(`${API_BASE}/api/custom-schemas/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ schema }),
  });
  if (!res.ok) throw new Error("Validation request failed");
  return res.json();
}
