# Migration Rehearsal

Migration rehearsal is a **single cohesive flow** that combines schema evolution, drift, and CDC to help you rehearse data migrations and pipeline changes before production.

---

## What it does

When you select **Migration Rehearsal** in the Create Wizard (or configure it in Advanced Config), Data Forge:

1. **Schema evolution** — Generates tables with realistic structure and relationships.
2. **Schema drift** — Simulates schema changes over time (add column, rename, type change, nullability).
3. **CDC (Change Data Capture)** — Produces INSERT/UPDATE/DELETE operations with `op_type`, `created_at`, `updated_at`, and batch metadata.
4. **Pipeline simulation** — Event streams and linked unstructured artifacts (support tickets, notes) for mixed structured+text pipelines.

Together, this lets you:

- Rehearse migrations on synthetic data before touching production.
- Test CDC consumers against realistic change patterns.
- Validate schema evolution handling in your ETL or warehouse loaders.
- Exercise mixed structured+unstructured pipelines (events + notes).

---

## How to use

### Wizard

1. **Create** → **Choose Input** — Pick a domain pack or custom schema.
2. **Use Case** — Select **Migration Rehearsal**.
3. **Realism** — Adjust scale, messiness, mode, layer if needed (defaults: scale 2000, realistic, CDC).
4. **Export** — Choose format and integrations.
5. **Review & Run** — Preflight runs automatically; click **Run**.

The wizard preconfigures:

- `drift_profile`: mild
- `mode`: cdc
- `messiness`: realistic
- `pipeline_simulation.enabled`: true

### Advanced Config

In **Advanced Configuration**, use:

- **ETL Realism** → Schema drift probability: `mild`, `moderate`, or `aggressive`
- **ETL Realism** → Mode: `cdc`
- **Pipeline Simulation** → Enable pipeline simulation

### Scenario category

When saving a scenario, use category **migration_rehearsal** for easy filtering.

---

## Drift profiles

| Profile      | Behavior                                                                 |
|-------------|---------------------------------------------------------------------------|
| `none`      | No schema drift.                                                          |
| `mild`      | Few drift events (add column, occasional rename).                        |
| `moderate`  | More events; type changes and nullability changes.                        |
| `aggressive`| Many drift events across tables.                                          |

Drift events are recorded in the quality report under `schema_drift`.

---

## CDC mode

With `mode: cdc`, exported data includes:

- `op_type`: INSERT, UPDATE, or DELETE
- `created_at`, `updated_at` timestamps
- `batch_id` for ordering

Use this to test CDC consumers, incremental loaders, and merge logic.

---

## Pipeline simulation

When enabled, the run produces:

- **Event stream** — `event_stream/events.jsonl` with `event_type`, `ts`, `entity_id`, `event_id`
- **Support tickets** — `unstructured/support_tickets.jsonl` linked to events via `entity_id`, `linked_event_id`
- **Link report** — `unstructured/link_report.json` with coverage, orphan detection, severity distribution

See [linked unstructured generation](#linked-unstructured-generation) below.

---

## Linked unstructured generation

Pipeline simulation generates **linked unstructured artifacts** (support tickets, notes) tied to structured events. This supports rehearsal of mixed structured+text pipelines.

### Outputs

| Artifact              | Path                          | Description                                      |
|-----------------------|-------------------------------|--------------------------------------------------|
| Event stream          | `event_stream/events.jsonl`   | Events with `event_type`, `entity_id`, `ts`       |
| Support tickets       | `unstructured/support_tickets.jsonl` | Notes linked to events via `linked_event_id` |
| Link report           | `unstructured/link_report.json`| Coverage, orphan links, severity distribution    |

### Link report

The link report includes:

- `total_events`, `total_unstructured_notes`
- `linked_event_count`, `orphan_link_count`
- `coverage_ratio` — fraction of events with at least one linked note
- `by_severity`, `by_event_type` — distributions

### Run detail page

For runs with pipeline simulation, the run detail page shows:

- Event count
- Linked unstructured count
- Coverage ratio
- Orphan link count (if any)

---

## Related docs

- [Create and config](create-and-config.md) — Wizard and Advanced Config
- [Generation engine](generation-engine.md) — Drift, CDC, messiness stages
- [Use cases](use-cases.md) — ETL simulation, warehouse load, etc.
