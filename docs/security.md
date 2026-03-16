# Security

Overview of Data Forge security practices and hardening measures.

## Input Validation

### Custom Schema API

- **Schema ID**: All `schema_id` path parameters are validated to prevent path traversal. Allowed format: `schema_<alphanumeric>` (max 64 chars). Slashes, backslashes, and `..` are rejected.
- **Payload validation**: Create and update requests use Pydantic models (`CustomSchemaCreate`, `CustomSchemaUpdate`). Schema bodies are validated via `SchemaModel` before storage.
- **Metadata sanitization**: `name`, `description`, and `tags` are trimmed and length-limited before persistence (name 500, description 2000, tags 50 chars each, max 50 tags).

### Path Safety

- **Project paths**: `config.ensure_path_allowed()` restricts resolved paths to project_root, schemas/, rules/, and output/. Paths outside these directories raise `SecurityError`.
- **Custom schema storage**: Schema files are stored under `custom_schemas/` and path resolution is validated so filenames cannot escape that directory.

## API Middleware

- **Request logging**: All requests are logged with method, path, status code, and duration.
- **Request size limit**: Requests with `Content-Length` > 2MB are rejected with `413 Payload Too Large` and a structured JSON body: `{ "detail": "Request body too large", "code": "payload_too_large", "max_size_bytes": 2097152 }`. Clients can use `code` for programmatic handling.
- **Rate limiting**: In-memory rate limiting per IP. GET/HEAD: 300/min, POST/PUT/PATCH/DELETE: 60/min. When exceeded, returns `429 Too Many Requests` with body `{ "detail": "Rate limit exceeded", "code": "rate_limit_exceeded", "retry_after_seconds": 60 }`. Resets on server restart.

## Schema Size Limits

Custom schemas are validated for size before save:
- **Schema body**: Maximum 512KB (JSON-serialized); requests exceeding this return `400` with `detail` describing the limit.
- **Structure**: Maximum 100 tables, 200 columns per table, 100 relationships.

Exceeding structure limits returns validation errors with structured messages. The schema body size check runs before structural validation on create and update.

## Schema Preview Safety

The `POST /api/schema/preview` endpoint (sample data for a schema) is non-persistent and does not run full generation. To avoid excessive load:

- **Tables**: Maximum 50 tables; schemas with more return `400` with detail `"Schema has too many tables for preview (max 50)"`.
- **Rows per table**: Request field `rows_per_table` is clamped to 1–20 (default 3). No separate response size limit; keep requests reasonable.

## CI and Secrets

- **Secrets**: Never commit `.env` or credentials. Use `.env.example` as a template.
- **CI**: GitHub Actions should not receive production credentials. Use repository secrets only for non-sensitive CI config.
- **Dependencies**: Run `uv pip compile` and `uv pip-audit` periodically to check for vulnerable packages.

## Privacy reporting

Generation runs produce a **privacy summary** and **privacy_audit** in the quality report (and in run lineage when applicable).

**What is measured:**

- **PII detection**: Column-level classification by name and generator hints (email, name, phone, address, credentials, financial, government_id, health, etc.). Categories and certainty (detected vs suspected) are in `quality_report.pii_detection`.
- **privacy_summary**: `total_sensitive_columns`, `by_category` (count per PII category), `high_risk_categories_detected` (credentials, government_id, financial).
- **privacy_audit**: `sensitive_columns_detected`, `redactions_applied` (when redaction is enabled), `warnings` (e.g. suspected/credentials/financial fields). No automatic blocking; `blocked` is reserved for future policy gating.

**What is not provided:**

- No formal privacy or anonymity guarantees. Synthetic data can still resemble real data; use redaction and access controls as appropriate.
- No automatic masking of values in exports; redaction applies to in-report samples only when `privacy_mode` is `warn` or `strict`.
- Detection is heuristic (column names and hints), not content-based.

See `pii/classifier.py` and `validators/quality.py` for implementation details.

## Storage

- Custom schemas are stored as JSON files in `custom_schemas/`. Ensure this directory has appropriate file permissions.
- SQLite backend (when used) stores run metadata and config; use file permissions to restrict access.
