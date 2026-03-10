"""PII / sensitive field detection based on names, hints, and patterns."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from data_forge.models.schema import SchemaModel


class PiiCategory(str, Enum):
    """Known PII/sensitive categories."""

    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    GOVERNMENT_ID = "government_id"
    FINANCIAL = "financial"
    HEALTH = "health"
    CREDENTIALS = "credentials"
    FREE_TEXT_SENSITIVE = "free_text_sensitive"
    UNKNOWN_SENSITIVE = "unknown_sensitive"
    UNCLASSIFIED = "unclassified"


class Certainty(str, Enum):
    """Classification certainty level."""

    DETECTED = "detected"
    SUSPECTED = "suspected"
    UNCLASSIFIED = "unclassified"


@dataclass
class ClassificationResult:
    """Per-table, per-column PII classification."""

    pii_detection: dict[str, dict[str, str]]  # table -> {column -> category}
    certainty: dict[str, dict[str, str]]  # table -> {column -> certainty}
    warnings: list[str]

    def to_report_dict(self) -> dict[str, Any]:
        return {"pii_detection": self.pii_detection}


# Column name patterns -> (category, certainty)
_COLUMN_PATTERNS: list[tuple[list[str], PiiCategory, Certainty]] = [
    # Email
    (["email", "email_address", "e_mail", "mail"], PiiCategory.EMAIL, Certainty.DETECTED),
    (["contact_email", "user_email"], PiiCategory.EMAIL, Certainty.SUSPECTED),
    # Phone
    (["phone", "mobile", "cell", "contact_number", "phone_number", "fax", "telephone"], PiiCategory.PHONE, Certainty.DETECTED),
    # Name
    (["name", "full_name", "display_name", "legal_name", "user_name", "username"], PiiCategory.NAME, Certainty.DETECTED),
    (["first_name", "firstname", "given_name"], PiiCategory.NAME, Certainty.DETECTED),
    (["last_name", "lastname", "surname", "family_name"], PiiCategory.NAME, Certainty.DETECTED),
    # Address
    (["address", "street", "street_address", "home_address", "billing_address", "shipping_address"], PiiCategory.ADDRESS, Certainty.DETECTED),
    (["city", "zip", "postal_code", "state", "country"], PiiCategory.ADDRESS, Certainty.SUSPECTED),
    # Date of birth
    (["dob", "date_of_birth", "birth_date", "birthdate"], PiiCategory.DATE_OF_BIRTH, Certainty.DETECTED),
    (["birth_year", "age"], PiiCategory.DATE_OF_BIRTH, Certainty.SUSPECTED),
    # Government ID
    (["ssn", "tax_id", "tax_id_number", "medicare_number", "passport_no", "passport_number", "national_id", "drivers_license"], PiiCategory.GOVERNMENT_ID, Certainty.DETECTED),
    (["govt_id", "government_id", "id_number"], PiiCategory.GOVERNMENT_ID, Certainty.SUSPECTED),
    # Financial
    (["account_number", "card_number", "iban", "credit_card", "bank_account", "routing_number", "bic"], PiiCategory.FINANCIAL, Certainty.DETECTED),
    (["salary", "income"], PiiCategory.FINANCIAL, Certainty.SUSPECTED),
    # Health
    (["diagnosis", "condition", "prescription", "medical_record", "health_status"], PiiCategory.HEALTH, Certainty.DETECTED),
    # Credentials
    (["password", "passwd", "pwd", "secret", "token", "api_token", "api_key", "auth_token", "access_token"], PiiCategory.CREDENTIALS, Certainty.DETECTED),
    (["credentials", "private_key"], PiiCategory.CREDENTIALS, Certainty.SUSPECTED),
    # Free text sensitive
    (["notes", "comments", "description", "bio"], PiiCategory.FREE_TEXT_SENSITIVE, Certainty.SUSPECTED),
]

# Generator hints from schema -> category
_HINT_TO_CATEGORY: dict[str, PiiCategory] = {
    "email": PiiCategory.EMAIL,
    "name": PiiCategory.NAME,
    "phone": PiiCategory.PHONE,
    "address": PiiCategory.ADDRESS,
    "company": PiiCategory.NAME,  # company name less sensitive but often PII
}


def _normalize(s: str) -> str:
    return s.lower().replace("-", "_").replace(" ", "_")


def _match_column(name: str) -> tuple[PiiCategory | None, Certainty]:
    n = _normalize(name)
    for patterns, cat, certainty in _COLUMN_PATTERNS:
        if n in patterns or any(p in n for p in patterns):
            return cat, certainty
    return None, Certainty.UNCLASSIFIED


def _match_hint(hint: str | None) -> PiiCategory | None:
    if not hint:
        return None
    return _HINT_TO_CATEGORY.get(_normalize(hint))


def classify_schema(
    schema: SchemaModel,
    overrides_path: Path | str | None = None,
) -> ClassificationResult:
    """
    Classify all columns in schema for PII/sensitive content.
    overrides_path: optional YAML file with manual overrides {table: {column: category}}
    """
    pii: dict[str, dict[str, str]] = {}
    certainty: dict[str, dict[str, str]] = {}
    warnings: list[str] = []

    overrides: dict[str, dict[str, str]] = {}
    if overrides_path:
        p = Path(overrides_path)
        if p.exists():
            try:
                import yaml
                data = yaml.safe_load(p.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "pii_overrides" in data:
                    overrides = data["pii_overrides"]
                elif isinstance(data, dict):
                    overrides = data
            except Exception:
                pass

    for table in schema.tables:
        pii[table.name] = {}
        certainty[table.name] = {}
        for col in table.columns:
            col_name = col.name

            # Manual override
            if table.name in overrides and col_name in overrides[table.name]:
                ov = overrides[table.name][col_name]
                pii[table.name][col_name] = ov
                certainty[table.name][col_name] = Certainty.DETECTED.value
                continue

            # Generator hint
            hint_cat = _match_hint(col.generator_hint)
            if hint_cat:
                pii[table.name][col_name] = hint_cat.value
                certainty[table.name][col_name] = Certainty.DETECTED.value
                continue

            # Column name patterns
            cat, cert = _match_column(col_name)
            if cat:
                pii[table.name][col_name] = cat.value
                certainty[table.name][col_name] = cert.value
                if cert == Certainty.SUSPECTED:
                    warnings.append(f"Detected suspected {cat.value} field: {table.name}.{col_name}")
                elif cat == PiiCategory.CREDENTIALS:
                    warnings.append(f"Detected credentials field: {table.name}.{col_name}")
                elif cat == PiiCategory.FINANCIAL:
                    warnings.append(f"Detected financial field: {table.name}.{col_name}")
            else:
                pii[table.name][col_name] = PiiCategory.UNCLASSIFIED.value
                certainty[table.name][col_name] = Certainty.UNCLASSIFIED.value

    return ClassificationResult(pii_detection=pii, certainty=certainty, warnings=warnings)
