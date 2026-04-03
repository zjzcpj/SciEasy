"""Tests for lineage: write record, query, ancestor trace (Phase 3.4)."""

from __future__ import annotations

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


class TestLineageStore:
    """Verify SQLite-backed LineageStore."""

    def test_write_and_query(self) -> None:
        store = LineageStore()  # in-memory
        record = _make_record("block_A", ["hash_in_1"], ["hash_out_1"])
        store.write(record)

        results = store.query(block_id="block_A")
        assert len(results) == 1
        assert results[0].block_id == "block_A"
        assert results[0].input_hashes == ["hash_in_1"]
        assert results[0].output_hashes == ["hash_out_1"]

    def test_query_all(self) -> None:
        store = LineageStore()
        store.write(_make_record("A", ["h1"], ["h2"]))
        store.write(_make_record("B", ["h2"], ["h3"]))
        results = store.query()
        assert len(results) == 2

    def test_query_nonexistent_block(self) -> None:
        store = LineageStore()
        store.write(_make_record("A", ["h1"], ["h2"]))
        results = store.query(block_id="nonexistent")
        assert len(results) == 0

    def test_write_with_environment(self) -> None:
        store = LineageStore()
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
        store = LineageStore()
        store.write(_make_record("A", ["raw"], ["h1"], timestamp="2026-01-01T00:00:00"))
        store.write(_make_record("B", ["h1"], ["h2"], timestamp="2026-01-01T00:01:00"))
        store.write(_make_record("C", ["h2"], ["h3"], timestamp="2026-01-01T00:02:00"))

        ancestors = store.ancestors("h3")
        block_ids = [r.block_id for r in ancestors]
        assert "C" in block_ids
        assert "B" in block_ids
        assert "A" in block_ids

    def test_ancestors_no_match(self) -> None:
        store = LineageStore()
        store.write(_make_record("A", ["h1"], ["h2"]))
        ancestors = store.ancestors("nonexistent")
        assert ancestors == []


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
