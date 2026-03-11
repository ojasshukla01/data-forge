"""Domain packs: pre-built schemas and rules for SaaS, e-commerce, fintech, etc."""

from pathlib import Path
from typing import Any, NamedTuple

from data_forge.schema_ingest import load_schema
from data_forge.rule_engine import load_rule_set
from data_forge.models.schema import SchemaModel
from data_forge.models.rules import RuleSet

__all__ = ["list_packs", "get_pack", "get_pack_metadata", "DomainPack"]

# Resolve paths relative to package: src/data_forge/domain_packs/ -> project root
_PACKS_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Extended metadata for API/UI display
PACK_METADATA: dict[str, dict[str, Any]] = {
    "saas_billing": {
        "name": "SaaS Billing",
        "category": "SaaS / CRM",
        "key_entities": ["organizations", "users", "subscriptions", "invoices", "support_tickets"],
        "recommended_use_cases": ["demo", "unit_test", "integration_test", "etl"],
        "supported_features": ["contracts", "etl_simulation", "warehouse_load", "privacy_scan"],
    },
    "ecommerce": {
        "name": "E-commerce",
        "category": "Retail",
        "key_entities": ["customers", "products", "orders", "payments", "shipments", "inventory"],
        "recommended_use_cases": ["demo", "integration_test", "load_test"],
        "supported_features": ["contracts", "etl_simulation", "warehouse_load", "privacy_scan"],
        "supports_event_streams": True,
        "simulation_event_types": ["order_created", "payment_captured", "order_packed", "order_shipped", "order_delivered", "order_refunded"],
        "benchmark_relevance": "high",
    },
    "fintech_transactions": {
        "name": "Fintech Transactions",
        "category": "Fintech",
        "key_entities": ["customers", "accounts", "cards", "transactions", "merchants", "fraud_flags"],
        "recommended_use_cases": ["integration_test", "load_test", "etl"],
        "supported_features": ["contracts", "etl_simulation", "warehouse_load", "privacy_scan"],
    },
    "healthcare_ops": {
        "name": "Healthcare Operations",
        "category": "Healthcare",
        "key_entities": ["patients", "providers", "appointments", "encounters", "claims", "prescriptions"],
        "recommended_use_cases": ["demo", "integration_test", "privacy_demo"],
        "supported_features": ["contracts", "etl_simulation", "warehouse_load", "privacy_scan"],
    },
    "logistics_supply_chain": {
        "name": "Logistics & Supply Chain",
        "category": "Logistics",
        "key_entities": ["warehouses", "suppliers", "purchase_orders", "shipments", "inventory_movements", "deliveries"],
        "recommended_use_cases": ["integration_test", "etl", "load_test"],
        "supported_features": ["contracts", "etl_simulation", "warehouse_load"],
        "supports_event_streams": True,
        "simulation_event_types": ["po_created", "shipment_dispatched", "shipment_in_transit", "delivery_completed", "return_created"],
        "benchmark_relevance": "medium",
    },
    "adtech_analytics": {
        "name": "AdTech Analytics",
        "category": "AdTech",
        "key_entities": ["advertisers", "campaigns", "ad_groups", "impressions", "clicks", "conversions"],
        "recommended_use_cases": ["demo", "integration_test", "analytics_demo"],
        "supported_features": ["contracts", "etl_simulation", "warehouse_load"],
    },
    "hr_workforce": {
        "name": "HR Workforce",
        "category": "HR",
        "key_entities": ["employees", "departments", "roles", "payroll", "leave_requests", "performance_reviews"],
        "recommended_use_cases": ["demo", "unit_test", "integration_test"],
        "supported_features": ["contracts", "etl_simulation", "warehouse_load", "privacy_scan"],
    },
    "iot_telemetry": {
        "name": "IoT Telemetry",
        "category": "IoT",
        "key_entities": ["devices", "device_models", "telemetry_readings", "alerts", "maintenance_events"],
        "recommended_use_cases": ["integration_test", "time_series_demo", "etl"],
        "supported_features": ["contracts", "etl_simulation", "warehouse_load"],
        "supports_event_streams": True,
        "simulation_event_types": ["reading_ingested", "threshold_breach", "alert_triggered", "maintenance_recorded"],
        "benchmark_relevance": "high",
    },
    "social_platform": {
        "name": "Social Platform",
        "category": "Social",
        "key_entities": ["users", "profiles", "posts", "comments", "likes", "follows", "messages"],
        "recommended_use_cases": ["demo", "integration_test", "load_test"],
        "supported_features": ["contracts", "etl_simulation", "warehouse_load", "privacy_scan"],
        "supports_event_streams": True,
        "simulation_event_types": ["post_created", "comment_added", "like_added", "follow_created", "report_created"],
        "benchmark_relevance": "medium",
    },
    "payments_ledger": {
        "name": "Payments Ledger",
        "category": "Payments",
        "key_entities": ["customers", "invoices", "payments", "ledger_entries", "refunds", "disputes"],
        "recommended_use_cases": ["demo", "integration_test", "load_test", "etl"],
        "supported_features": ["contracts", "etl_simulation", "warehouse_load", "privacy_scan"],
        "supports_event_streams": True,
        "simulation_event_types": ["invoice_created", "payment_captured", "refund_issued", "dispute_created"],
        "benchmark_relevance": "high",
    },
}


