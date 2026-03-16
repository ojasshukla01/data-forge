"""Tests for row/cardinality planner. Lock default heuristic behavior."""

from data_forge.models.schema import ColumnDef, DataType, SchemaModel, TableDef
from data_forge.generators.row_planner import default_plan_row_counts, _row_count_for_table


def _minimal_table(name: str) -> TableDef:
    return TableDef(name=name, columns=[ColumnDef(name="id", data_type=DataType.INTEGER, primary_key=True)])


def test_row_count_for_table_heuristics():
    """Default heuristics: users/customers/orgs/products=scale; orders/invoices/subs=max(scale//2, scale*2); line/item/detail=scale*3; else scale."""
    scale = 1000
    assert _row_count_for_table(_minimal_table("users"), scale) == 1000
    assert _row_count_for_table(_minimal_table("customers"), scale) == 1000
    assert _row_count_for_table(_minimal_table("organizations"), scale) == 1000
    assert _row_count_for_table(_minimal_table("products"), scale) == 1000
    assert _row_count_for_table(_minimal_table("orders"), scale) == max(500, 2000)
    assert _row_count_for_table(_minimal_table("invoices"), scale) == max(500, 2000)
    assert _row_count_for_table(_minimal_table("subscriptions"), scale) == max(500, 2000)
    assert _row_count_for_table(_minimal_table("order_lines"), scale) == 3000
    assert _row_count_for_table(_minimal_table("line_items"), scale) == 3000
    assert _row_count_for_table(_minimal_table("invoice_details"), scale) == 3000
    assert _row_count_for_table(_minimal_table("other"), scale) == 1000


def test_default_plan_row_counts_same_as_engine():
    """Planner returns same counts as previous engine logic for a small schema."""
    schema = SchemaModel(
        name="test",
        tables=[
            _minimal_table("users"),
            _minimal_table("orders"),
            _minimal_table("order_lines"),
        ],
    )
    scale = 100
    counts = default_plan_row_counts(schema, scale, None)
    assert counts["users"] == 100
    assert counts["orders"] == max(50, 200)
    assert counts["order_lines"] == 300


def test_default_plan_row_counts_respects_tables_filter():
    """When tables_filter is set, only those tables get entries."""
    schema = SchemaModel(
        name="test",
        tables=[_minimal_table("users"), _minimal_table("orders")],
    )
    counts = default_plan_row_counts(schema, 50, ["users"])
    assert counts == {"users": 50}
