# Custom Schema Studio

Custom Schema Studio is a first-class feature for designing and managing user-defined relational schemas inside Data Forge.

It complements domain packs by letting you create your own schema (tables, columns, relationships) and reuse it across scenarios and runs.

---

## Concepts

- **Custom schema** — a named, versioned schema definition (metadata + structure) stored under `custom_schemas/`.
- **Schema version** — each save that changes the schema body appends a new version; versions can be inspected and diffed.
- **Schema JSON** — the structural definition, compatible with `SchemaModel` in `src/data_forge/models/schema.py`.

Each custom schema record stores:

- `id` — e.g. `schema_ab12cd34ef56`.
- `name`, `description`, `tags`.
- `version` — latest version number.
- `created_at`, `updated_at`.
- `versions[]` — history of `{ version, schema, updated_at }`.

---

## Backend API

Router: `/api/custom-schemas` (see `src/data_forge/api/routers/custom_schemas.py`).

- `GET /api/custom-schemas`
  - Returns a list of `CustomSchemaSummary` objects (id, name, description, tags, version, timestamps).
- `POST /api/custom-schemas`
  - Creates a new schema.
  - Body:
    - `name` (string, required)
    - `description` (optional)
    - `tags` (optional string array)
    - `schema` (object, required) — `SchemaModel`-compatible JSON: `{ name, tables, relationships }`.
- `GET /api/custom-schemas/{id}`
  - Returns `CustomSchemaDetail` with the latest schema body.
- `PUT /api/custom-schemas/{id}`
  - Updates metadata and, if `schema` is present, appends a new version.
  - Body fields:
    - `name`, `description`, `tags` (optional metadata)
    - `schema` (optional) — new schema JSON.
- `DELETE /api/custom-schemas/{id}`
  - Deletes the schema record from the local registry.
- `GET /api/custom-schemas/{id}/versions`
  - Returns:
    - `schema_id`
    - `versions[]` (version + updated_at)
    - `current_version`.
- `GET /api/custom-schemas/{id}/versions/{version}`
  - Returns the schema body for a specific version.
- `GET /api/custom-schemas/{id}/diff?left=1&right=2`
  - Returns a simple structural diff:
    - `schema_id`, `left_version`, `right_version`, `changed[]` (top-level keys with different values).

All schema JSON is validated by `SchemaModel` before being saved.

---

## Storage

Custom schemas are stored in `custom_schemas/` at the repo root as JSON files:

- `custom_schemas/schema_<id>.json`

This keeps the feature **local-first** and friendly to source control.

Each file contains:

- Top-level metadata (`id`, `name`, `description`, `tags`, `created_at`, `updated_at`).
- `version` (latest).
- `versions[]` (history of schema bodies).

---

## Schema Studio UI

Route: `/schema/studio` (see `frontend/src/app/schema/studio/page.tsx`).

Main pieces:

- **Schema list** (left column)
  - Lists existing custom schemas with name, description, and latest version.
  - Empty state messaging when no schemas exist yet.
- **Schema editor** (main panel)
  - Metadata fields: name, tags, description.
  - JSON editor for the schema body:
    - Expected structure: `{ "name": "example", "tables": [...], "relationships": [...] }`.
    - Inline JSON validation on blur; errors are shown under the editor.
  - Actions:
    - **Save schema** — creates or updates a schema via the API.
    - Link to **Advanced config** for using the schema when configuring runs.
- **How it works** card
  - Short guide on defining, saving, and using schemas.

The Studio is intentionally form + JSON-based in this iteration, with a relational overview via the existing Schema Visualizer (`/schema`) for pack-based schemas.

---

## Using custom schemas with scenarios and runs

Current integration is lightweight and focuses on design and reuse:

- Use Schema Studio to define your schema structure.
- Export or store that JSON under `schemas/` if you want to load it via `schema_path`.
- In Advanced Config:
  - Use the **Schema & Input** section to point to a schema path or pack.
  - The UI links back to Schema Studio for richer editing.

Scenarios can include arbitrary metadata in `config`, including a `custom_schema_id` field if you choose to store it there. The run engine remains backward compatible and continues to rely on pack + schema ingest for physical generation.

---

## Limitations and future extensions

Current limitations:

- No drag-and-drop ERD editor; schema editing is JSON-based.
- Diff is top-level only; table/column-level diffing is not yet implemented.
- Preview data rows are not generated directly from custom schemas in this iteration.

Potential future work:

- Table/column editors and relationship pickers in the UI.
- ERD-style visual editing backed by `SchemaModel`.
- DDL export (SQL) per dialect.
- Preview generation using the existing engine and generators.
-- First-class integration of `custom_schema_id` into scenario configs and manifests.