class DomainPack(NamedTuple):
    """A domain pack: schema + rule set + name."""

    name: str
    schema: SchemaModel
    rule_set: RuleSet
    description: str


def _project_path(*parts: str) -> Path:
    return _PACKS_ROOT.joinpath(*parts)


def list_packs() -> list[tuple[str, str]]:
    """Return (pack_id, description) for each built-in pack."""
    return [
        ("saas_billing", "SaaS / CRM: organizations, users, plans, subscriptions, invoices, support tickets"),
        ("ecommerce", "E-commerce: customers, products, orders, payments, refunds, shipments, inventory"),
        ("fintech_transactions", "Fintech: customers, accounts, cards, transactions, merchants, settlements, fraud_flags"),
        ("healthcare_ops", "Healthcare: patients, providers, appointments, encounters, diagnoses, prescriptions, claims"),
        ("logistics_supply_chain", "Logistics: warehouses, suppliers, purchase orders, shipments, inventory, deliveries"),
        ("adtech_analytics", "AdTech: advertisers, campaigns, ad groups, impressions, clicks, conversions"),
        ("hr_workforce", "HR: employees, departments, roles, payroll, leave requests, performance reviews"),
        ("iot_telemetry", "IoT: devices, models, locations, telemetry readings, alerts, maintenance"),
        ("social_platform", "Social: users, profiles, posts, comments, likes, follows, messages"),
        ("payments_ledger", "Payments: customers, invoices, payments, ledger entries, refunds, disputes"),
    ]


def get_pack_metadata(pack_id: str) -> dict[str, Any] | None:
    """Return extended metadata for a pack, or None if not found."""
    return PACK_METADATA.get(pack_id)


def get_pack(pack_id: str) -> DomainPack | None:
    """Load a domain pack by id. Returns None if not found."""
    schema_path = _project_path("schemas", f"{pack_id}.sql")
    rules_path = _project_path("rules", f"{pack_id}.yaml")
    if not schema_path.exists():
        schema_path = _project_path("schemas", f"{pack_id}.json")
    if not schema_path.exists():
        return None
    schema = load_schema(schema_path, project_root=_PACKS_ROOT)
    rule_set = load_rule_set(rules_path, project_root=_PACKS_ROOT)
    desc = next((d for pid, d in list_packs() if pid == pack_id), "")
    return DomainPack(name=pack_id, schema=schema, rule_set=rule_set, description=desc)
