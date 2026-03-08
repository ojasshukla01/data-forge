"""Redaction of sensitive values in previews and reports."""

from dataclasses import dataclass
from typing import Any

from data_forge.pii.classifier import PiiCategory


@dataclass
class RedactionConfig:
    """Configuration for redaction behavior."""

    enabled: bool = True
    # Category-specific masks
    masks: dict[str, str] | None = None

    def get_mask(self, category: str) -> str:
        defaults = {
            PiiCategory.EMAIL.value: "***@***",
            PiiCategory.PHONE.value: "***REDACTED***",
            PiiCategory.NAME.value: "***REDACTED***",
            PiiCategory.ADDRESS.value: "***REDACTED***",
            PiiCategory.DATE_OF_BIRTH.value: "***REDACTED***",
            PiiCategory.GOVERNMENT_ID.value: "***REDACTED***",
            PiiCategory.FINANCIAL.value: "***REDACTED***",
            PiiCategory.HEALTH.value: "***REDACTED***",
            PiiCategory.CREDENTIALS.value: "***SECRET***",
            PiiCategory.FREE_TEXT_SENSITIVE.value: "***REDACTED***",
            PiiCategory.UNKNOWN_SENSITIVE.value: "***REDACTED***",
        }
        m = self.masks or {}
        return m.get(category, defaults.get(category, "***REDACTED***"))


def redact_value(value: Any, category: str, config: RedactionConfig) -> Any:
    """Redact a single value if config.enabled and category is sensitive."""
    if not config.enabled or value is None:
        return value
    if category in (PiiCategory.UNCLASSIFIED.value, "unclassified"):
        return value
    return config.get_mask(category)


def redact_dict(
    d: dict[str, Any],
    column_classification: dict[str, str],
    config: RedactionConfig,
) -> dict[str, Any]:
    """Redact values in a dict based on column -> category mapping."""
    if not config.enabled:
        return d
    out: dict[str, Any] = {}
    for k, v in d.items():
        cat = column_classification.get(k, PiiCategory.UNCLASSIFIED.value)
        if cat == PiiCategory.UNCLASSIFIED.value:
            out[k] = v
        else:
            out[k] = redact_value(v, cat, config)
    return out


def redact_samples(
    samples: list[dict[str, Any]],
    table_name: str,
    pii_detection: dict[str, dict[str, str]],
    config: RedactionConfig,
) -> list[dict[str, Any]]:
    """Redact sensitive columns in sample rows."""
    if not config.enabled or not samples:
        return samples
    col_cats = pii_detection.get(table_name, {})
    if not col_cats:
        return samples
    return [redact_dict(r, col_cats, config) for r in samples]
