"""Tests for input serialization before subprocess transport (issue #621).

Verifies that ``serialise_inputs()`` in ``local.py`` correctly auto-flushes
in-memory DataObject instances and converts them to wire-format dicts that
``worker.reconstruct_inputs()`` can round-trip.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from scieasy.core.types.array import Array


def _make_array(data: np.ndarray, axes: list[str] | None = None) -> Array:
    """Create an in-memory Array with _data set (no storage_ref)."""

    arr = Array(axes=axes or ["y", "x"])
    arr._data = data  # type: ignore[attr-defined]
    return arr


class TestSerialiseInputs:
    """Test serialise_inputs() for the input serialization path."""

    def test_in_memory_array_becomes_wire_format(self, tmp_path: Path) -> None:
        """An in-memory Array (no storage_ref) should be auto-flushed and
        converted to wire format with backend/path/metadata keys."""
        from scieasy.engine.runners.local import serialise_inputs

        arr = _make_array(np.zeros((10, 10), dtype=np.uint8))
        assert arr.storage_ref is None

        result = serialise_inputs({"image": arr}, str(tmp_path))

        wire = result["image"]
        assert isinstance(wire, dict)
        assert "backend" in wire
        assert "path" in wire
        assert "metadata" in wire
        assert wire["backend"] is not None
        assert wire["path"] is not None
        # type_chain should include Array
        assert "Array" in wire["metadata"]["type_chain"]

    def test_wire_format_round_trips_through_reconstruct(self, tmp_path: Path) -> None:
        """Wire format from serialise_inputs should reconstruct via worker."""
        from scieasy.core.types.array import Array
        from scieasy.engine.runners.local import serialise_inputs
        from scieasy.engine.runners.worker import reconstruct_inputs

        arr = _make_array(np.zeros((5, 5), dtype=np.float32))
        wire_inputs = serialise_inputs({"image": arr}, str(tmp_path))

        # Wrap in payload envelope as worker expects
        payload = {"inputs": wire_inputs}
        reconstructed = reconstruct_inputs(payload)

        assert "image" in reconstructed
        recon_arr = reconstructed["image"]
        assert isinstance(recon_arr, Array)
        assert recon_arr.storage_ref is not None

    def test_scalar_inputs_pass_through(self, tmp_path: Path) -> None:
        """Scalars (str, int, float, bool, None, list, dict) pass through."""
        from scieasy.engine.runners.local import serialise_inputs

        inputs = {
            "threshold": 0.5,
            "name": "test",
            "count": 42,
            "flag": True,
            "items": [1, 2, 3],
            "options": {"a": 1},
            "empty": None,
        }
        result = serialise_inputs(inputs, str(tmp_path))
        assert result == inputs

    def test_already_wire_format_passes_through(self, tmp_path: Path) -> None:
        """Dicts already in wire format (with backend/path) pass through."""
        from scieasy.engine.runners.local import serialise_inputs

        wire = {
            "backend": "zarr",
            "path": "/data/existing.zarr",
            "metadata": {"type_chain": ["DataObject", "Array"]},
        }
        result = serialise_inputs({"image": wire}, str(tmp_path))
        assert result["image"] is wire

    def test_collection_of_arrays(self, tmp_path: Path) -> None:
        """A Collection of in-memory Arrays should be serialized recursively."""
        from scieasy.core.types.array import Array
        from scieasy.core.types.collection import Collection
        from scieasy.engine.runners.local import serialise_inputs

        arrays = [
            _make_array(np.zeros((3, 3), dtype=np.uint8)),
            _make_array(np.ones((3, 3), dtype=np.uint8)),
        ]
        coll = Collection(arrays, item_type=Array)

        result = serialise_inputs({"images": coll}, str(tmp_path))

        wire = result["images"]
        assert wire["_collection"] is True
        assert wire["item_type"] == "Array"
        assert len(wire["items"]) == 2
        for item in wire["items"]:
            assert "backend" in item
            assert "path" in item

    def test_flush_context_restored_after_call(self, tmp_path: Path) -> None:
        """The flush context output_dir should be restored after the call."""
        from scieasy.core.storage.flush_context import clear, get_output_dir, set_output_dir
        from scieasy.engine.runners.local import serialise_inputs

        # Set a prior context
        set_output_dir("/previous/dir")
        serialise_inputs({}, str(tmp_path))
        assert get_output_dir() == "/previous/dir"

        # Clean up
        clear()
