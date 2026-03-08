# Data Forge — Implementation Audit

**Audit date:** 2025-03-08  
**Repository:** data-forge (schema-aware synthetic data platform)  
**Scope:** Full local repository (source, config, tests, docs, domain packs)

---

# 1. Repository Overview

## Tree-level summary

```
data-forge/
├── src/data_forge/
│   ├── __init__.py              # version only
│   ├── config.py                # Settings, env presets, OutputFormat
│   ├── cli.py                   # Typer: generate, packs, validate
│   ├── engine.py                # Main pipeline
│   ├── models/
│   │   ├── schema.py            # ColumnDef, TableDef, SchemaModel, DataType
│   │   ├── rules.py             # BusinessRule, DistributionRule, RuleSet
│   │   └── generation.py        # GenerationRequest, TableSnapshot, Provenance
│   ├── schema_ingest/
│   │   ├── __init__.py          # load_schema, _parse_openapi
│   │   ├── sql_ddl.py           # parse_sql_ddl
│   │   └── json_schema.py       # parse_json_schema
│   ├── rule_engine/__init__.py  # load_rule_set, evaluate_rule
│   ├── generators/
│   │   ├── primitives.py        # PrimitiveGenerator
│   │   ├── table.py             # generate_table
│   │   ├── distributions.py     # apply_distribution
│   │   └── relationship_builder.py
│   ├── anomaly_injector/__init__.py
│   ├── validators/
│   │   ├── __init__.py          # re-exports + duplicate validate_* stubs
│   │   └── quality.py           # compute_quality_report, _ref_integrity
│   ├── exporters/__init__.py    # export_tables, export_table, CSV/JSON/Parquet/SQL
│   ├── domain_packs/__init__.py # list_packs, get_pack
│   └── ui/app.py                # Streamlit app
├── schemas/
│   ├── saas_billing.sql
│   └── ecommerce.sql
├── rules/
│   ├── saas_billing.yaml
│   └── ecommerce.yaml
├── tests/
│   ├── test_schema_ingest.py
│   └── test_engine.py
├── pyproject.toml
├── docker-compose.yml
├── README.md
└── .gitignore
```

## Detected stack and architecture

- **Runtime:** Python 3.10+
- **CLI:** Typer
- **UI:** Streamlit
- **Schema / validation:** Pydantic, Pydantic-Settings
- **Generation:** Faker, Mimesis, custom distributions
- **Export:** csv, json, pyarrow (Parquet)
- **Declared but unused in src:** FastAPI, uvicorn, sqlmodel, duckdb, polars, great-expectations, jinja2, httpx
- **Architecture:** Single pipeline in `engine.run_generation`; modular but mostly linear; no async, no streaming

---

# 2. Implemented Features Audit

## schema_ingest

| Aspect | Status | Evidence |
|--------|--------|----------|
| SQL DDL parsing | **Complete** | `schema_ingest/sql_ddl.py`: CREATE TABLE, PRIMARY KEY, inline REFERENCES, FOREIGN KEY (col) REFERENCES |
| JSON Schema parsing | **Complete** | `json_schema.py`: tables, definitions, single-properties formats |
| OpenAPI parsing | **Partial** | `_parse_openapi`: extracts components/schemas as tables; **no relationships**, no paths/operations |
| Pydantic ingest | **Missing** | `config.SchemaSource.PYDANTIC` exists; no Pydantic schema loader implemented |
| YAML schema load | **Partial** | `load_schema` accepts .yaml/.yml and passes to JSON Schema / OpenAPI path; works if structure matches |
| load_schema dispatch | **Complete** | `schema_ingest/__init__.py`: infers from .sql, .json, .yaml/.yml |

**Quality notes:**
- SQL parser: regex-based; no sqlparse/sqlglot; may break on complex DDL (CHECK, GENERATED, etc.)
- `_normalize_sql_type` strips constraint keywords with `re.sub(r"\b" + kw + r"\b.*", ...)` — can truncate type if keyword appears in type name
- JSON Schema: no `$ref` resolution; nested objects flattened as JSON type

---

## rule_engine

