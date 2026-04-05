"""AppBlock — bridges external GUI software via file-exchange protocol."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, ClassVar

from scieasy.blocks.app.bridge import FileExchangeBridge
from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState, ExecutionMode
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection


class _PopenProcessAdapter:
    """Adapter wrapping subprocess.Popen with process_handle interface for FileWatcher.

    ADR-019: FileWatcher expects a process_handle with ``is_alive()`` and ``pid``
    attributes. ``subprocess.Popen`` has ``poll()`` and ``pid`` but no ``is_alive()``.
    This adapter bridges the two interfaces.
    """

    def __init__(self, proc: subprocess.Popen) -> None:  # type: ignore[type-arg]
        self._proc = proc

    @property
    def pid(self) -> int:
        return self._proc.pid

    def is_alive(self) -> bool:
        return self._proc.poll() is None


class AppBlock(Block):
    """Block that delegates work to an external GUI application.

    Communication happens via a file-exchange directory: the block serialises
    inputs, launches the application, watches for output files, and collects
    the results.

    State transitions: IDLE -> READY -> RUNNING -> PAUSED -> (RUNNING ->) DONE

    The block enters PAUSED state after launching the external application,
    signalling to the scheduler that it is waiting for external output.
    Once output files are detected, the block transitions back to RUNNING
    and then to DONE.
    """

    app_command: ClassVar[str] = ""
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL
    output_patterns: ClassVar[list[str]] = ["*"]
    watch_timeout: ClassVar[int] = 300

    name: ClassVar[str] = "App Block"
    description: ClassVar[str] = "Delegate work to an external GUI application"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="data", accepted_types=[DataObject], required=False, description="Input data for the app"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="result", accepted_types=[Artifact], description="Output artifacts from the app"),
    ]

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        """Prepare inputs, launch the external app, and collect outputs.

        ADR-018: Handles CANCELLED transitions when external process exits unexpectedly.
        ADR-019: Stores ProcessHandle from bridge for cancellation support.
        ADR-020: Accepts and returns Collection-wrapped data.
        """
        self.transition(BlockState.RUNNING)
        try:
            bridge = FileExchangeBridge()
            command = config.get("app_command") or self.app_command
            if not command:
                raise ValueError("AppBlock requires 'app_command' in config or as class variable")

            patterns = config.get("output_patterns") or self.output_patterns
            timeout = int(config.get("watch_timeout", self.watch_timeout))

            # Create exchange directory.
            exchange_dir = Path(config.get("exchange_dir") or tempfile.mkdtemp(prefix="scieasy_app_"))

            # ADR-020: Unpack Collection inputs to raw values for serialization.
            unpacked_inputs: dict[str, Any] = {}
            for key, value in inputs.items():
                if isinstance(value, Collection):
                    items = list(value)
                    unpacked_inputs[key] = items[0] if len(items) == 1 else items
                else:
                    unpacked_inputs[key] = value

            # Step 1: Prepare inputs.
            bridge.prepare(unpacked_inputs, exchange_dir)

            # Step 2: Launch and pause (waiting for external interaction).
            self.transition(BlockState.PAUSED)
            proc = bridge.launch(command, exchange_dir)

            # ADR-019: Wrap Popen in adapter for FileWatcher process monitoring.
            process_adapter = _PopenProcessAdapter(proc)

            # Step 3: Watch for outputs with process monitoring.
            from scieasy.blocks.app.watcher import FileWatcher, ProcessExitedWithoutOutputError

            output_dir = exchange_dir / "outputs"
            output_dir.mkdir(exist_ok=True)
            watcher = FileWatcher(
                directory=output_dir,
                patterns=patterns,
                timeout=timeout,
                process_handle=process_adapter,
            )
            watcher.start()
            try:
                output_files = watcher.wait_for_output()
            except ProcessExitedWithoutOutputError:
                # ADR-018: Process exited without producing output — cancel.
                self.transition(BlockState.CANCELLED)
                return {}
            finally:
                watcher.stop()

            # Step 4: Resume and collect.
            self.transition(BlockState.RUNNING)
            results = bridge.collect(output_files)

            # ADR-020: Wrap output artifacts in Collection.
            collection_results: dict[str, Any] = {}
            for key, value in results.items():
                if isinstance(value, Artifact):
                    collection_results[key] = Collection([value], item_type=Artifact)
                else:
                    collection_results[key] = value

            self.transition(BlockState.DONE)
            return collection_results

        except Exception:
            if self.state not in (BlockState.CANCELLED, BlockState.DONE):
                self.transition(BlockState.ERROR)
            raise
