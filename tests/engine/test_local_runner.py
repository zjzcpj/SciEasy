"""Tests for LocalRunner — ADR-017."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from scieasy.engine.events import EventBus
from scieasy.engine.runners.local import LocalRunner
from scieasy.engine.runners.process_handle import (
    ProcessExitInfo,
    ProcessHandle,
    ProcessRegistry,
)

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
        registry = ProcessRegistry()
        runner = LocalRunner(event_bus=bus, registry=registry)

        # Create a fake block with a class path
        class FakeBlock:
            pass

        block = FakeBlock()
        result = asyncio.run(runner.run(block, {"input": "ref1"}, {"param": 1}))

        assert result == output_data
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
        registry = ProcessRegistry()
        runner = LocalRunner(event_bus=bus, registry=registry)

        class FakeBlock:
            pass

        result = asyncio.run(runner.run(FakeBlock(), {}, {}))
        assert result == {}