| Aspect | Status | Evidence |
|--------|--------|----------|
| Load YAML rules | **Complete** | `load_rule_set(path)` in `rule_engine/__init__.py` |
| Business rules (ORDER, RANGE, SUM, EQUALITY) | **Complete** | `evaluate_rule`, `_eval_order`, `_eval_range`, `_eval_sum`, `_eval_equality` |
| Distribution rules in YAML | **Complete** | Loaded into RuleSet; applied in `generate_table` via `apply_distribution` |
| Rule enforcement during generation | **Missing** | `evaluate_rule` is **never called** from `engine` or `table`. Rules are loaded but not enforced. |
| REFERENCE, UNIQUENESS, ENUM, PATTERN, CUSTOM | **Stubbed** | RuleType exists; no implementation in `evaluate_rule` |

**Quality notes:**
- `ecommerce.yaml` has `refund_after_order` with `created_at >= created_at` (self-referential, always passes)
- `line_item_amount` SUM rule expects `context["_children"]`; context is never populated during generation

---

## generators

| Aspect | Status | Evidence |
|--------|--------|----------|
| PrimitiveGenerator | **Complete** | `primitives.py`: Faker + Mimesis; DataType + generator_hint; seeded |
| generate_table | **Complete** | `table.py`: per-column generation, distribution rules, PK uniqueness |
| Distribution application | **Complete** | `distributions.py`: uniform, normal, skewed, categorical, seasonal, long_tail |
| RelationshipBuilder (FK assignment) | **Complete** | `relationship_builder.py`: assigns parent PKs to child FK columns |
| parent_key_supplier | **Unused** | Passed as `None` from engine; FK resolution done post-hoc by RelationshipBuilder |
| Time-aware / event simulation | **Missing** | No lifecycle, CDC, or event streams |
| row_estimate | **Unused** | `TableDef.row_estimate` exists; engine uses hardcoded table-name heuristics |

**Quality notes:**
- Row counts: `orders/invoices/subscriptions` use `max(scale//2, scale*2)` → effectively `scale*2` for scale≥4
- `hash(table.name)` in PK generation is process-dependent (Python hash randomization); may affect cross-run reproducibility on some configs

---

## relationship / FK handling

| Aspect | Status | Evidence |
|--------|--------|----------|
| Dependency-ordered generation | **Complete** | `SchemaModel.dependency_order()` topological sort |
| FK assignment after generation | **Complete** | `RelationshipBuilder.assign_foreign_keys`; `i % len(parent_pks)` for many-to-one |
| Multi-column FK | **Partial** | Only first column of `to_columns`/`from_columns` used |
| Composite PK | **Partial** | Supported in schema; RelationshipBuilder only uses `to_columns[0]` |
| Optional (nullable) FK | **Partial** | Model supports it; generator always assigns a parent PK |

---

## anomaly_injector

| Aspect | Status | Evidence |
|--------|--------|----------|
| NULL_FIELD | **Complete** | Sets random column to None |
| EMPTY_STRING | **Complete** | Sets random string column to "" |
| INVALID_ENUM | **Complete** | Sets column to "__INVALID__" |
| MALFORMED_STRING | **Complete** | Sets string column to `\x00\xff\xfe broken \u0000` |
| DUPLICATE_ROW | **Complete** | Appends copy of random row |
| OUT_OF_RANGE, NEGATIVE_VALUE, WRONG_TYPE | **Stubbed** | AnomalyType defines them; no implementation |
| Bug: no string columns | **Risky** | `rng.choice([...])` on empty list raises when row has no string columns for EMPTY_STRING/MALFORMED_STRING |

---

## validators / quality report

| Aspect | Status | Evidence |
|--------|--------|----------|
| compute_quality_report | **Complete** | `quality.py`: row counts, null ratios, ref integrity |
| validate_referential_integrity | **Complete** | Used inside compute_quality_report |
| validate_schema_compliance | **Complete** | In `quality.py` and duplicated in `validators/__init__.py`; **never called** from pipeline |
| Statistical similarity score | **Missing** | Not implemented |
| Privacy leakage score | **Missing** | Not implemented |
| Test coverage score | **Missing** | Not implemented |

