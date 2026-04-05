"""Extended tests for LineageStore and ProvenanceGraph edge cases.

Issue #55: Updated to use per-port dict format for input_hashes/output_hashes.
"""

from __future__ import annotations

import sqlite3

import pytest

from scieasy.core.lineage.graph import ProvenanceGraph
from scieasy.core.lineage.record import LineageRecord
from scieasy.core.lineage.store import LineageStore


class TestLineageStoreClose:
    """LineageStore.close — resource cleanup."""

    def test_close_then_query_raises(self) -> None:
        store = LineageStore(":memory:")
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
            input_hashes={"p": ["h1"]},
            output_hashes={"p": ["h2"]},
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

    # ADR-020: test_write_with_batch_info removed — batch_info field deleted.
    # ADR-018: TODO: Add test for termination, partial_output_refs, termination_detail.
    def test_write_with_termination_fields(self) -> None:
        store = LineageStore(":memory:")
        record = LineageRecord(
            block_id="b1",
            block_version="1.0",
            block_config={"param": "value"},
            input_hashes={"data": ["in1"]},
            output_hashes={"data": ["out1"]},
            timestamp="2026-01-01T00:00:00",
            duration_ms=50,
            termination="cancelled",
            partial_output_refs=["partial_out1"],
            termination_detail="User cancelled via UI",
        )
        store.write(record)
        records = store.query()
        assert len(records) == 1
        assert records[0].termination == "cancelled"
        assert records[0].partial_output_refs == ["partial_out1"]
        assert records[0].termination_detail == "User cancelled via UI"
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
            input_hashes={"p": ["in1"]},
            output_hashes={"p": ["out1"]},
            timestamp="2026-01-01T00:00:00",
            duration_ms=10,
        )
        graph = ProvenanceGraph()
        graph.build([record])
        assert graph.ancestors("totally_missing") == []
