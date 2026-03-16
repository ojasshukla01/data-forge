"""Tests for Privacy + API Contract Validation Pack."""

from pathlib import Path

from data_forge.models.schema import SchemaModel, TableDef, ColumnDef, DataType
from data_forge.models.rules import RuleSet, BusinessRule, RuleType
from data_forge.pii.classifier import classify_schema
from data_forge.pii.redaction import redact_value, RedactionConfig
from data_forge.validators.quality import compute_quality_report
from data_forge.contracts.fixtures import generate_contract_fixtures
from data_forge.contracts.validate import validate_contract_fixtures


def _run_cli(args: list[str]):
    import subprocess
    r = subprocess.run(
        ["python", "-m", "data_forge.cli"] + args,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    return r


# --- PII detection ---
def test_detect_email_phone_dob():
    schema = SchemaModel(
        tables=[
            TableDef(name="users", columns=[
                ColumnDef(name="id", data_type=DataType.INTEGER),
                ColumnDef(name="email", data_type=DataType.STRING),
                ColumnDef(name="phone", data_type=DataType.STRING),
                ColumnDef(name="dob", data_type=DataType.DATE),
            ])
        ]
    )
    r = classify_schema(schema)
    assert r.pii_detection["users"]["email"] == "email"
    assert r.pii_detection["users"]["phone"] == "phone"
    assert r.pii_detection["users"]["dob"] == "date_of_birth"
    assert r.pii_detection["users"]["id"] == "unclassified"


def test_detect_password_credentials():
    schema = SchemaModel(
        tables=[
            TableDef(name="auth", columns=[
                ColumnDef(name="api_token", data_type=DataType.STRING),
                ColumnDef(name="password", data_type=DataType.STRING),
            ])
        ]
    )
    r = classify_schema(schema)
    assert r.pii_detection["auth"]["api_token"] == "credentials"
    assert r.pii_detection["auth"]["password"] == "credentials"
    assert any("credentials" in w for w in r.warnings)


def test_manual_override(tmp_path):
    override = tmp_path / "pii_overrides.yaml"
    override.write_text("""
pii_overrides:
  users:
    internal_id: government_id
""")
    schema = SchemaModel(
        tables=[TableDef(name="users", columns=[
            ColumnDef(name="internal_id", data_type=DataType.STRING),
        ])]
    )
    r = classify_schema(schema, overrides_path=override)
    assert r.pii_detection["users"]["internal_id"] == "government_id"


def test_unclassified_vs_detected():
    schema = SchemaModel(
        tables=[TableDef(name="t", columns=[
            ColumnDef(name="email", data_type=DataType.STRING),
            ColumnDef(name="other", data_type=DataType.STRING),
        ])]
    )
    r = classify_schema(schema)
    assert r.certainty["t"]["email"] == "detected"
    assert r.certainty["t"]["other"] == "unclassified"


# --- Privacy / redaction ---
def test_strict_mode_redacts_samples():
    schema = SchemaModel(
        tables=[TableDef(name="users", columns=[
            ColumnDef(name="id", data_type=DataType.INTEGER),
            ColumnDef(name="email", data_type=DataType.STRING),
        ])]
    )
    rule_set = RuleSet(
        name="r",
        business_rules=[
            BusinessRule(
                name="fail",
                rule_type=RuleType.RANGE,
                table="users",
                fields=["id"],
                params={"min": 100, "max": 200},
            ),
        ],
    )
    pii = {"users": {"email": "email", "id": "unclassified"}}
    cfg = RedactionConfig(enabled=True)
    report = compute_quality_report(
        schema,
        {"users": [{"id": 1, "email": "secret@test.com"}]},
        rule_set=rule_set,
        pii_detection=pii,
        privacy_mode="strict",
        redaction_config=cfg,
    )
    samples = report.get("rule_violations", {}).get("samples", [])
    for s in samples:
        if "row" in s and "email" in s["row"]:
            assert s["row"]["email"] == "***@***"


def test_credentials_masked():
    cfg = RedactionConfig(enabled=True)
    out = redact_value("mypassword123", "credentials", cfg)
    assert out == "***SECRET***"


def test_privacy_audit_in_report():
    schema = SchemaModel(
        tables=[TableDef(name="users", columns=[
            ColumnDef(name="email", data_type=DataType.STRING),
        ])]
    )
    pii = {"users": {"email": "email"}}
    report = compute_quality_report(
        schema,
        {"users": [{"email": "x@y.com"}]},
        pii_detection=pii,
        privacy_mode="warn",
        redaction_config=RedactionConfig(enabled=True),
        privacy_warnings=["Detected email field"],
    )
    pa = report.get("privacy_audit", {})
    assert pa["mode"] == "warn"
    assert pa["sensitive_columns_detected"] >= 1
    assert "warnings" in pa
    assert pa["blocked"] is False
    ps = report.get("privacy_scorecard", {})
    assert "risk_score" in ps
    assert ps.get("risk_level") in {"low", "medium", "high"}
    pol = report.get("privacy_policy", {})
    assert pol.get("enforced") is False
    assert "would_block" in pol


def test_sensitive_not_raw_when_redaction_enabled():
    schema = SchemaModel(
        tables=[TableDef(name="users", columns=[
            ColumnDef(name="id", data_type=DataType.INTEGER),
            ColumnDef(name="email", data_type=DataType.STRING),
        ])]
    )
    rule_set = RuleSet(
        name="r",
        business_rules=[
            BusinessRule(
                name="always_fail",
                rule_type=RuleType.ORDER,
                table="users",
                expression="id <= 0",
            ),
        ],
    )
    pii = {"users": {"email": "email"}}
    report = compute_quality_report(
        schema,
        {"users": [{"id": 1, "email": "sensitive@real.com"}]},
        rule_set=rule_set,
        pii_detection=pii,
        privacy_mode="strict",
        redaction_config=RedactionConfig(enabled=True),
    )
    rv = report.get("rule_violations", {})
    for v in rv.get("samples", []) + list(rv.get("by_rule", {}).keys()):
        if isinstance(v, dict) and "row" in v:
            assert v["row"].get("email") != "sensitive@real.com"


def test_privacy_policy_would_block_in_strict_for_high_risk():
    schema = SchemaModel(
        tables=[TableDef(name="auth", columns=[ColumnDef(name="api_token", data_type=DataType.STRING)])]
    )
    pii = {"auth": {"api_token": "credentials"}}
    report = compute_quality_report(
        schema,
        {"auth": [{"api_token": "secret"}]},
        pii_detection=pii,
        privacy_mode="strict",
        redaction_config=RedactionConfig(enabled=True),
    )
    policy = report.get("privacy_policy", {})
    assert policy.get("would_block") is False
    assert policy.get("policy_decision") == "allow"


def test_privacy_policy_blocks_when_enforced_and_high_risk_enabled():
    schema = SchemaModel(
        tables=[TableDef(name="auth", columns=[ColumnDef(name="api_token", data_type=DataType.STRING)])]
    )
    pii = {"auth": {"api_token": "credentials"}}
    report = compute_quality_report(
        schema,
        {"auth": [{"api_token": "secret"}]},
        pii_detection=pii,
        privacy_mode="strict",
        redaction_config=RedactionConfig(enabled=True),
        privacy_policy_mode="enforce",
        privacy_policy_fail_on_high_risk=True,
    )
    policy = report.get("privacy_policy", {})
    assert policy.get("would_block") is True
    assert policy.get("policy_decision") == "block"
    assert any(
        str(v).startswith("high_risk_categories_present")
        for v in policy.get("violations", [])
    )


def test_privacy_policy_threshold_warning_in_advisory_mode():
    schema = SchemaModel(
        tables=[TableDef(name="users", columns=[ColumnDef(name="email", data_type=DataType.STRING)])]
    )
    pii = {"users": {"email": "email"}}
    report = compute_quality_report(
        schema,
        {"users": [{"email": "x@y.com"}]},
        pii_detection=pii,
        privacy_mode="warn",
        redaction_config=RedactionConfig(enabled=True),
        privacy_policy_mode="advisory",
        privacy_policy_max_risk_score=1,
    )
    policy = report.get("privacy_policy", {})
    assert policy.get("would_block") is True
    assert policy.get("policy_decision") == "warn"
    assert any("risk_score_exceeds_threshold" in v for v in policy.get("violations", []))


def test_privacy_policy_sensitive_column_threshold_enforced():
    schema = SchemaModel(
        tables=[
            TableDef(
                name="users",
                columns=[
                    ColumnDef(name="email", data_type=DataType.STRING),
                    ColumnDef(name="phone", data_type=DataType.STRING),
                ],
            )
        ]
    )
    pii = {"users": {"email": "email", "phone": "phone"}}
    report = compute_quality_report(
        schema,
        {"users": [{"email": "x@y.com", "phone": "123"}]},
        pii_detection=pii,
        privacy_mode="warn",
        redaction_config=RedactionConfig(enabled=True),
        privacy_policy_mode="enforce",
        privacy_policy_max_sensitive_columns=1,
    )
    policy = report.get("privacy_policy", {})
    assert policy.get("policy_decision") == "block"
    assert policy.get("violation_count", 0) >= 1
    assert any(
        "sensitive_columns_exceed_threshold" in v
        for v in policy.get("violations", [])
    )


# --- Contracts ---
def test_generate_fixtures_from_openapi(tmp_path):
    spec = tmp_path / "openapi.yaml"
    spec.write_text("""
openapi: "3.0.0"
info: { title: Test, version: "1.0" }
paths:
  /users:
    get:
      responses:
        "200":
          content:
            application/json:
              schema:
                type: object
                properties:
                  id: { type: integer }
                  name: { type: string }
                required: [id, name]
components:
  schemas: {}
""")
    paths = generate_contract_fixtures(spec, tmp_path / "out", seed=1)
    assert len(paths) >= 1
    json_files = list((tmp_path / "out").glob("*.json"))
    assert len(json_files) >= 1
    import json
    data = json.loads(json_files[0].read_text())
    assert "id" in data or "name" in data


def test_validate_generated_fixtures(tmp_path):
    spec = tmp_path / "openapi.yaml"
    spec.write_text("""
openapi: "3.0.0"
info: { title: Test, version: "1.0" }
components:
  schemas:
    User:
      type: object
      properties:
        id: { type: integer }
        name: { type: string }
      required: [id, name]
""")
    (tmp_path / "fixtures").mkdir()
    (tmp_path / "fixtures" / "User.json").write_text('{"id": 1, "name": "alice"}')
    report = validate_contract_fixtures(spec, tmp_path / "fixtures")
    assert report["total"] >= 1
    assert report["passed"] >= 1
    assert report["failed"] == 0


def test_validate_detects_invalid_fixture(tmp_path):
    spec = tmp_path / "openapi.yaml"
    spec.write_text("""
openapi: "3.0.0"
components:
  schemas:
    Order:
      type: object
      properties:
        customer_id: { type: integer }
      required: [customer_id]
""")
    (tmp_path / "fixtures").mkdir()
    (tmp_path / "fixtures" / "bad.json").write_text('{"other": 1}')
    report = validate_contract_fixtures(spec, tmp_path / "fixtures")
    assert report["failed"] >= 1
    reasons = " ".join(str(f.get("reason", "")).lower() for f in report.get("failures", []))
    assert "required" in reasons or "customer_id" in reasons


def test_cli_generate_contracts(tmp_path):
    spec = tmp_path / "api.yaml"
    spec.write_text("""
openapi: "3.0.0"
paths:
  /items:
    get:
      responses:
        "200":
          content:
            application/json:
              schema:
                type: object
                properties:
                  items: { type: array, items: { type: string } }
""")
    r = _run_cli(["generate-contracts", "--schema", str(spec), "-o", str(tmp_path)])
    assert r.returncode == 0
    assert (tmp_path / "get_items_response_200.json").exists() or list(tmp_path.glob("*.json"))


def test_cli_validate_contracts(tmp_path):
    spec = tmp_path / "api.yaml"
    spec.write_text("""
openapi: "3.0.0"
components:
  schemas:
    X:
      type: object
      properties: { a: { type: string } }
""")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "X.json").write_text('{"a": "ok"}')
    r = _run_cli(["validate-contracts", "--schema", str(spec), "--data", str(tmp_path / "data")])
    assert r.returncode == 0


# --- Regression ---
def test_warn_mode_reports_sensitive():
    schema = SchemaModel(
        tables=[TableDef(name="users", columns=[
            ColumnDef(name="account_number", data_type=DataType.STRING),
        ])]
    )
    r = classify_schema(schema)
    assert r.pii_detection["users"]["account_number"] == "financial"
    assert any("financial" in w for w in r.warnings)
