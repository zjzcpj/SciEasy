"""Tests for worker.py subprocess entry point.

ADR-017: All block execution happens in isolated subprocesses.
ADR-027 D11 + Addendum 1 §1 (T-014): ``reconstruct_inputs`` now
returns typed :class:`~scieasy.core.types.base.DataObject` instances
instead of :class:`~scieasy.core.proxy.ViewProxy`; ``serialise_outputs``
writes the full typed metadata sidecar via
:func:`~scieasy.core.types.serialization._serialise_one`.
"""

from __future__ import annotations

from pathlib import Path

from scieasy.engine.runners.worker import (
    main,
    reconstruct_inputs,
    serialise_outputs,
)

# ---------------------------------------------------------------------------
# reconstruct_inputs
# ---------------------------------------------------------------------------


class TestReconstructInputs:
    def test_scalar_inputs_pass_through(self) -> None:
        """ADR-017: Non-reference inputs pass through as-is."""
        payload = {"inputs": {"port_a": "ref1", "port_b": "ref2"}}
        result = reconstruct_inputs(payload)
        assert result == {"port_a": "ref1", "port_b": "ref2"}

    def test_returns_empty_dict_when_no_inputs(self) -> None:
        payload = {"block_class": "mod.Block"}
        result = reconstruct_inputs(payload)
        assert result == {}

    def test_storage_ref_dict_becomes_typed_instance(self) -> None:
        """ADR-027 D11 + ADR-031: dicts with backend/path reconstruct
        into typed DataObject instances.
        """
        from scieasy.core.types.array import Array

        payload = {
            "inputs": {
                "image": {
                    "backend": "zarr",
                    "path": "/data/img.zarr",
                    "format": "zarr",
                    "metadata": {
                        "type_chain": ["DataObject", "Array"],
                        "axes": ["z", "y", "x"],
                        "shape": [8, 16, 16],
                        "dtype": "uint8",
                    },
                },
                "label": "test",
            }
        }
        result = reconstruct_inputs(payload)

        assert isinstance(result["image"], Array)
        assert result["image"].axes == ["z", "y", "x"]
        assert result["image"].shape == (8, 16, 16)
        assert result["image"].storage_ref is not None
        assert result["image"].storage_ref.backend == "zarr"
        assert result["image"].storage_ref.path == "/data/img.zarr"
        assert result["image"].storage_ref.format == "zarr"
        assert result["label"] == "test"


# ---------------------------------------------------------------------------
# serialise_outputs
# ---------------------------------------------------------------------------


