"""Extended tests for LineageStore and ProvenanceGraph edge cases."""

from __future__ import annotations

import sqlite3

import pytest

from scieasy.core.lineage.graph import ProvenanceGraph
from scieasy.core.lineage.record import LineageRecord
from scieasy.core.lineage.store import LineageStore


class TestLineageStoreClose:
    """LineageStore.close — resource cleanup."""

    def test_close_then_query_raises(self) -> None:
        store = LineageStore()
        store.close()
        with pytest.raises(sqlite3.ProgrammingError):
            store.query()

    def test_file_based_store(self, tmp_path: pytest.TempPathFactory) -> None:
        db_path = tmp_path / "lineage.db"  # type: ignore[operator]
        store = LineageStore(db_path)
        record = LineageRecord(
            block_id="b1",
            block_version="1.0",
            block_config={},
            input_hashes=["h1"],
            output_hashes=["h2"],
            timestamp="2026-01-01T00:00:00",
            duration_ms=100,
        )
        store.write(record)
        store.close()

        # Re-open and verify data persists
        store2 = LineageStore(db_path)
        records = store2.query()
        assert len(records) == 1
        assert records[0].block_id == "b1"
        store2.close()

    def test_write_with_batch_info(self) -> None:
        store = LineageStore()
        record = LineageRecord(
            block_id="b1",
            block_version="1.0",
            block_config={"param": "value"},
            input_hashes=["in1"],
            output_hashes=["out1"],
            timestamp="2026-01-01T00:00:00",
            duration_ms=50,
            batch_info={"batch_id": 0, "total": 10},
        )
        store.write(record)
        records = store.query()
        assert len(records) == 1
        assert records[0].batch_info == {"batch_id": 0, "total": 10}
        store.close()


class TestProvenanceGraphEdgeCases:
    """ProvenanceGraph — edge cases with empty or missing data."""

    def test_empty_graph_ancestors(self) -> None:
        graph = ProvenanceGraph()
        graph.build([])
        assert graph.ancestors("nonexistent") == []

    def test_empty_graph_descendants(self) -> None:
        graph = ProvenanceGraph()
        graph.build([])
        assert graph.descendants("nonexistent") == []

    def test_empty_graph_audit_trail(self) -> None:
        graph = ProvenanceGraph()
        graph.build([])
        assert graph.audit_trail("nonexistent") == []

    def test_ancestors_nonexistent_hash(self) -> None:
        record = LineageRecord(
            block_id="b1",
            block_version="1.0",
            block_config={},
            input_hashes=["in1"],
            output_hashes=["out1"],
            timestamp="2026-01-01T00:00:00",
            duration_ms=10,
        )
        graph = ProvenanceGraph()
        graph.build([record])
        assert graph.ancestors("totally_missing") == []
