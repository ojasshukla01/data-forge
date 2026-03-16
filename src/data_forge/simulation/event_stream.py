"""Event stream generation for pipeline simulation."""

import json
import random
from pathlib import Path
from typing import Any

from data_forge.simulation.time_patterns import EventPattern, apply_time_pattern


# Event types per domain pack (extensible)
PACK_EVENT_TYPES: dict[str, list[str]] = {
    "ecommerce": [
        "order_created",
        "payment_captured",
        "order_packed",
        "order_shipped",
        "order_delivered",
        "order_refunded",
    ],
    "fintech_transactions": [
        "payment_initiated",
        "payment_authorized",
        "payment_settled",
        "payment_reversed",
        "fraud_flagged",
    ],
    "logistics_supply_chain": [
        "po_created",
        "shipment_dispatched",
        "shipment_in_transit",
        "delivery_completed",
        "return_created",
    ],
    "iot_telemetry": [
        "reading_ingested",
        "threshold_breach",
        "alert_triggered",
        "maintenance_recorded",
    ],
    "social_platform": [
        "post_created",
        "comment_added",
        "like_added",
        "follow_created",
        "report_created",
    ],
    "saas_billing": [
        "subscription_created",
        "invoice_issued",
        "payment_received",
        "subscription_cancelled",
    ],
    "payments_ledger": [
        "invoice_created",
        "payment_captured",
        "refund_issued",
        "dispute_created",
    ],
}


def generate_event_stream(
    pack_id: str,
    event_count: int,
    start_ts: float,
    end_ts: float,
    pattern: EventPattern = EventPattern.STEADY,
    replay_mode: str = "ordered",
    late_arrival_ratio: float = 0.0,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """
    Generate a list of event records.
    Each event has: event_type, ts, entity_id, payload (optional).
    Deterministic with fixed seed.
    """
    event_types = PACK_EVENT_TYPES.get(pack_id, ["event"])
    if not event_types:
        event_types = ["event"]

    rng = random.Random(seed)
    timestamps = apply_time_pattern(event_count, pattern, start_ts, end_ts, seed)

    events: list[dict[str, Any]] = []
    for i, ts in enumerate(timestamps):
        event_type = rng.choice(event_types)
        entity_id = f"entity_{rng.randint(1, max(1, event_count // 10))}"
        evt = {
            "event_type": event_type,
            "ts": round(ts, 3),
            "entity_id": entity_id,
            "event_id": f"evt_{i:08d}",
        }
        if late_arrival_ratio > 0 and rng.random() < late_arrival_ratio:
            evt["late_arrival"] = True
            evt["event_ts_original"] = ts
            evt["ts"] = round(ts + rng.uniform(60, 3600), 3)  # 1min–1hr late
        events.append(evt)

    if replay_mode == "shuffled":
        rng.shuffle(events)
    elif replay_mode == "windowed":
        # Sort by ts but in chunks (simulate windowed processing)
        window_size = max(1, len(events) // 5)
        for j in range(0, len(events), window_size):
            chunk = events[j : j + window_size]
            rng.shuffle(chunk)
            events[j : j + window_size] = chunk

    return events


def write_event_stream_jsonl(events: list[dict[str, Any]], path: Path) -> Path:
    """Write events to JSONL file. Returns path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for evt in events:
            f.write(json.dumps(evt, default=str) + "\n")
    return path


def generate_support_ticket_notes(
    events: list[dict[str, Any]],
    *,
    seed: int = 42,
    max_notes: int = 500,
) -> list[dict[str, Any]]:
    """
    Generate lightweight unstructured support notes linked to structured event/entity IDs.
    This provides a rehearsal foundation for mixed structured + text pipelines.
    """
    if not events:
        return []
    rng = random.Random(seed + 101)
    templates = [
        "Customer reported issue after {event_type}. Investigate entity {entity_id}.",
        "Support note: follow-up required for {event_type} on {entity_id}.",
        "Escalation candidate tied to {event_type}; observed anomaly around entity {entity_id}.",
        "Operations comment: verify downstream impact from {event_type} for {entity_id}.",
    ]
    sample_size = min(max_notes, max(1, len(events) // 5))
    selected = events if len(events) <= sample_size else rng.sample(events, sample_size)
    notes: list[dict[str, Any]] = []
    for i, evt in enumerate(selected):
        event_type = str(evt.get("event_type", "event"))
        entity_id = str(evt.get("entity_id", "entity_unknown"))
        note = rng.choice(templates).format(event_type=event_type, entity_id=entity_id)
        notes.append(
            {
                "ticket_id": f"ticket_{i:07d}",
                "entity_id": entity_id,
                "linked_event_id": str(evt.get("event_id", "")),
                "event_type": event_type,
                "ts": evt.get("ts"),
                "note": note,
                "severity": rng.choice(["low", "medium", "high"]),
            }
        )
    return notes


def write_unstructured_notes_jsonl(notes: list[dict[str, Any]], path: Path) -> Path:
    """Write linked unstructured notes as JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in notes:
            f.write(json.dumps(row, default=str) + "\n")
    return path


def build_unstructured_link_report(
    events: list[dict[str, Any]],
    notes: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build a lightweight linkage report for structured+unstructured rehearsal.
    Includes coverage, orphan detection, and severity distribution.
    """
    total_events = len(events)
    total_notes = len(notes)
    event_ids = {str(e.get("event_id", "")) for e in events if e.get("event_id") is not None}
    linked_event_ids = {
        str(n.get("linked_event_id", ""))
        for n in notes
        if n.get("linked_event_id") is not None
    }
    matched_links = sorted(eid for eid in linked_event_ids if eid in event_ids)
    orphan_links = sorted(eid for eid in linked_event_ids if eid and eid not in event_ids)
    by_severity: dict[str, int] = {}
    by_event_type: dict[str, int] = {}
    for note in notes:
        severity = str(note.get("severity", "unknown"))
        by_severity[severity] = by_severity.get(severity, 0) + 1
        event_type = str(note.get("event_type", "event"))
        by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
    coverage_ratio = round(len(matched_links) / max(1, total_events), 4)
    return {
        "total_events": total_events,
        "total_unstructured_notes": total_notes,
        "linked_event_count": len(matched_links),
        "orphan_link_count": len(orphan_links),
        "coverage_ratio": coverage_ratio,
        "by_severity": by_severity,
        "by_event_type": by_event_type,
        "orphan_linked_event_ids": orphan_links[:100],
    }