---

## exporters

| Aspect | Status | Evidence |
|--------|--------|----------|
| CSV | **Complete** | `_export_csv` |
| JSON | **Complete** | `_export_json` |
| JSONL / NDJSON | **Complete** | `_export_jsonl` |
| Parquet | **Complete** | `_export_parquet`; falls back to string for mixed types |
| SQL inserts | **Complete** | `_export_sql`; dialect param unused (always generic) |
| Avro | **Missing** | Not implemented |
| REST mock payloads | **Missing** | Not implemented |
| Kafka / NDJSON streams | **Missing** | Not implemented |

**Quality notes:**
- SQL export: single dialect; no MySQL backtick, no Oracle; table/column names not quoted

---

## domain_packs

| Aspect | Status | Evidence |
|--------|--------|----------|
| list_packs | **Complete** | Hardcoded list of saas_billing, ecommerce |
| get_pack | **Complete** | Loads schema + rules from `schemas/{id}.sql`, `rules/{id}.yaml` |
| SaaS schema + rules | **Complete** | `schemas/saas_billing.sql`, `rules/saas_billing.yaml` |
| E-commerce schema + rules | **Complete** | `schemas/ecommerce.sql`, `rules/ecommerce.yaml` |
| Pack discovery / registry | **Missing** | Packs hardcoded; no filesystem scan or plugin system |

---

## CLI

| Aspect | Status | Evidence |
|--------|--------|----------|
| data-forge --version | **Complete** | `cli.py` callback |
| data-forge generate | **Complete** | --pack, -s, -r, --seed, --scale, --anomalies, -o, -f, --locale |
| data-forge packs | **Complete** | Lists domain packs |
| data-forge validate | **Partial** | Loads schema only; `--data` option accepted but **never used** |
| Environment preset from CLI | **Missing** | request.environment not overridable via CLI |

---

## UI

| Aspect | Status | Evidence |
|--------|--------|----------|
| Domain pack generation | **Complete** | Tab "Domain pack": pack select, seed, scale, anomalies, format |
| Custom schema upload | **Complete** | Tab "Custom schema": file_uploader for .sql/.json, .yaml |
| Download button | **Stubbed** | Sends "See output/ directory" text file, not actual ZIP of output |

---

## config / settings

| Aspect | Status | Evidence |
|--------|--------|----------|
| Settings model | **Complete** | `config.py`: pydantic-settings, DATA_FORGE_ prefix |
| Environment preset enum | **Complete** | UNIT_TEST, INTEGRATION_TEST, etc. |
| Actual usage | **Missing** | `Settings` imported in engine + cli but **never instantiated or used** |
| request.environment | **Unused** | Passed in GenerationRequest; engine ignores it |

---

## Docker / local environment

| Aspect | Status | Evidence |
|--------|--------|----------|
| Postgres service | **Complete** | `docker-compose.yml`: postgres:16-alpine |
| Load test / import scripts | **Missing** | No script to load SQL output into Postgres |
| Redpanda | **Commented** | Present but disabled |

---

## tests

| Aspect | Status | Evidence |
|--------|--------|----------|
| test_parse_sql_ddl_simple | **Complete** | `tests/test_schema_ingest.py` |
| test_parse_sql_ddl_with_fk | **Complete** | |
| test_load_schema_saas_billing | **Complete** | |
| test_run_generation_saas_pack | **Complete** | `tests/test_engine.py` |
| test_export_result | **Complete** | |
| Coverage | **Low** | No tests for rule_engine, anomaly_injector, exporters, distributions, validators, CLI, UI |
| Property-based | **Missing** | Hypothesis in dev deps but not used |

---

## docs / developer experience

| Aspect | Status | Evidence |
|--------|--------|----------|
| README | **Complete** | Features, quick start, project layout, roadmap |
| API docs | **Missing** | No Sphinx/MkDocs |
| CONTRIBUTING | **Missing** | |
| Changelog | **Missing** | |
| pre-commit | **Missing** | In dev deps; no .pre-commit-config.yaml |

---

