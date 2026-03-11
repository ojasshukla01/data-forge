# Schema Studio

Schema Studio lets you design and manage custom relational schemas for use with Data Forge runs and scenarios.

## Overview

- **Route**: `/schema/studio`
- **API**: `/api/custom-schemas`
- **Storage**: JSON files in `custom_schemas/` (schema_&lt;id&gt;.json)

## Features

### Form mode

- **Tables**: Add, remove, rename tables
- **Columns**: Define columns with data type, nullable, primary key
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
- `POST /api/custom-schemas/validate` — validates structure and column generation rules
- Structural checks: unique table/column names, primary key refs, relationship refs, rule_type and params
- Error UX: highlights affected tables and columns in form mode

### Version history

- Each save creates a new version (up to 50)
- `GET /api/custom-schemas/{id}/versions` — list versions
- `GET /api/custom-schemas/{id}/diff?left=1&right=2` — diff with tables_added, tables_removed, tables_modified (columns_added/removed/modified)

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

Supported `rule_type`: `faker`, `uuid`, `sequence`, `range`, `static`, `weighted_choice`. See [generation-engine.md](generation-engine.md).

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
