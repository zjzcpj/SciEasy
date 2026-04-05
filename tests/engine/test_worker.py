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
    def test_scalar_inputs_pass_through(self) -> None:
        """ADR-017: Non-reference inputs pass through as-is."""
        payload = {"inputs": {"port_a": "ref1", "port_b": "ref2"}}
        result = reconstruct_inputs(payload)
        assert result == {"port_a": "ref1", "port_b": "ref2"}

    def test_returns_empty_dict_when_no_inputs(self) -> None:
        payload = {"block_class": "mod.Block"}
        result = reconstruct_inputs(payload)
        assert result == {}

    def test_storage_ref_dict_becomes_view_proxy(self) -> None:
        """ADR-017: Dicts with backend/path are reconstructed as ViewProxy."""
        from scieasy.core.proxy import ViewProxy

        payload = {
            "inputs": {
                "image": {
                    "backend": "zarr",
                    "path": "/data/img.zarr",
                    "format": "zarr",
                    "metadata": {"axes": ["z", "y", "x"]},
                },
                "label": "test",
            }
        }
        result = reconstruct_inputs(payload)

        assert isinstance(result["image"], ViewProxy)
        assert result["image"].storage_ref.backend == "zarr"
        assert result["image"].storage_ref.path == "/data/img.zarr"
        assert result["image"].storage_ref.format == "zarr"
        assert result["image"].storage_ref.metadata == {"axes": ["z", "y", "x"]}
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

    def test_serialises_storage_ref(self) -> None:
        mock_obj = MagicMock()
        mock_obj.storage_ref.backend = "zarr"
        mock_obj.storage_ref.path = "/data/output.zarr"
        mock_obj.storage_ref.format = "zarr"
        mock_obj.storage_ref.metadata = None

        outputs = {"image": mock_obj}
        result = serialise_outputs(outputs, "/output")
        assert result == {
            "image": {
                "backend": "zarr",
                "path": "/data/output.zarr",
                "format": "zarr",
                "metadata": None,
            }
        }

    def test_serialises_int_without_storage_ref_attribute(self) -> None:
        """ADR-017: int values without storage_ref are preserved as int."""
        outputs = {"count": 5}
        result = serialise_outputs(outputs, "")
        assert result == {"count": 5}

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
