"""LocalRunner -- in-process block execution."""

from __future__ import annotations

import time
import uuid
from typing import Any

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.result import BlockResult
from scieasy.blocks.base.state import BlockState


class LocalRunner:
    """Execute blocks in the local process.

    Implements the :class:`~scieasy.engine.runners.base.BlockRunner`
    protocol for same-machine execution.
    """

    def __init__(self) -> None:
        self._runs: dict[str, str] = {}

    async def run(
        self,
        block: Block,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> BlockResult:
        """Execute *block* locally with the given *inputs* and *config*.

        Manages state transitions (READY -> RUNNING -> DONE/ERROR) and
        calls validate, run, postprocess in sequence.
        """
        run_id = uuid.uuid4().hex[:12]
        self._runs[run_id] = "running"

        block.transition(BlockState.READY)
        block.validate(inputs)
        block.transition(BlockState.RUNNING)

        start = time.monotonic()
        try:
            block_config = block.config if isinstance(block.config, BlockConfig) else BlockConfig(**(config or {}))
            outputs = block.run(inputs, block_config)
            outputs = block.postprocess(outputs)
            duration_ms = int((time.monotonic() - start) * 1000)
            block.transition(BlockState.DONE)
            self._runs[run_id] = "done"
            return BlockResult(outputs=outputs, duration_ms=duration_ms)
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            block.transition(BlockState.ERROR)
            self._runs[run_id] = "error"
            return BlockResult(outputs={}, duration_ms=duration_ms, error=exc)

    async def check_status(self, run_id: str) -> str:
        """Query the current status of a previously started run."""
        return self._runs.get(run_id, "unknown")

    async def cancel(self, run_id: str) -> None:
        """Request cancellation of a running execution."""
        if run_id in self._runs:
            self._runs[run_id] = "cancelled"