# 3. Gap Analysis

| Gap | Status | Notes |
|-----|--------|-------|
| ETL/ELT realism | **Missing** | No bronze/silver/gold layers, no incremental loads |
| CDC / incremental loads | **Missing** | No change-data-capture or delta simulation |
| Batch vs stream simulation | **Missing** | All batch; no event stream mode |
| Bronze/silver/gold outputs | **Missing** | Single export format per run |
| Schema evolution / drift | **Missing** | No versioning or drift simulation |
| Source-system messiness | **Partial** | Anomaly injector adds some; no configurable "ugliness" profiles |
| Privacy / PII handling | **Missing** | No PII detection, masking, or synthetic-only guarantee |
| Data leakage risk | **Unaddressed** | Faker/Mimesis produce random data; no learning from real data, so no memorization risk. But no explicit guarantee documented. |
| Exception handling | **Weak** | Broad `except Exception` in engine; most modules raise through |
| Observability / logging | **Missing** | No structlog/logging; no metrics |
| Reproducibility | **Partial** | Seed used; Python hash() may vary across processes |
| Performance / scaling | **Untested** | No benchmarks; in-memory only; scale 50k+ unverified |
| E2E testing | **Missing** | No test that runs CLI or UI |
| Property-based testing | **Missing** | Hypothesis unused |
| Golden dataset / regression | **Missing** | No golden fixtures or checksum tests |
| API contract validation | **Missing** | No OpenAPI request/response generation or validation |
| Extensibility for new packs | **Partial** | Must edit `list_packs` + add files; no plugin/scan |

---

# 4. Security and Privacy Review

| Item | Finding |
|------|---------|
| YAML loading | **Safe** | `yaml.safe_load` used in `rule_engine.load_rule_set` and `schema_ingest.load_schema` |
| Path traversal | **Risk** | `load_schema(path)`, `load_rule_set(path)` accept user-controlled paths; no `path.resolve().relative_to(base)` check. Caller can read arbitrary files if path is user-supplied. |
| File handling | **Risk** | `path.read_text()`, `path.write_text()`; output_dir from CLI can be anywhere. No validation of output path. |
| Arbitrary code execution | **Low** | No `eval`, `exec`, or dynamic imports from user input. Rule expressions are parsed as simple strings (field names, ops). |
| Logging of sensitive values | **N/A** | No logging of row data. |
| Secrets handling | **Low** | No secrets in code. Docker Compose uses plain postgres password (local dev only). |
| Data leakage guarantee | **Cannot guarantee** | No learning-from-real-data path, so no memorization. README claims "privacy-safe" but there is no formal check or documentation of what that means. |
| Dependency risks | **Moderate** | Many heavy deps (great-expectations, sdv optional) declared; CVEs should be monitored. |

**Path traversal mitigation suggestion:** Resolve and validate paths against a project root or explicitly allowed directories before read/write.

---

# 5. Test Coverage Review

| Test | What it validates |
|------|-------------------|
| test_parse_sql_ddl_simple | SQL parser produces one table, correct types, PK |
| test_parse_sql_ddl_with_fk | Inline REFERENCES creates relationship |
| test_load_schema_saas_billing | load_schema from file, dependency order |
| test_run_generation_saas_pack | run_generation succeeds, quality_report present, seed reproducibility of row counts |
| test_export_result | export_result writes CSV files |

**Critical paths untested:**
- `rule_engine.evaluate_rule` (never called, but unit-testable)
- `anomaly_injector` (including bug with no string columns)
- `exporters` for JSON, Parquet, SQL
- `relationship_builder` with composite FK
- CLI `generate` and `validate` commands
- Streamlit UI
- JSON Schema and OpenAPI load paths
- Error paths: invalid schema, missing files, malformed YAML

**Conclusion:** Coverage is minimal. Critical pipeline and edge cases are not exercised. Not sufficient for confident refactoring or regression prevention.

---

# 6. Priority Roadmap

## P0 — Most urgent