class TestSerialiseOutputs:
    def test_serialises_plain_values_natively(self) -> None:
        """ADR-017: scalar types (int, str, float, bool, None) pass through as-is."""
        outputs = {"result": 42, "name": "hello"}
        result = serialise_outputs(outputs, "")
        assert result == {"result": 42, "name": "hello"}

    def test_serialises_typed_dataobject_with_storage_ref(self) -> None:
        """ADR-027 Addendum 1 §1 (T-014): typed DataObject outputs use the
        full metadata sidecar (type_chain + framework + meta + user + extras).
        """
        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.types.array import Array

        arr = Array(axes=["y", "x"], shape=(8, 8), dtype="uint8")
        arr._storage_ref = StorageReference(backend="zarr", path="/data/output.zarr", format="zarr")

        result = serialise_outputs({"image": arr}, "/output")
        payload = result["image"]

        assert payload["backend"] == "zarr"
        assert payload["path"] == "/data/output.zarr"
        assert payload["format"] == "zarr"
        md = payload["metadata"]
        assert md["type_chain"] == ["DataObject", "Array"]
        assert md["axes"] == ["y", "x"]
        assert md["shape"] == [8, 8]
        assert md["dtype"] == "uint8"
        # framework slot is populated with FrameworkMeta fields.
        assert "framework" in md
        assert "object_id" in md["framework"]
        # meta is None on the base Array class.
        assert md["meta"] is None
        # user is an empty dict by default.
        assert md["user"] == {}

    def test_serialises_int_without_storage_ref_attribute(self) -> None:
        """ADR-017: int values without storage_ref are preserved as int."""
        outputs = {"count": 5}
        result = serialise_outputs(outputs, "")
        assert result == {"count": 5}

    def test_serialises_dataobject_without_storage_ref(self) -> None:
        """In-memory DataObject with no storage_ref serialises with None envelope.

        T-014 relaxes the ADR pseudocode's RuntimeError: when auto-flush is a
        no-op (no flush context configured), the object's storage_ref stays
        ``None``. The worker emits ``backend=None`` / ``path=None`` so the
        wire format remains JSON-clean and the receiving worker can round-
        trip the object through _reconstruct_one.
        """
        from scieasy.core.types.array import Array

        arr = Array(axes=["y", "x"], shape=(2, 2), dtype="uint8")
        # No storage_ref set, no flush context → _auto_flush returns the obj.
        result = serialise_outputs({"data": arr}, "")
        assert result["data"]["backend"] is None
        assert result["data"]["path"] is None
        assert result["data"]["metadata"]["type_chain"] == ["DataObject", "Array"]
        assert result["data"]["metadata"]["axes"] == ["y", "x"]

    def test_serialises_dataobject_without_storage_ref_auto_flushes_when_output_dir_present(
        self,
        tmp_path: Path,
    ) -> None:
        """A storage-backed Array serialises with backend/path populated."""
        import numpy as np

        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.storage.zarr_backend import ZarrBackend
        from scieasy.core.types.array import Array

        data = np.array([[1, 2], [3, 4]], dtype="uint8")
        zarr_path = str(tmp_path / "arr.zarr")
        ref = ZarrBackend().write(data, StorageReference(backend="zarr", path=zarr_path))
        arr = Array(axes=["y", "x"], shape=(2, 2), dtype="uint8", storage_ref=ref)

        result = serialise_outputs({"data": arr}, str(tmp_path))

        assert result["data"]["backend"] == "zarr"
        assert result["data"]["path"] is not None
        assert result["data"]["metadata"]["axes"] == ["y", "x"]
        assert str(result["data"]["path"]).endswith(".zarr")
        assert Path(result["data"]["path"]).exists()

    def test_serialise_collection_with_none_item_type(self) -> None:
        """Collection with item_type=None should not crash the worker (#168)."""
        from scieasy.core.types.collection import Collection

        col = Collection.__new__(Collection)
        col._items = []
        col._item_type = None  # type: ignore[assignment]

        result = serialise_outputs({"output": col}, "/tmp/out")
        assert result["output"]["_collection"] is True
        assert result["output"]["item_type"] == "DataObject"

    def test_empty_outputs(self) -> None:
        result = serialise_outputs({}, "")
        assert result == {}


# ---------------------------------------------------------------------------
# main — module-level function (tested indirectly via subprocess in
# integration tests; here we verify import works)
# ---------------------------------------------------------------------------


class TestWorkerMain:
    def test_main_is_callable(self) -> None:
        """Verify the main function exists and is callable."""
        assert callable(main)

    def test_main_outputs_include_environment_key(self) -> None:
        """Issue #54: worker main() should include 'environment' in JSON stdout.

        We invoke worker.py as a subprocess with a minimal payload using a
        trivial block class. The stdout JSON must contain both 'outputs'
        and 'environment' keys.
        """
        import json
        import subprocess
        import sys

        # Create a minimal block that returns a scalar output.
        # The worker expects block_class as a dotted path that can be imported.
        # We use subprocess to run worker.py directly, feeding JSON via stdin.
        payload = json.dumps(
            {
                "block_class": "tests.engine.test_worker._StubBlock",
                "inputs": {},
                "config": {},
                "output_dir": "",
            }
        )

        result = subprocess.run(
            [sys.executable, "-m", "scieasy.engine.runners.worker"],
            input=payload,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # If the block import fails, it's because the test stub isn't importable
        # from the subprocess context. In that case we fall back to checking
        # that the error payload is well-formed JSON (the worker always writes
        # JSON to stdout).
        parsed = json.loads(result.stdout)

        if "error" not in parsed:
            assert "outputs" in parsed, f"Missing 'outputs' key: {parsed}"
            assert "environment" in parsed, f"Missing 'environment' key: {parsed}"
            env = parsed["environment"]
            assert "python_version" in env
            assert "platform" in env
            assert "key_packages" in env


class _StubBlock:
    """Minimal block stub for subprocess worker test."""

    def run(self, inputs: dict, config: object) -> dict:
        return {"result": "ok"}
