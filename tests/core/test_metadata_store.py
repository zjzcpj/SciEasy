"""Unit tests for MetadataStore (ADR-032).

Covers: put/get round-trip, put_wire/get_wire round-trip,
get_by_storage_path, ancestors, descendants, list_by_type,
list_by_workflow, vacuum, upsert, missing object_id, empty db,
WAL mode, schema version, close, put_wire_if_missing, delete.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scieasy.core.metadata_store import MetadataStore, get_metadata_store, set_metadata_store

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_wire_dict(
    *,
    object_id: str = "obj-001",
    type_chain: list[str] | None = None,
    derived_from: str | None = None,
    created_at: str = "2026-04-12T00:00:00+00:00",
    backend: str | None = "zarr",
    path: str | None = "/data/zarr/test.zarr",
    workflow_id: str | None = None,
    block_id: str | None = None,
) -> dict:
    if type_chain is None:
        type_chain = ["DataObject", "Array", "Image"]
    return {
        "backend": backend,
        "path": path,
        "format": None,
        "metadata": {
            "type_chain": type_chain,
            "framework": {
                "object_id": object_id,
                "derived_from": derived_from,
                "created_at": created_at,
                "source": "",
                "lineage_id": None,
            },
            "meta": None,
            "user": {},
        },
    }


@pytest.fixture()
def store(tmp_path: Path) -> MetadataStore:
    """Create a fresh MetadataStore backed by a temp directory."""
    db_path = tmp_path / "metadata.db"
    s = MetadataStore(db_path)
    yield s
    s.close()


# ---------------------------------------------------------------------------
# Phase 1a: Core MetadataStore class tests
# ---------------------------------------------------------------------------


class TestPutWireGetWireRoundTrip:
    """put_wire() + get_wire() round-trip preserves the exact wire dict."""

    def test_basic_round_trip(self, store: MetadataStore) -> None:
        wire = _make_wire_dict()
        store.put_wire(wire)
        result = store.get_wire("obj-001")
        assert result == wire

    def test_missing_returns_none(self, store: MetadataStore) -> None:
        assert store.get_wire("nonexistent") is None


class TestPutGetRoundTrip:
    """put() via DataObject + get() reconstructs a typed DataObject."""

    def test_round_trip(self, store: MetadataStore) -> None:
        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.types.base import DataObject

        obj = DataObject(storage_ref=StorageReference(backend="zarr", path="/tmp/test.zarr"))
        store.put(obj)
        restored = store.get(obj.framework.object_id)
        assert restored is not None
        assert restored.framework.object_id == obj.framework.object_id

    def test_get_missing_returns_none(self, store: MetadataStore) -> None:
        assert store.get("nonexistent") is None


class TestGetByStoragePath:
    def test_lookup_by_path(self, store: MetadataStore) -> None:
        wire = _make_wire_dict(path="/data/zarr/my_array.zarr", type_chain=["DataObject", "Array"])
        store.put_wire(wire)
        result = store.get_by_storage_path("/data/zarr/my_array.zarr")
        assert result is not None
        assert result.framework.object_id == "obj-001"

    def test_missing_path_returns_none(self, store: MetadataStore) -> None:
        assert store.get_by_storage_path("/nonexistent") is None


class TestAncestors:
    def test_single_lineage_chain(self, store: MetadataStore) -> None:
        # grandparent -> parent -> child
        store.put_wire(_make_wire_dict(object_id="gp", derived_from=None))
        store.put_wire(_make_wire_dict(object_id="parent", derived_from="gp"))
        store.put_wire(_make_wire_dict(object_id="child", derived_from="parent"))

        chain = store.ancestors("child")
        ids = [r["object_id"] for r in chain]
        assert ids == ["child", "parent", "gp"]

    def test_no_ancestors(self, store: MetadataStore) -> None:
        store.put_wire(_make_wire_dict(object_id="root", derived_from=None))
        chain = store.ancestors("root")
        assert len(chain) == 1
        assert chain[0]["object_id"] == "root"

    def test_nonexistent_object(self, store: MetadataStore) -> None:
        chain = store.ancestors("nonexistent")
        assert chain == []


class TestDescendants:
    def test_single_descendant_chain(self, store: MetadataStore) -> None:
        store.put_wire(_make_wire_dict(object_id="root", derived_from=None))
        store.put_wire(_make_wire_dict(object_id="child1", derived_from="root"))
        store.put_wire(_make_wire_dict(object_id="child2", derived_from="root"))

        desc = store.descendants("root")
        ids = {r["object_id"] for r in desc}
        assert ids == {"root", "child1", "child2"}

    def test_nonexistent_object(self, store: MetadataStore) -> None:
        desc = store.descendants("nonexistent")
        assert desc == []


class TestListByType:
    def test_filter_by_type(self, store: MetadataStore) -> None:
        store.put_wire(_make_wire_dict(object_id="img1", type_chain=["DataObject", "Array", "Image"]))
        store.put_wire(_make_wire_dict(object_id="df1", type_chain=["DataObject", "DataFrame"]))
        store.put_wire(_make_wire_dict(object_id="img2", type_chain=["DataObject", "Array", "Image"]))

        images = store.list_by_type("Image")
        assert len(images) == 2
        ids = {r["object_id"] for r in images}
        assert ids == {"img1", "img2"}

    def test_no_results(self, store: MetadataStore) -> None:
        assert store.list_by_type("NonexistentType") == []


class TestListByWorkflow:
    def test_filter_by_workflow(self, store: MetadataStore) -> None:
        store.put_wire(_make_wire_dict(object_id="a"), workflow_id="wf-1", block_id="b1")
        store.put_wire(_make_wire_dict(object_id="b"), workflow_id="wf-1", block_id="b2")
        store.put_wire(_make_wire_dict(object_id="c"), workflow_id="wf-2", block_id="b1")

        results = store.list_by_workflow("wf-1")
        assert len(results) == 2
        ids = {r["object_id"] for r in results}
        assert ids == {"a", "b"}

    def test_no_results(self, store: MetadataStore) -> None:
        assert store.list_by_workflow("nonexistent") == []


class TestDelete:
    def test_delete_existing(self, store: MetadataStore) -> None:
        store.put_wire(_make_wire_dict(object_id="to-delete"))
        assert store.get_wire("to-delete") is not None
        store.delete("to-delete")
        assert store.get_wire("to-delete") is None

    def test_delete_nonexistent_is_noop(self, store: MetadataStore) -> None:
        store.delete("nonexistent")  # Should not raise


class TestVacuum:
    def test_removes_orphan_entries(self, store: MetadataStore) -> None:
        store.put_wire(_make_wire_dict(object_id="alive", path="/data/alive.zarr"))
        store.put_wire(_make_wire_dict(object_id="orphan", path="/data/orphan.zarr"))
        store.put_wire(_make_wire_dict(object_id="no-path", path=None, backend=None))

        removed = store.vacuum(existing_paths={"/data/alive.zarr"})
        assert removed == 1
        assert store.get_wire("alive") is not None
        assert store.get_wire("orphan") is None
        # Entries with no storage_path are not vacuumed
        assert store.get_wire("no-path") is not None


class TestUpsert:
    def test_duplicate_object_id_replaces(self, store: MetadataStore) -> None:
        wire1 = _make_wire_dict(object_id="dup", path="/old.zarr")
        wire2 = _make_wire_dict(object_id="dup", path="/new.zarr")
        store.put_wire(wire1)
        store.put_wire(wire2)
        result = store.get_wire("dup")
        assert result is not None
        assert result["path"] == "/new.zarr"


class TestPutWireIfMissing:
    def test_inserts_when_absent(self, store: MetadataStore) -> None:
        wire = _make_wire_dict(object_id="new-obj")
        store.put_wire_if_missing(wire)
        assert store.get_wire("new-obj") is not None

    def test_skips_when_present(self, store: MetadataStore) -> None:
        wire1 = _make_wire_dict(object_id="existing", path="/old.zarr")
        wire2 = _make_wire_dict(object_id="existing", path="/new.zarr")
        store.put_wire(wire1)
        store.put_wire_if_missing(wire2)
        result = store.get_wire("existing")
        assert result is not None
        # Original value preserved, not overwritten
        assert result["path"] == "/old.zarr"


class TestEdgeCases:
    def test_missing_object_id_silently_ignored(self, store: MetadataStore) -> None:
        wire = {"backend": "zarr", "path": "/test", "format": None, "metadata": {"framework": {}}}
        store.put_wire(wire)  # No crash
        # Nothing stored
        row = store._conn.execute("SELECT COUNT(*) FROM data_objects").fetchone()
        assert row[0] == 0

    def test_missing_metadata_dict_silently_ignored(self, store: MetadataStore) -> None:
        store.put_wire({"backend": "zarr", "path": "/test"})
        row = store._conn.execute("SELECT COUNT(*) FROM data_objects").fetchone()
        assert row[0] == 0

    def test_empty_database_queries(self, store: MetadataStore) -> None:
        assert store.get("x") is None
        assert store.get_wire("x") is None
        assert store.get_by_storage_path("/x") is None
        assert store.ancestors("x") == []
        assert store.descendants("x") == []
        assert store.list_by_type("Image") == []
        assert store.list_by_workflow("wf") == []


class TestWALMode:
    def test_wal_mode_enabled(self, store: MetadataStore) -> None:
        mode = store._conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert mode.lower() == "wal"


class TestSchemaVersion:
    def test_user_version_set(self, store: MetadataStore) -> None:
        version = store._conn.execute("PRAGMA user_version;").fetchone()[0]
        assert version == 1


class TestSingleton:
    def test_default_is_none(self) -> None:
        # Save and restore the global to avoid test pollution
        original = get_metadata_store()
        try:
            set_metadata_store(None)
            assert get_metadata_store() is None
        finally:
            set_metadata_store(original)

    def test_set_and_get(self, store: MetadataStore) -> None:
        original = get_metadata_store()
        try:
            set_metadata_store(store)
            assert get_metadata_store() is store
        finally:
            set_metadata_store(original)


class TestBookkeepingColumns:
    """Verify workflow_id, block_id, port_name are stored and queryable."""

    def test_bookkeeping_populated(self, store: MetadataStore) -> None:
        wire = _make_wire_dict(object_id="bk-1")
        store.put_wire(wire, workflow_id="wf-A", block_id="blk-1", port_name="output")

        row = store._conn.execute(
            "SELECT workflow_id, block_id, port_name FROM data_objects WHERE object_id = ?",
            ("bk-1",),
        ).fetchone()
        assert row == ("wf-A", "blk-1", "output")


class TestRepr:
    def test_repr(self, store: MetadataStore) -> None:
        r = repr(store)
        assert "MetadataStore" in r
        assert "metadata.db" in r
