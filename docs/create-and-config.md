# Create flow, wizard, and advanced config

This document explains how to create scenarios and runs using the **Create Wizard** and **Advanced Configuration** in the Product UI, and how they relate to the underlying config schema.

---

## Create Wizard

The Create Wizard is a guided path for common generation flows. It is optimized for:

- Picking a **domain pack** quickly.
- Choosing a **use case preset** (demo, unit test, integration test, ETL, warehouse load).
- Tuning core realism knobs (scale, messiness, mode, layer).
- Choosing export format and integrations.
- Running **preflight** and launching a run.
- Optionally **saving a scenario** for reuse.

Wizard steps:

1. **Choose input**
   - Start from scratch: pick a **domain pack** from the available pack list.
   - Use a saved scenario: select from existing scenarios; the wizard prefills fields from that config.
2. **Use Case**
   - Presets for demo, unit test, integration test, ETL simulation, warehouse load.
   - Each preset sets scale and messiness defaults; you can still edit them later.
3. **Realism**
   - Scale (base row count hint).
   - Messiness (clean → realistic → chaotic).
   - Mode (full snapshot, incremental, CDC).
   - Layer (bronze, silver, gold, all).
4. **Export**
   - Export format (CSV / JSON / JSONL / Parquet / SQL).
   - Integrations: dbt seeds, Great Expectations, Airflow DAGs, OpenAPI contracts.
5. **Review & Run**
   - Summary of pack, scale, messiness, mode, layer, export format.
   - **Preflight** runs automatically on entry and can be refreshed:
     - Blockers (must-fix issues).
     - Warnings.
     - Recommendations.
     - Estimated rows and memory.
   - **Run** queues a generation run and navigates to the run detail page.
   - **Save as scenario** stores the current wizard config as a reusable scenario (with name, description, category).

The wizard maps the selected options into a flat config compatible with the backend `RunConfig` model. Advanced-only fields (simulation, benchmark, detailed load/export, runtime) remain available in **Advanced Configuration**.

---

## Advanced Configuration

Advanced Configuration is the expert workspace for the full nested config schema. It exposes all major sections from `RunConfig`:

- **Schema & Input** (generation)
- **Rules**
- **Generation**
- **ETL Realism**
- **Pipeline Simulation**
- **Privacy**
- **Contracts**
- **Exports**
- **Database Load**
- **Validation**
- **dbt / GE / Airflow**
- **Benchmark / Performance**
- **Raw Config & CLI preview**

Key capabilities:

- Load from query params:
  - `?scenario=<id>`: load an existing scenario and edit its config.
  - `?clone=<json>`: load a cloned run config (with optional masked fields).
- Edit nested blocks:
  - `pipeline_simulation` (enabled, density, pattern, replay mode, late arrivals).
  - `benchmark` (profile, scale preset, iterations).
  - `export` (format, write_manifest, integration flags and directories).
  - `load` (target, db_uri, chunk/batch sizing).
  - `privacy` (mode).
- **Preflight & Run** panel:
  - Run preflight on the current config.
  - View blockers and warnings.
  - Launch a run that uses the full config.
- **Scenario actions**:
  - If loaded from a scenario: **Update scenario** (with confirmation), or **Save as new scenario**.
  - From scratch: **Save as scenario**.
- **Import / Export**:
  - Export current config as JSON.
  - Import a JSON config file and merge it with sensible defaults.

Internally, advanced config edits a flat config object that is normalized by `RunConfig.from_flat_dict()` on the backend. This keeps legacy scenarios and new nested configs compatible.

## Preflight

Both the wizard and advanced config use the same `/api/preflight` endpoint.

Preflight checks:

- Validates pack, schema, and rules paths.
- Estimates row counts and memory usage.
- Highlights likely issues with load targets and integrations.
- Surfaces privacy or manifest-related warnings where applicable.

Preflight results:

- **Blockers**: prevent running from the wizard; in advanced, the Run button is disabled when blockers are present.
- **Warnings**: informational but do not block runs.
- **Recommendations**: tuning suggestions (e.g. lower scale, enable manifest, adjust batch size).

You can re-run preflight after changing config in either flow.

---

## Save, update, and save-as-new scenarios

Scenarios are reusable saved configurations. They work consistently across wizard and advanced:

- **Save as scenario (wizard)**:
  - Available from the Review step.
  - Captures the wizard’s flat config and metadata (name, description, category).
  - The scenario can be loaded later in wizard or advanced.
- **Save as scenario / Save as new (advanced)**:
  - Always available in the Preflight & Run panel.
  - When editing a loaded scenario:
    - **Update scenario** overwrites the existing scenario config and appends a new version in its history.
    - **Save as new scenario** keeps the original scenario and creates a new scenario derived from it.
- **Versioning**:
  - Scenario updates are versioned and can be inspected and diffed on the scenario detail page.

Imported configs and cloned run configs are treated like any other config when saving scenarios.

---

## Import / export config

Advanced Config supports direct config import/export:

- **Export**:
  - Downloads the current config as a JSON file.
  - The file can be checked into version control or used for automation and CI.
- **Import**:
  - Loads a JSON file and merges it with `DEFAULT_CONFIG`.
  - Fields not present in the file keep their defaults; new fields from the file override defaults.

This flow is useful for:

- Sharing configs between environments.
- Keeping “golden” scenario definitions under source control.
- Quickly iterating on configs outside the UI.
