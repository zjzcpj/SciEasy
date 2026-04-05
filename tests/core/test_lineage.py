"""Tests for lineage: write record, query, ancestor trace (Phase 3.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scieasy.core.lineage.environment import EnvironmentSnapshot
from scieasy.core.lineage.graph import ProvenanceGraph
from scieasy.core.lineage.record import LineageRecord
from scieasy.core.lineage.store import LineageStore


def _make_record(
    block_id: str,
    input_hashes: list[str],
    output_hashes: list[str],
    timestamp: str = "2026-01-01T00:00:00",
) -> LineageRecord:
    """Helper to create a LineageRecord with minimal fields."""
    return LineageRecord(
        input_hashes=input_hashes,
        block_id=block_id,
        block_config={"param": 1},
        block_version="1.0.0",
        output_hashes=output_hashes,
        timestamp=timestamp,
        duration_ms=100,
    )


class TestEnvironmentSnapshot:
    """Verify EnvironmentSnapshot.capture()."""

    def test_capture_basic(self) -> None:
        snap = EnvironmentSnapshot.capture()
        assert "3." in snap.python_version  # Python 3.x
        assert snap.platform != ""
        assert isinstance(snap.key_packages, dict)

    def test_capture_custom_deps(self) -> None:
        snap = EnvironmentSnapshot.capture(key_dependencies=["numpy", "zarr"])
        assert "numpy" in snap.key_packages
        assert "zarr" in snap.key_packages

    def test_capture_missing_package_skipped(self) -> None:
        snap = EnvironmentSnapshot.capture(key_dependencies=["nonexistent_pkg_12345"])
        assert "nonexistent_pkg_12345" not in snap.key_packages


class TestEnvironmentSnapshotSerialization:
    """Verify to_dict / from_dict round-trip serialization (issue #54)."""

    def test_to_dict_round_trip(self) -> None:
        """to_dict + from_dict preserves all fields."""
        snapshot = EnvironmentSnapshot.capture()
        data = snapshot.to_dict()
        restored = EnvironmentSnapshot.from_dict(data)
        assert restored.python_version == snapshot.python_version
        assert restored.platform == snapshot.platform
        assert restored.key_packages == snapshot.key_packages
        assert restored.full_freeze == snapshot.full_freeze
        assert restored.conda_env == snapshot.conda_env

    def test_to_dict_is_json_serializable(self) -> None:
        """to_dict output can be JSON-serialized."""
        import json

        snapshot = EnvironmentSnapshot.capture()
        data = snapshot.to_dict()
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

    def test_from_dict_handles_missing_optional_fields(self) -> None:
        """from_dict works with minimal required fields."""
        data = {"python_version": "3.11.0", "platform": "Linux"}
        snapshot = EnvironmentSnapshot.from_dict(data)
        assert snapshot.python_version == "3.11.0"
        assert snapshot.platform == "Linux"
        assert snapshot.key_packages == {}
        assert snapshot.full_freeze is None
        assert snapshot.conda_env is None

    def test_to_dict_includes_all_keys(self) -> None:
        """to_dict output contains all expected keys."""
        snapshot = EnvironmentSnapshot(
            python_version="3.12.0",
            platform="Linux-6.1",
            key_packages={"numpy": "1.26.0"},
            full_freeze="numpy==1.26.0\nzarr==2.18.0",
            conda_env="name: sci\ndependencies:\n  - numpy",
        )
        data = snapshot.to_dict()
        assert data == {
            "python_version": "3.12.0",
            "platform": "Linux-6.1",
            "key_packages": {"numpy": "1.26.0"},
            "full_freeze": "numpy==1.26.0\nzarr==2.18.0",
            "conda_env": "name: sci\ndependencies:\n  - numpy",
        }
        restored = EnvironmentSnapshot.from_dict(data)
        assert restored == snapshot


class TestLineageStore:
    """Verify SQLite-backed LineageStore."""

    def test_write_and_query(self) -> None:
        store = LineageStore(":memory:")
        record = _make_record("block_A", ["hash_in_1"], ["hash_out_1"])
        store.write(record)

        results = store.query(block_id="block_A")
        assert len(results) == 1
        assert results[0].block_id == "block_A"
        assert results[0].input_hashes == ["hash_in_1"]
        assert results[0].output_hashes == ["hash_out_1"]

    def test_query_all(self) -> None:
        store = LineageStore(":memory:")
        store.write(_make_record("A", ["h1"], ["h2"]))
        store.write(_make_record("B", ["h2"], ["h3"]))
        results = store.query()
        assert len(results) == 2

    def test_query_nonexistent_block(self) -> None:
        store = LineageStore(":memory:")
        store.write(_make_record("A", ["h1"], ["h2"]))
        results = store.query(block_id="nonexistent")
        assert len(results) == 0

    def test_write_with_environment(self) -> None:
        store = LineageStore(":memory:")
        env = EnvironmentSnapshot.capture()
        record = LineageRecord(
            input_hashes=["in1"],
            block_id="env_block",
            block_config={},
            block_version="1.0",
            output_hashes=["out1"],
            timestamp="2026-01-01T00:00:00",
            duration_ms=50,
            environment=env,
        )
        store.write(record)
        results = store.query(block_id="env_block")
        assert len(results) == 1
        assert results[0].environment is not None
        assert "3." in results[0].environment.python_version

    def test_ancestors_linear_chain(self) -> None:
        """A -> B -> C: ancestors of C's output should include B and A."""
        store = LineageStore(":memory:")
        store.write(_make_record("A", ["raw"], ["h1"], timestamp="2026-01-01T00:00:00"))
        store.write(_make_record("B", ["h1"], ["h2"], timestamp="2026-01-01T00:01:00"))
        store.write(_make_record("C", ["h2"], ["h3"], timestamp="2026-01-01T00:02:00"))

        ancestors = store.ancestors("h3")
        block_ids = [r.block_id for r in ancestors]
        assert "C" in block_ids
        assert "B" in block_ids
        assert "A" in block_ids

    def test_ancestors_no_match(self) -> None:
        store = LineageStore(":memory:")
        store.write(_make_record("A", ["h1"], ["h2"]))
        ancestors = store.ancestors("nonexistent")
        assert ancestors == []

    def test_store_ancestors_diamond_no_duplicates(self) -> None:
        """LineageStore ancestors should deduplicate in diamond patterns."""
        store = LineageStore(":memory:")
        store.write(_make_record("A", ["raw"], ["h1", "h2"], timestamp="2026-01-01T00:00:00"))
        store.write(_make_record("B", ["h1", "h2"], ["h3"], timestamp="2026-01-01T00:01:00"))
        ancestors = store.ancestors("h3")
        block_ids = [r.block_id for r in ancestors]
        assert block_ids.count("A") == 1

    def test_default_path_persists(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """LineageStore with default path persists records to disk."""
        monkeypatch.chdir(tmp_path)
        store = LineageStore()
        record = _make_record("persist_block", ["h_in"], ["h_out"])
        store.write(record)
        store.close()

        store2 = LineageStore()
        results = store2.query(block_id="persist_block")
        assert len(results) == 1
        assert results[0].output_hashes == ["h_out"]
        store2.close()


class TestProvenanceGraph:
    """Verify in-memory ProvenanceGraph."""

    def _build_linear_graph(self) -> tuple[ProvenanceGraph, list[LineageRecord]]:
        """Build a simple linear A -> B -> C graph."""
        records = [
            _make_record("A", ["raw"], ["h1"], timestamp="2026-01-01T00:00:00"),
            _make_record("B", ["h1"], ["h2"], timestamp="2026-01-01T00:01:00"),
            _make_record("C", ["h2"], ["h3"], timestamp="2026-01-01T00:02:00"),
        ]
        graph = ProvenanceGraph()
        graph.build(records)
        return graph, records

    def test_ancestors(self) -> None:
        graph, _ = self._build_linear_graph()
        ancestors = graph.ancestors("h3")
        block_ids = [r.block_id for r in ancestors]
        assert "C" in block_ids
        assert "B" in block_ids
        assert "A" in block_ids

    def test_ancestors_partial(self) -> None:
        graph, _ = self._build_linear_graph()
        ancestors = graph.ancestors("h2")
        block_ids = [r.block_id for r in ancestors]
        assert "B" in block_ids
        assert "A" in block_ids
        assert "C" not in block_ids

    def test_descendants(self) -> None:
        graph, _ = self._build_linear_graph()
        descendants = graph.descendants("h1")
        block_ids = [r.block_id for r in descendants]
        assert "B" in block_ids
        assert "C" in block_ids

    def test_audit_trail_ordered(self) -> None:
        graph, _ = self._build_linear_graph()
        trail = graph.audit_trail("h3")
        block_ids = [r.block_id for r in trail]
        assert block_ids == ["A", "B", "C"]

    def test_descendants_diamond_no_duplicates(self) -> None:
        """Diamond DAG: D should appear exactly once in descendants."""
        records = [
            _make_record("A", ["raw"], ["h1"], timestamp="2026-01-01T00:00:00"),
            _make_record("B", ["h1"], ["h2"], timestamp="2026-01-01T00:01:00"),
            _make_record("C", ["h1"], ["h3"], timestamp="2026-01-01T00:01:00"),
            _make_record("D", ["h2", "h3"], ["h4"], timestamp="2026-01-01T00:02:00"),
        ]
        graph = ProvenanceGraph()
        graph.build(records)
        descendants = graph.descendants("h1")
        block_ids = [r.block_id for r in descendants]
        assert block_ids.count("D") == 1
        assert set(block_ids) == {"B", "C", "D"}

    def test_ancestors_multi_output_no_duplicates(self) -> None:
        """Record with multiple outputs should appear once in ancestors."""
        records = [
            _make_record("A", ["raw"], ["h1", "h2"], timestamp="2026-01-01T00:00:00"),
            _make_record("B", ["h1", "h2"], ["h3"], timestamp="2026-01-01T00:01:00"),
        ]
        graph = ProvenanceGraph()
        graph.build(records)
        ancestors = graph.ancestors("h3")
        block_ids = [r.block_id for r in ancestors]
        assert block_ids.count("A") == 1
        assert set(block_ids) == {"A", "B"}

    def test_diff(self) -> None:
        """Build a diamond: A -> B, A -> C, B+C -> D."""
        records = [
            _make_record("A", ["raw"], ["h1"], timestamp="2026-01-01T00:00:00"),
            _make_record("B", ["h1"], ["h2"], timestamp="2026-01-01T00:01:00"),
            _make_record("C", ["h1"], ["h3"], timestamp="2026-01-01T00:01:00"),
            _make_record("D", ["h2", "h3"], ["h4"], timestamp="2026-01-01T00:02:00"),
        ]
        graph = ProvenanceGraph()
        graph.build(records)

        diff = graph.diff("h2", "h4")
        only_in_b_ids = {r.block_id for r in diff["only_in_b"]}
        # h4's ancestry includes D and C (which are not in h2's ancestry)
        assert "D" in only_in_b_ids
        assert "C" in only_in_b_ids


class TestLineageTerminationFields:
    """ADR-018: termination, partial_output_refs, termination_detail fields."""

    def test_default_termination_is_completed(self) -> None:
        record = _make_record("block_A", ["in1"], ["out1"])
        assert record.termination == "completed"
        assert record.partial_output_refs == []
        assert record.termination_detail == ""

    def test_cancelled_termination(self) -> None:
        record = LineageRecord(
            input_hashes=["in1"],
            block_id="block_B",
            block_config={},
            block_version="1.0",
            output_hashes=[],
            timestamp="2026-01-01T00:00:00",
            duration_ms=50,
            termination="cancelled",
            partial_output_refs=["partial_1"],
            termination_detail="User cancelled via WebSocket",
        )
        assert record.termination == "cancelled"
        assert record.partial_output_refs == ["partial_1"]
        assert record.termination_detail == "User cancelled via WebSocket"

    def test_skipped_termination(self) -> None:
        record = LineageRecord(
            input_hashes=[],
            block_id="block_C",
            block_config={},
            block_version="1.0",
            output_hashes=[],
            timestamp="2026-01-01T00:00:00",
            duration_ms=0,
            termination="skipped",
            termination_detail="upstream block_A error",
        )
        assert record.termination == "skipped"
        assert record.termination_detail == "upstream block_A error"

    def test_error_termination(self) -> None:
        record = LineageRecord(
            input_hashes=["in1"],
            block_id="block_D",
            block_config={"param": 1},
            block_version="1.0",
            output_hashes=[],
            timestamp="2026-01-01T00:00:00",
            duration_ms=200,
            termination="error",
            partial_output_refs=["partial_out1", "partial_out2"],
            termination_detail="ZeroDivisionError in process_item",
        )
        assert record.termination == "error"
        assert len(record.partial_output_refs) == 2

    def test_store_round_trip_with_termination(self) -> None:
        """Write a record with termination fields and read it back."""
        store = LineageStore(":memory:")
        record = LineageRecord(
            input_hashes=["in"],
            block_id="store_test",
            block_config={},
            block_version="1.0",
            output_hashes=["out"],
            timestamp="2026-01-01T00:00:00",
            duration_ms=10,
            termination="cancelled",
            partial_output_refs=["p1"],
            termination_detail="test cancel",
        )
        store.write(record)
        results = store.query(block_id="store_test")
        assert len(results) == 1
        assert results[0].termination == "cancelled"
        assert results[0].partial_output_refs == ["p1"]
        assert results[0].termination_detail == "test cancel"
