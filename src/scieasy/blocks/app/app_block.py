"""AppBlock — bridges external GUI software via file-exchange protocol."""

from __future__ import annotations

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

    # TODO(ADR-017): Must use spawn_block_process() instead of direct subprocess.
    # TODO(ADR-018): State machine must include CANCELLED transitions.
    # TODO(ADR-019): ProcessHandle integration for cancellation — store handle from bridge.launch().
    # TODO(ADR-020): run() receives/returns dict[str, Collection].

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Prepare inputs, launch the external app, and collect outputs.

        The lifecycle is:
        1. RUNNING — prepare inputs into exchange dir
        2. PAUSED  — launch external app, wait for output
        3. RUNNING — collect output files
        4. DONE    — return results
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

            # Step 1: Prepare inputs.
            bridge.prepare(inputs, exchange_dir)

            # Step 2: Launch and pause (waiting for external interaction).
            self.transition(BlockState.PAUSED)
            bridge.launch(command, exchange_dir)

            # Step 3: Watch for outputs.
            from scieasy.blocks.app.watcher import FileWatcher

            output_dir = exchange_dir / "outputs"
            output_dir.mkdir(exist_ok=True)
            watcher = FileWatcher(
                directory=output_dir,
                patterns=patterns,
                timeout=timeout,
            )
            watcher.start()
            try:
                output_files = watcher.wait_for_output()
            finally:
                watcher.stop()

            # Step 4: Resume and collect.
            self.transition(BlockState.RUNNING)
            results = bridge.collect(output_files)

            self.transition(BlockState.DONE)
            return results

        except Exception:
            self.transition(BlockState.ERROR)
            raise
