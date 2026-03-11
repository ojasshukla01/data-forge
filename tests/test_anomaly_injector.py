"""Tests for anomaly injector."""

from data_forge.anomaly_injector import inject_anomalies, AnomalyType


def test_empty_string_anomaly():
    rows = [{"a": "hello", "b": "world"}]
    result = inject_anomalies(
        rows,
        ratio=1.0,
        seed=42,
        anomaly_types=[AnomalyType.EMPTY_STRING],
    )
    assert len(result) >= 1
    assert result[0]["a"] == "" or result[0]["b"] == ""


def test_malformed_string_anomaly():
    rows = [{"x": "normal"}]
    result = inject_anomalies(
        rows,
        ratio=1.0,
        seed=99,
        anomaly_types=[AnomalyType.MALFORMED_STRING],
    )
    assert "\x00" in str(result[0].get("x", "")) or "broken" in str(result[0].get("x", ""))


def test_rows_without_string_columns_no_crash():
    """Anomaly injector must never crash when row has no string columns."""
    rows = [
        {"id": 1, "count": 10, "active": True},
        {"id": 2, "count": 20, "active": False},
    ]
    result = inject_anomalies(
        rows,
        ratio=0.5,
        seed=123,
        anomaly_types=[AnomalyType.EMPTY_STRING, AnomalyType.MALFORMED_STRING],
    )
    assert len(result) >= 2
    assert result[0]["id"] in (1, 2)
    assert result[1]["id"] in (1, 2)


def test_null_field_anomaly():
    rows = [{"a": 1, "b": 2}]
    result = inject_anomalies(
        rows,
        ratio=1.0,
        seed=1,
        anomaly_types=[AnomalyType.NULL_FIELD],
    )
    has_none = any(v is None for v in result[0].values())
    assert has_none
