"""Tests for checkpoint serialization and CheckpointManager — ADR-018."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from scieasy.engine.checkpoint import (
    CheckpointManager,
    WorkflowCheckpoint,
    load_checkpoint,
    save_checkpoint,
    serialize_intermediate_refs,
)
from scieasy.engine.events import (
    BLOCK_CANCELLED,
    BLOCK_DONE,
    BLOCK_ERROR,
    BLOCK_SKIPPED,
    EventBus,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TS = datetime(2026, 4, 4, 12, 0, 0)


def _make_checkpoint(**overrides: object) -> WorkflowCheckpoint:
    """Create a minimal checkpoint, applying *overrides* on top."""
    defaults: dict[str, object] = {
        "workflow_id": "wf-001",
        "timestamp": _TS,
        "block_states": {"A": "DONE", "B": "READY"},
    }
    defaults.update(overrides)
    return WorkflowCheckpoint(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------


class TestSaveLoadRoundtrip:
    """save_checkpoint -> load_checkpoint preserves all fields."""

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        cp = _make_checkpoint(
            pending_block="B",
            config_snapshot={"timeout": 30},
            intermediate_refs={"A": "/data/result_a.zarr"},
        )
        path = tmp_path / "cp.json"
        save_checkpoint(cp, path)

        restored = load_checkpoint(path)

        assert restored.workflow_id == cp.workflow_id
        assert restored.timestamp == cp.timestamp
        assert restored.block_states == cp.block_states
        assert restored.pending_block == cp.pending_block
        assert restored.config_snapshot == cp.config_snapshot
        assert restored.intermediate_refs == cp.intermediate_refs
        assert restored.skip_reasons == cp.skip_reasons

    def test_checkpoint_with_skip_reasons(self, tmp_path: Path) -> None:
        """CANCELLED and SKIPPED states plus skip reasons are preserved."""
        cp = _make_checkpoint(
            block_states={
                "A": "DONE",
                "B": "CANCELLED",
                "C": "SKIPPED",
            },
            skip_reasons={
                "B": "user requested cancellation",
                "C": "upstream B was cancelled",
            },
        )
        path = tmp_path / "cp_skip.json"
        save_checkpoint(cp, path)

        restored = load_checkpoint(path)

        assert restored.block_states["B"] == "CANCELLED"
        assert restored.block_states["C"] == "SKIPPED"
        assert restored.skip_reasons["B"] == "user requested cancellation"
        assert restored.skip_reasons["C"] == "upstream B was cancelled"

    def test_checkpoint_with_intermediate_refs(self, tmp_path: Path) -> None:
        """Intermediate data references survive serialization."""
        refs = {
            "block_A": "/storage/run-42/block_A.zarr",
            "block_B": {"uri": "s3://bucket/block_B.parquet", "size": 1024},
        }
        cp = _make_checkpoint(intermediate_refs=refs)
        path = tmp_path / "cp_refs.json"
        save_checkpoint(cp, path)

        restored = load_checkpoint(path)

        assert restored.intermediate_refs["block_A"] == refs["block_A"]
        assert restored.intermediate_refs["block_B"] == refs["block_B"]

    def test_save_creates_parent_directories(self, tmp_path: Path) -> None:
        """save_checkpoint creates missing parent directories."""
        path = tmp_path / "deep" / "nested" / "cp.json"
        save_checkpoint(_make_checkpoint(), path)

        assert path.exists()
        restored = load_checkpoint(path)
        assert restored.workflow_id == "wf-001"


# ---------------------------------------------------------------------------
# CheckpointManager
# ---------------------------------------------------------------------------


class TestCheckpointManager:
    """Tests for the CheckpointManager class."""

    def test_checkpoint_manager_save_load(self, tmp_path: Path) -> None:
        """Manager.save / Manager.load cycle works and updates latest."""
        mgr = CheckpointManager(tmp_path / "checkpoints")
        cp = _make_checkpoint()

        saved_path = mgr.save(cp)
        assert saved_path.exists()
        assert mgr.latest is cp

        loaded = mgr.load("wf-001")
        assert loaded is not None
        assert loaded.workflow_id == cp.workflow_id
        assert loaded.timestamp == cp.timestamp
        assert loaded.block_states == cp.block_states

    def test_load_nonexistent(self, tmp_path: Path) -> None:
        """Loading a checkpoint for an unknown workflow_id returns None."""
        mgr = CheckpointManager(tmp_path / "checkpoints")
        assert mgr.load("does-not-exist") is None

    def test_checkpoint_manager_auto_subscribe(self) -> None:
        """When given an EventBus, CheckpointManager subscribes to terminal events."""
        bus = EventBus()
        # Before manager creation, no subscribers
        assert len(bus._subscribers[BLOCK_DONE]) == 0

        mgr = CheckpointManager("/tmp/unused", event_bus=bus)

        # After creation, exactly one subscriber for each terminal event
        assert len(bus._subscribers[BLOCK_DONE]) == 1
        assert len(bus._subscribers[BLOCK_ERROR]) == 1
        assert len(bus._subscribers[BLOCK_CANCELLED]) == 1
        assert len(bus._subscribers[BLOCK_SKIPPED]) == 1

        # Verify the callbacks point to the manager's method
        assert bus._subscribers[BLOCK_DONE][0] == mgr._on_state_change
        assert bus._subscribers[BLOCK_ERROR][0] == mgr._on_state_change
        assert bus._subscribers[BLOCK_CANCELLED][0] == mgr._on_state_change
        assert bus._subscribers[BLOCK_SKIPPED][0] == mgr._on_state_change

    def test_latest_initially_none(self, tmp_path: Path) -> None:
        """CheckpointManager.latest is None before any save."""
        mgr = CheckpointManager(tmp_path / "checkpoints")
        assert mgr.latest is None

    def test_manager_creates_checkpoint_dir(self, tmp_path: Path) -> None:
        """CheckpointManager creates the checkpoint directory if absent."""
        target = tmp_path / "new_dir" / "checkpoints"
        assert not target.exists()
        CheckpointManager(target)
        assert target.exists()
        assert target.is_dir()


# ---------------------------------------------------------------------------
# intermediate_refs serialisation (Collection-aware)
# ---------------------------------------------------------------------------


class TestIntermediateRefsSerialization:
    """Tests for serialize_intermediate_refs -- Collection support (#62)."""

    def test_serialize_collection_output(self) -> None:
        """Collection outputs preserve structure instead of str()."""
        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.types.array import Image
        from scieasy.core.types.collection import Collection

        img = Image(shape=(10, 10))
        img.storage_ref = StorageReference(backend="zarr", path="/tmp/test.zarr")
        collection = Collection([img], item_type=Image)

        block_outputs = {"block_a": {"result": collection}}
        serialized = serialize_intermediate_refs(block_outputs)

        ref_data = serialized["block_a"]["result"]
        assert ref_data["_collection"] is True
        assert ref_data["item_type"] == "Image"
        assert len(ref_data["items"]) == 1
        assert ref_data["items"][0]["backend"] == "zarr"

    def test_serialize_plain_value_passthrough(self) -> None:
        """Scalar values pass through unchanged."""
        block_outputs = {"block_a": {"count": 42, "name": "test"}}
        serialized = serialize_intermediate_refs(block_outputs)
        assert serialized["block_a"]["count"] == 42
        assert serialized["block_a"]["name"] == "test"

    def test_serialize_storage_ref_output(self) -> None:
        """DataObject with storage_ref serializes to ref dict."""
        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.types.array import Image

        img = Image(shape=(10, 10))
        img.storage_ref = StorageReference(backend="zarr", path="/tmp/img.zarr")

        block_outputs = {"block_a": {"image": img}}
        serialized = serialize_intermediate_refs(block_outputs)
        assert serialized["block_a"]["image"]["backend"] == "zarr"

    def test_round_trip_json_serializable(self) -> None:
        """Serialized intermediate_refs can be JSON-serialized."""
        import json

        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.types.array import Image
        from scieasy.core.types.collection import Collection

        img = Image(shape=(5, 5))
        img.storage_ref = StorageReference(backend="zarr", path="/tmp/test.zarr")
        collection = Collection([img], item_type=Image)

        block_outputs = {"block_a": {"result": collection}}
        serialized = serialize_intermediate_refs(block_outputs)
        json_str = json.dumps(serialized)
        restored = json.loads(json_str)
        assert restored["block_a"]["result"]["_collection"] is True

    def test_serialize_collection_item_without_storage_ref(self) -> None:
        """Collection item without storage_ref falls back to _value string."""
        from scieasy.core.types.array import Image
        from scieasy.core.types.collection import Collection

        img = Image(shape=(3, 3))
        # No storage_ref set
        collection = Collection([img], item_type=Image)

        block_outputs = {"block_a": {"result": collection}}
        serialized = serialize_intermediate_refs(block_outputs)

        ref_data = serialized["block_a"]["result"]
        assert ref_data["_collection"] is True
        assert "_value" in ref_data["items"][0]

    def test_serialize_non_dict_output(self) -> None:
        """Non-dict block output is serialized via _serialize_value."""
        block_outputs = {"block_a": "simple_string"}
        serialized = serialize_intermediate_refs(block_outputs)
        assert serialized["block_a"] == "simple_string"
