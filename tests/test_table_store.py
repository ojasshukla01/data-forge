"""Tests for table store backends."""

from pathlib import Path

from data_forge.table_store import InMemoryTableStore, SpillBackedTableStore, build_table_store


def test_in_memory_table_store_round_trip() -> None:
    store = InMemoryTableStore()
    store.set_table_rows("users", [{"id": 1}, {"id": 2}])
    store.append_rows("users", [{"id": 3}])
    assert store.get_row_count("users") == 3
    assert store.sample_rows("users", 2) == [{"id": 1}, {"id": 2}]
    assert [r["id"] for r in store.iter_rows("users")] == [1, 2, 3]


def test_spill_table_store_round_trip_and_cleanup(tmp_path: Path) -> None:
    spill_dir = tmp_path / "spill"
    store = SpillBackedTableStore(spill_dir=spill_dir)
    store.append_rows("orders", [{"id": 10}, {"id": 11}])
    store.append_rows("orders", [{"id": 12}])
    assert store.get_row_count("orders") == 3
    assert [r["id"] for r in store.iter_rows("orders")] == [10, 11, 12]
    assert spill_dir.exists()
    store.cleanup()
    assert not spill_dir.exists()


def test_build_table_store_factory() -> None:
    assert build_table_store("memory").backend_name == "memory"
    assert build_table_store("spill").backend_name == "spill"
    assert build_table_store("unknown").backend_name == "memory"