| Title | Why | Files / modules |
|-------|-----|------------------|
| Wire rule evaluation into generation | Rules are loaded but never enforced; core value prop broken | `engine.py`, `generators/table.py`, `rule_engine` |
| Fix anomaly injector crash on non-string rows | `rng.choice([])` when row has no string columns | `anomaly_injector/__init__.py` |
| Use Settings and request.environment | Config exists but is dead code; env presets unused | `engine.py`, `config.py`, `cli.py` |
| Validate --data in CLI | Option advertised but does nothing | `cli.py` |

## P1 — Important next

| Title | Why | Files / modules |
|-------|-----|------------------|
| Add business-rule compliance to quality report | Users need to know if rules pass | `validators/quality.py`, `engine.py` |
| Add tests for rule_engine, anomaly_injector, exporters | Critical paths uncovered | `tests/` |
| Implement invoice total = sum(line_items) | Key business rule; requires parent-child context | `engine.py`, `generators/table.py`, rule YAML |
| Path validation for load_schema / output | Security; avoid arbitrary file read/write | `schema_ingest/__init__.py`, `cli.py` |

## P2 — Later enhancements

| Title | Why | Files / modules |
|-------|-----|------------------|
| Provenance / "explain why" | Differentiator; `with_provenance` already in model | `engine.py`, `generators/table.py`, `models/generation.py` |
| OpenAPI request/response generation | Phase 2 goal | New module |
| Event stream simulator | Phase 2 goal | New module |
| Remove or use unused deps | FastAPI, duckdb, polars, great-expectations, sqlmodel | `pyproject.toml` |

---

# 7. Concrete Engineering Recommendations

1. **Instantiate and use Settings:** Create `settings = Settings()` in engine or a factory; pass output_dir, anomaly_ratio, locale from it. Override from CLI when provided.

2. **Call evaluate_rule in a validation pass:** After generation, iterate rows and call `evaluate_rule` for each applicable business rule; collect failures and add to quality_report.

3. **Guard anomaly injection:** Before `rng.choice([k for k,v in row.items() if isinstance(v, str)])`, check list non-empty; otherwise skip EMPTY_STRING/MALFORMED_STRING or fall back to NULL_FIELD.

4. **Use table.row_estimate when present:** In engine row-count logic, prefer `table.row_estimate` over hardcoded table-name map.

5. **Deduplicate validators:** Remove `validate_schema_compliance` and `validate_referential_integrity` from `validators/__init__.py`; import from `quality` only. Optionally call schema compliance in quality report.

6. **Add golden test:** Generate with fixed seed, checksum output (e.g. row counts + first row of each table); assert in CI.

7. **Document privacy stance:** Add a short "Privacy" section to README: no learning from real data; output is purely synthetic from Faker/Mimesis + schema; no guarantee if used with future learning features.

8. **Fix ecommerce refund_after_order rule:** Use a meaningful expression or remove if unimplementable without cross-table context.

---

# 8. Suggested Next Implementation Milestone

**Wire rule evaluation into generation and quality report**

- Implement a validation pass that runs `evaluate_rule` for each business rule on each relevant row.
- Add `rule_violations` to quality_report (count and sample).
- For SUM rules (e.g. invoice total = sum(line_items)), either:
  - (a) Populate `context["_children"]` when generating parent rows from child aggregates, or
  - (b) Add a post-generation pass that recomputes parent totals from child rows and fixes them.
- Fix the anomaly injector crash.
- Add 2–3 tests for rule evaluation and anomaly injection.

This delivers the promised "business-valid" behavior and closes the largest gap between README and implementation.

---

# Appendix A: Machine-readable checklist

