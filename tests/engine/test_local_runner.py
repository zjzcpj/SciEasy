"""Tests for LocalRunner and subprocess pipeline — ADR-017."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from scieasy.engine.events import EventBus
from scieasy.engine.runners.local import LocalRunner
from scieasy.engine.runners.process_handle import (
    ProcessExitInfo,
    ProcessHandle,
    ProcessRegistry,
)
from scieasy.engine.runners.worker import reconstruct_inputs, serialise_outputs

# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestLocalRunnerConstruction:
    def test_default_construction(self) -> None:
        runner = LocalRunner()
        assert runner._event_bus is None
        assert runner._registry is None

    def test_construction_with_dependencies(self) -> None:
        bus = EventBus()
        registry = ProcessRegistry()
        runner = LocalRunner(event_bus=bus, registry=registry)
        assert runner._event_bus is bus
        assert runner._registry is registry


# ---------------------------------------------------------------------------
# check_status
# ---------------------------------------------------------------------------


class TestLocalRunnerCheckStatus:
    def _make_handle(self, block_id: str, alive: bool = True) -> ProcessHandle:
        mock_ops = MagicMock()
        mock_ops.is_alive.return_value = alive

        handle = ProcessHandle(
            block_id=block_id,
            pid=12345,
            start_time=datetime.now(),
            resource_request=MagicMock(),
        )
        handle._platform_ops = mock_ops
        return handle

    def test_unknown_when_no_registry(self) -> None:
        runner = LocalRunner(event_bus=None, registry=None)
        result = asyncio.run(runner.check_status("any-id"))
        assert result == "unknown"

    def test_unknown_when_handle_not_found(self) -> None:
        registry = ProcessRegistry()
        runner = LocalRunner(event_bus=None, registry=registry)
        result = asyncio.run(runner.check_status("nonexistent"))
        assert result == "unknown"

    def test_running_when_alive(self) -> None:
        registry = ProcessRegistry()
        handle = self._make_handle("block-1", alive=True)
        registry.register(handle)
        runner = LocalRunner(event_bus=None, registry=registry)
        result = asyncio.run(runner.check_status("block-1"))
        assert result == "running"

    def test_completed_when_not_alive(self) -> None:
        registry = ProcessRegistry()
        handle = self._make_handle("block-1", alive=False)
        registry.register(handle)
        runner = LocalRunner(event_bus=None, registry=registry)
        result = asyncio.run(runner.check_status("block-1"))
        assert result == "completed"


# ---------------------------------------------------------------------------
# cancel
# ---------------------------------------------------------------------------


class TestLocalRunnerCancel:
    def _make_handle(self, block_id: str) -> ProcessHandle:
        mock_ops = MagicMock()
        mock_ops.terminate_tree.return_value = ProcessExitInfo(was_killed_by_framework=True)

        handle = ProcessHandle(
            block_id=block_id,
            pid=12345,
            start_time=datetime.now(),
            resource_request=MagicMock(),
        )
        handle._platform_ops = mock_ops
        return handle

    def test_cancel_without_registry_is_safe(self) -> None:
        runner = LocalRunner(event_bus=None, registry=None)
        asyncio.run(runner.cancel("any-id"))  # Should not raise

    def test_cancel_nonexistent_handle_is_safe(self) -> None:
        registry = ProcessRegistry()
        runner = LocalRunner(event_bus=None, registry=registry)
        asyncio.run(runner.cancel("nonexistent"))  # Should not raise

    def test_cancel_terminates_handle(self) -> None:
        registry = ProcessRegistry()
        handle = self._make_handle("block-1")
        registry.register(handle)
        runner = LocalRunner(event_bus=None, registry=registry)
        asyncio.run(runner.cancel("block-1"))
        assert handle.was_killed_by_framework is True


# ---------------------------------------------------------------------------
# run — with mocked subprocess
# ---------------------------------------------------------------------------


class TestLocalRunnerRun:
    @patch("scieasy.engine.runners.process_handle.subprocess.Popen")
    def test_run_returns_parsed_output(self, mock_popen_cls: MagicMock) -> None:
        """run() should return parsed JSON from subprocess stdout."""
        output_data = {"outputs": {"result": "42"}}
        mock_proc = MagicMock()
        mock_proc.pid = 100
        mock_proc.stdin = MagicMock()
        mock_proc.communicate.return_value = (
            json.dumps(output_data).encode(),
            b"",
        )
        mock_proc.returncode = 0
        mock_popen_cls.return_value = mock_proc

        bus = MagicMock()
        bus.emit = AsyncMock()
        registry = ProcessRegistry()
        runner = LocalRunner(event_bus=bus, registry=registry)

        # Create a fake block with a class path
        class FakeBlock:
            pass

        block = FakeBlock()
        result = asyncio.run(runner.run(block, {"input": "ref1"}, {"param": 1}))

        # After fix #120: envelope is unwrapped — we get the inner dict.
        assert result == {"result": "42"}
        mock_proc.communicate.assert_called_once()

    @patch("scieasy.engine.runners.process_handle.subprocess.Popen")
    def test_run_returns_error_on_nonzero_exit(self, mock_popen_cls: MagicMock) -> None:
        """run() should return error dict when subprocess exits with non-zero code."""
        mock_proc = MagicMock()
        mock_proc.pid = 101
        mock_proc.stdin = MagicMock()
        mock_proc.communicate.return_value = (b"", b"traceback here")
        mock_proc.returncode = 1
        mock_popen_cls.return_value = mock_proc

        bus = MagicMock()
        bus.emit = AsyncMock()
        registry = ProcessRegistry()
        runner = LocalRunner(event_bus=bus, registry=registry)

        class FakeBlock:
            pass

        result = asyncio.run(runner.run(FakeBlock(), {}, {}))

        assert "error" in result
        assert "traceback here" in result["error"]

    @patch("scieasy.engine.runners.process_handle.subprocess.Popen")
    def test_run_returns_empty_dict_on_no_stdout(self, mock_popen_cls: MagicMock) -> None:
        """run() should return empty dict when subprocess produces no stdout."""
        mock_proc = MagicMock()
        mock_proc.pid = 102
        mock_proc.stdin = MagicMock()
        mock_proc.communicate.return_value = (b"", b"")
        mock_proc.returncode = 0
        mock_popen_cls.return_value = mock_proc

        bus = MagicMock()
        bus.emit = AsyncMock()
        registry = ProcessRegistry()
        runner = LocalRunner(event_bus=bus, registry=registry)

        class FakeBlock:
            pass

        result = asyncio.run(runner.run(FakeBlock(), {}, {}))
        assert result == {}

    @patch("scieasy.engine.runners.process_handle.subprocess.Popen")
    def test_run_unwraps_output_envelope(self, mock_popen_cls: MagicMock) -> None:
        """run() should unwrap the {"outputs": ...} envelope (#120)."""
        inner = {"port_a": "value_a", "port_b": 123}
        envelope = {"outputs": inner}
        mock_proc = MagicMock()
        mock_proc.pid = 200
        mock_proc.stdin = MagicMock()
        mock_proc.communicate.return_value = (json.dumps(envelope).encode(), b"")
        mock_proc.returncode = 0
        mock_popen_cls.return_value = mock_proc

        bus = MagicMock()
        bus.emit = AsyncMock()
        runner = LocalRunner(event_bus=bus, registry=ProcessRegistry())

        class FakeBlock:
            pass

        result = asyncio.run(runner.run(FakeBlock(), {}, {}))
        assert result == inner

    @patch("scieasy.engine.runners.process_handle.subprocess.Popen")
    def test_run_passes_through_non_envelope_json(self, mock_popen_cls: MagicMock) -> None:
        """run() should return raw dict when no 'outputs' key is present."""
        raw = {"error": "something broke"}
        mock_proc = MagicMock()
        mock_proc.pid = 201
        mock_proc.stdin = MagicMock()
        mock_proc.communicate.return_value = (json.dumps(raw).encode(), b"")
        mock_proc.returncode = 0
        mock_popen_cls.return_value = mock_proc

        bus = MagicMock()
        bus.emit = AsyncMock()
        runner = LocalRunner(event_bus=bus, registry=ProcessRegistry())

        class FakeBlock:
            pass

        result = asyncio.run(runner.run(FakeBlock(), {}, {}))
        assert result == raw


# ---------------------------------------------------------------------------
# reconstruct_inputs — TypeSignature recovery (#132)
# ---------------------------------------------------------------------------


class TestReconstructInputsTypeChain:
    def test_uses_type_chain_from_metadata(self) -> None:
        """reconstruct_inputs should recover type_chain from metadata (#132)."""
        payload = {
            "inputs": {
                "image": {
                    "backend": "zarr",
                    "path": "/data/img.zarr",
                    "format": "zarr",
                    "metadata": {"type_chain": ["DataObject", "Image"]},
                }
            }
        }
        result = reconstruct_inputs(payload)
        proxy = result["image"]
        assert proxy.dtype_info.type_chain == ["DataObject", "Image"]

    def test_falls_back_to_dataobject_without_metadata(self) -> None:
        """reconstruct_inputs should default to ['DataObject'] when no type_chain."""
        payload = {
            "inputs": {
                "data": {
                    "backend": "zarr",
                    "path": "/data/obj.zarr",
                    "format": "zarr",
                }
            }
        }
        result = reconstruct_inputs(payload)
        proxy = result["data"]
        assert proxy.dtype_info.type_chain == ["DataObject"]

    def test_scalar_passthrough(self) -> None:
        """Scalar values should pass through unchanged."""
        payload = {"inputs": {"threshold": 0.5, "name": "test"}}
        result = reconstruct_inputs(payload)
        assert result == {"threshold": 0.5, "name": "test"}


# ---------------------------------------------------------------------------
# serialise_outputs — type_chain inclusion (#132)
# ---------------------------------------------------------------------------


class TestSerialiseOutputsTypeChain:
    def test_includes_type_chain_in_metadata(self) -> None:
        """serialise_outputs should add type_chain to serialized metadata (#132)."""
        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.types.base import DataObject

        obj = DataObject.__new__(DataObject)
        obj._storage_ref = StorageReference(backend="zarr", path="/out/result.zarr", format="zarr", metadata={})
        obj._metadata = {}
        obj._data = None

        result = serialise_outputs({"output": obj}, "/tmp/out")
        assert "type_chain" in result["output"]["metadata"]
        assert "DataObject" in result["output"]["metadata"]["type_chain"]


# ---------------------------------------------------------------------------
# spawn_block_process — async emit scheduling (#122)
# ---------------------------------------------------------------------------


class TestSpawnEmitScheduling:
    @patch("scieasy.engine.runners.process_handle.subprocess.Popen")
    def test_emit_scheduled_on_running_loop(self, mock_popen_cls: MagicMock) -> None:
        """emit() should be scheduled via create_task when event loop exists (#122)."""
        from scieasy.engine.runners.process_handle import spawn_block_process

        mock_proc = MagicMock()
        mock_proc.pid = 300
        mock_proc.stdin = MagicMock()
        mock_popen_cls.return_value = mock_proc

        bus = MagicMock()
        bus.emit = AsyncMock()
        registry = ProcessRegistry()

        async def _run() -> None:
            spawn_block_process(
                block_class="some.module.Block",
                inputs_refs={},
                config={},
                event_bus=bus,
                registry=registry,
            )
            # Let the scheduled task run
            await asyncio.sleep(0)

        asyncio.run(_run())
        bus.emit.assert_called_once()

    @patch("scieasy.engine.runners.process_handle.subprocess.Popen")
    def test_emit_skipped_without_event_loop(self, mock_popen_cls: MagicMock) -> None:
        """spawn_block_process should not raise when no event loop exists (#122)."""
        from scieasy.engine.runners.process_handle import spawn_block_process

        mock_proc = MagicMock()
        mock_proc.pid = 301
        mock_proc.stdin = MagicMock()
        mock_popen_cls.return_value = mock_proc

        bus = MagicMock()
        bus.emit = AsyncMock()
        registry = ProcessRegistry()

        # Call outside any async context — should not raise.
        spawn_block_process(
            block_class="some.module.Block",
            inputs_refs={},
            config={},
            event_bus=bus,
            registry=registry,
        )
        # emit should NOT have been called (no loop to schedule on).
        bus.emit.assert_not_called()
