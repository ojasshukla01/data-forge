# Schema Studio

Schema Studio lets you design and manage custom relational schemas for use with Data Forge runs and scenarios.

## Overview

- **Route**: `/schema/studio`
- **API**: `/api/custom-schemas` — full endpoint list (validate, CRUD, versions, diff, restore) is in [api-reference.md](api-reference.md).
- **Storage**: JSON files in `custom_schemas/` at the repo root: `custom_schemas/schema_<id>.json` (metadata, version, versions history).

## How it works (workflow)

1. **Choose or create a schema** — You must select an existing schema from the sidebar or click "New schema" before adding tables. The Add table button and editor tabs are only enabled when a schema is open.

2. **Add tables and columns** — Use the Tables tab to add tables. Switch to the Columns tab to add columns to each table: data type, nullable, primary key, optional generation rules (faker, sequence, uuid, etc.).

3. **Define relationships** — Use the Relationships tab to add foreign keys (from_table/from_columns → to_table/to_columns).

4. **Validate and save** — Click Validate to check structure and rules. Fix any errors, then Save. Versions are tracked.

5. **Use in runs** — Use with Create wizard (custom schema source) or Advanced config (custom schema dropdown). Your saved schema appears in the dropdown.

## UI layout

- **Sidebar (left):** Custom schemas list (one scrollable list). Below it, a fixed "How it works" section with step-by-step instructions.
- **Editor (right):** Form mode and JSON mode tabs. Form mode has Tables, Columns, Relationships tabs. When no schema is selected, a clear message instructs you to choose or create a schema first.

## Features

### Form mode

- **Tables**: Add, remove, rename tables; unique constraints (one per line, comma-separated columns)
- **Columns**: Define columns with data type, nullable, primary key, check constraint, generation rules
- **Relationships**: Define foreign keys (from_table/from_columns → to_table/to_columns)
- Data types: string, integer, bigint, float, date, datetime, uuid, email, etc.

### JSON mode

- Edit the raw schema JSON for advanced control
- Supports metadata: name, description, tags, unique_constraints, check, display_name

### Sample preview

- Generate sample rows without saving or running a full generation
- Preview by data type and by column `generation_rule` (faker, uuid, sequence, range)
- Select tables to view, set rows per table (1–20), refresh preview on demand
- Shows row count per table

### Validation

- **Validate** button validates schema structure before save
- `POST /api/custom-schemas/validate` — returns `{ valid, errors, warnings }`
- Structural checks: unique table/column names, primary key refs, relationship refs, rule_type and params
- **Warnings** (non-blocking): e.g. empty table, self-referential relationship
- Error UX: highlights affected tables and columns in form mode

### Version history and restore

- Each save creates a new version (up to 50)
- **Version history** (expandable card in the editor): list versions, compare any two with diff (tables_added/removed/modified, columns_added/removed/modified), and **Restore** a version as a new revision (non-destructive). Restore creates a new version from the selected one; use it to roll back without losing history.
- `GET /api/custom-schemas/{id}/versions` — list versions
- `GET /api/custom-schemas/{id}/diff?left=1&right=2` — diff
- `POST /api/custom-schemas/{id}/versions/{version}/restore` — restore that version as a new revision

### Duplicate schema

- Use **Duplicate** (when a schema is open) to create a copy with a new name and id. Useful for variants or templates.

### Generation rules (column-level)

Columns can define `generation_rule` to override default value generation:

```json
{
  "name": "id",
  "data_type": "integer",
  "generation_rule": {
    "rule_type": "sequence",
    "params": { "start": 1, "step": 1 }
  }
}
```

Supported `rule_type`: `faker`, `uuid`, `sequence`, `range`, `static`, `weighted_choice`. Optional param `null_probability` (0–1) for any rule returns `null` with that probability. See [generation-engine.md](generation-engine.md).

## Loading and error states

- **No schema selected:** The editor shows a clear message to choose a schema from the sidebar or click "New schema". Form and JSON tabs are disabled until a schema is selected or created.
- **Validation:** After clicking Validate, errors (blocking) and warnings (advisory) appear in a summary box; errors are listed so you can fix them before save.
- **Save/restore:** Saving shows a brief loading state; restore shows which version is being restored until the new revision is loaded.

## Integration

- **Advanced Config**: Schema & Input section has a "Custom schema" dropdown
- **Wizard**: "Choose Schema Source" — Domain Pack or Custom Schema; select from Schema Studio list; payload includes `custom_schema_id`
- **Generate API**: Accepts `custom_schema_id`; loads schema from Custom Schema Studio and runs generation
- **Preflight**: Validates `custom_schema_id` exists and estimates rows from schema tables
- **Run provenance**: Completed runs record custom_schema_id and custom_schema_version in manifest, lineage, and run detail; the Run detail page and Lineage/Manifest cards show custom schema provenance when used

## Schema structure

```json
{
  "name": "my_schema",
  "description": "Optional description",
  "tables": [
    {
      "name": "users",
      "columns": [
        {"name": "id", "data_type": "integer", "primary_key": true},
        {"name": "email", "data_type": "email", "nullable": false}
      ],
      "primary_key": ["id"],
      "unique_constraints": [["email"]]
    }
  ],
  "relationships": [
    {
      "name": "orders_to_users",
      "from_table": "orders",
      "from_columns": ["user_id"],
      "to_table": "users",
      "to_columns": ["id"],
      "cardinality": "many-to-one"
    }
  ]
}
```