```json
{
  "implemented": [
    "schema_ingest.sql_ddl",
    "schema_ingest.json_schema",
    "schema_ingest.openapi_partial",
    "rule_engine.load_rules",
    "rule_engine.evaluate_rule",
    "generators.primitives",
    "generators.table",
    "generators.distributions",
    "generators.relationship_builder",
    "anomaly_injector.basic",
    "validators.quality_report",
    "exporters.csv_json_parquet_sql",
    "domain_packs.saas_ecommerce",
    "cli.generate_packs_validate",
    "ui.streamlit",
    "config.settings_model",
    "docker_compose.postgres",
    "tests.5_unit"
  ],
  "partial": [
    "rule_engine.rules_not_enforced",
    "schema_ingest.openapi_no_relationships",
    "validators.schema_compliance_never_called",
    "cli.validate_data_dir_unused",
    "config.settings_unused",
    "provenance.stubbed",
    "row_estimate.unused"
  ],
  "missing": [
    "pydantic_schema_ingest",
    "business_rule_enforcement",
    "cdc_incremental",
    "event_stream_simulation",
    "privacy_pii_handling",
    "api_contract_generation",
    "golden_dataset_testing",
    "e2e_tests",
    "property_based_tests",
    "logging_observability",
    "avro_kafka_export"
  ],
  "risks": [
    "anomaly_injector_crash_no_string_columns",
    "path_traversal_user_paths",
    "hash_reproducibility",
    "unused_heavy_dependencies"
  ],
  "next_best_milestone": "Wire rule evaluation into generation and quality report; fix anomaly injector crash"
}
```

---

# Appendix B: GitHub Issues Backlog

| Title | Priority | Category | Description | Affected files | Effort |
|-------|----------|----------|-------------|----------------|--------|
| Rules loaded but never enforced during generation | P0 | Bug | evaluate_rule exists but is never called; business rules have no effect | engine.py, table.py | M |
| Anomaly injector crashes when row has no string columns | P0 | Bug | rng.choice([]) on EMPTY_STRING/MALFORMED_STRING | anomaly_injector/__init__.py | S |
| Settings and environment preset never used | P0 | Tech debt | Config is dead code | engine.py, cli.py, config.py | S |
| Validate --data does nothing | P0 | Bug | CLI accepts --data for validate but ignores it | cli.py | S |
| Add rule compliance to quality report | P1 | Feature | Run evaluate_rule and report violations | validators/quality.py, engine.py | M |
| Tests for rule_engine, anomaly_injector, exporters | P1 | Test | No unit tests for these modules | tests/ | M |
| Implement invoice total = sum(line_items) | P1 | Feature | Parent-child aggregation for SUM rules | engine.py, table.py | M |
| Path validation for schema/rules/output | P1 | Security | Prevent path traversal | schema_ingest, cli | S |
| Use table.row_estimate for row counts | P1 | Enhancement | Prefer schema hint over heuristics | engine.py | S |
| Provenance / explain mode | P2 | Feature | Populate TableSnapshot.provenance when with_provenance=True | engine.py, table.py | L |
| OpenAPI request/response generation | P2 | Feature | Generate API payloads from OpenAPI | New module | L |
| Event stream simulator | P2 | Feature | CDC / event streams | New module | L |
| E2E test for CLI generate | P2 | Test | Subprocess test of data-forge generate | tests/ | M |
| Property-based tests with Hypothesis | P2 | Test | Invariants for schema parse, generation | tests/ | M |
| Remove or integrate unused dependencies | P2 | Tech debt | FastAPI, duckdb, polars, great-expectations | pyproject.toml | S |

---

# Appendix C: Brutally Honest Verdict

Data Forge is a solid MVP scaffold with a clear architecture and working end-to-end path for schema → generation → export. The schema ingest, FK resolution, and export stack are implemented and tested enough to be useful.

The main problem: **the rule engine is ornamental**. Rules are loaded and parsed, but `evaluate_rule` is never called. Distribution rules work; business rules do not. The README promises "business-valid" data, but invoice totals are not constrained to equal the sum of line items, and date ordering rules are not enforced. That gap is the biggest disconnect between marketing and implementation.

Secondary issues: Settings and environment presets are unused; the validate command's `--data` option does nothing; provenance is stubbed; and the anomaly injector can crash on tables without string columns. Test coverage is thin and skips most modules. Several declared dependencies (FastAPI, DuckDB, Polars, Great Expectations) are unused.

The codebase is readable and modular. With a focused effort to wire rule evaluation, fix the injector, and add tests, it would deserve the "business-valid" claim. Until then, it is a good schema-aware fake-data generator with optional anomalies, but not yet a rule-respecting synthetic data platform.
