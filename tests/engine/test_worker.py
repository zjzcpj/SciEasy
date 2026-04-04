"""Tests for worker.py subprocess entry point — ADR-017."""

from __future__ import annotations

from unittest.mock import MagicMock

from scieasy.engine.runners.worker import (
    main,
    reconstruct_inputs,
    serialise_outputs,
)

# ---------------------------------------------------------------------------
# reconstruct_inputs
# ---------------------------------------------------------------------------


class TestReconstructInputs:
    def test_returns_inputs_from_payload(self) -> None:
        payload = {"inputs": {"port_a": "ref1", "port_b": "ref2"}}
        result = reconstruct_inputs(payload)
        assert result == {"port_a": "ref1", "port_b": "ref2"}

    def test_returns_empty_dict_when_no_inputs(self) -> None:
        payload = {"block_class": "mod.Block"}
        result = reconstruct_inputs(payload)
        assert result == {}


# ---------------------------------------------------------------------------
# serialise_outputs
# ---------------------------------------------------------------------------


class TestSerialiseOutputs:
    def test_serialises_plain_values_as_strings(self) -> None:
        outputs = {"result": 42, "name": "hello"}
        result = serialise_outputs(outputs, "")
        assert result == {"result": "42", "name": "hello"}

    def test_serialises_storage_ref(self) -> None:
        mock_obj = MagicMock()
        mock_obj.storage_ref.backend = "zarr"
        mock_obj.storage_ref.path = "/data/output.zarr"
        mock_obj.storage_ref.format = "zarr"

        outputs = {"image": mock_obj}
        result = serialise_outputs(outputs, "/output")
        assert result == {
            "image": {
                "backend": "zarr",
                "path": "/data/output.zarr",
                "format": "zarr",
            }
        }

    def test_serialises_value_without_storage_ref_attribute(self) -> None:
        outputs = {"count": 5}
        result = serialise_outputs(outputs, "")
        assert result == {"count": "5"}

    def test_serialises_value_with_none_storage_ref(self) -> None:
        mock_obj = MagicMock()
        mock_obj.storage_ref = None

        outputs = {"data": mock_obj}
        result = serialise_outputs(outputs, "")
        # Should fall back to str()
        assert "data" in result

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
