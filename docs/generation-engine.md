# Generation Engine

Data Forge generates synthetic relational data from schema definitions. This document describes the engine, generation rules, and behavior.

## Overview

The engine (`src/data_forge/engine.py`) runs a pipeline:

1. Load schema and rules
2. Order tables by dependencies
3. Generate rows per table
4. Resolve foreign keys
5. Optional: drift, CDC, messiness, anomalies
6. Validate, export, quality report

## Generation Rules

When `rule_set.generation_rules` exist, they override `generator_hint` behavior for the specified table/column. Rules are applied per-table and per-column.

### Supported Rule Types

| Type | Params | Behavior |
|------|--------|----------|
| **faker** | `{"provider": "name"}` | Uses Faker provider (name, email, phone, company, etc.) |
| **uuid** | `{}` | Generates UUID v4 |
| **sequence** | `{"start": 1, "step": 1}` | Increments per row |
| **range** | `{"min": 0, "max": 100}` | Random value in [min, max] (int or float) |
| **static** | `{"value": "fixed"}` | Constant value for all rows |
| **weighted_choice** | `{"choices": ["a", "b"], "weights": [0.7, 0.3]}` | Pick from choices by weight; weights optional (uniform if omitted) |

**Optional param (any rule):** `null_probability` — float in [0, 1); probability of returning `null` instead of applying the rule.

### Faker Providers

Common providers: `name`, `email`, `phone`, `company`, `address`, `city`, `country`, `url`, `uuid`. Any Faker attribute can be used.

### Validation

- **Unknown rule_type** → error (engine returns failure)
- **Invalid params** (e.g. faker without provider, range min > max) → error

### Example (YAML rules)

```yaml
generation_rules:
  - table: users
    column: email
    rule_type: faker
    params:
      provider: email
  - table: users
    column: id
    rule_type: uuid
    params: {}
  - table: items
    column: seq_no
    rule_type: sequence
    params:
      start: 1
      step: 1
  - table: prices
    column: amount
    rule_type: range
    params:
      min: 0.0
      max: 999.99
  - table: users
    column: middle_name
    rule_type: faker
    params:
      provider: name
      null_probability: 0.3   # 30% chance of null
```

## Column Value Generation Order

1. If column is a FK → use parent_key_supplier
2. If RuleSet has `generation_rules` for (table, column) → apply rule
3. If ColumnDef has `generation_rule` (custom schema) → apply rule
4. Else use `generator_hint` (ColumnDef)
5. Else use `data_type` and constraints

## Column-Level Generation Rules (Custom Schemas)

Custom schemas (SchemaModel) can define `generation_rule` on each column. This overrides `generator_hint` and data-type inference.

Structure in JSON:

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

Validation: `rule_type` must be one of `faker`, `uuid`, `sequence`, `range`. Params are validated the same as RuleSet generation rules. Invalid column rules cause schema validation to fail.

## Distributions

`distribution_rules` are applied after value generation (e.g. categorical, skewed). They modify the generated value. `generation_rules` produce the base value.
