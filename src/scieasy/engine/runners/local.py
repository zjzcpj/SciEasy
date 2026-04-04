"""LocalRunner — subprocess execution on the local machine.

ADR-017: All block execution in isolated subprocesses. No in-process execution.
Uses spawn_block_process() as the single subprocess creation entry point.
"""

from __future__ import annotations

from typing import Any


class LocalRunner:
    """Execute blocks as local subprocesses.

    TODO(ADR-017): Implement using spawn_block_process().

    Implements the BlockRunner protocol (engine/runners/base.py).

    Methods:
        async run(block, inputs, config) -> RunHandle
            - Calls spawn_block_process() to create isolated subprocess.
            - Returns RunHandle with run_id, ProcessHandle, and asyncio.Future.
            - Future resolves when subprocess exits with output refs.

        async check_status(run_id) -> BlockState
            - Queries ProcessHandle.is_alive() for the given run_id.
            - Returns RUNNING if alive, DONE/ERROR based on exit info.

        async cancel(run_id) -> None
            - Calls ProcessHandle.terminate(grace_period_sec) for the given run_id.
    """

    async def run(
        self,
        block: Any,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> Any:
        """Execute *block* in an isolated subprocess.

        TODO(ADR-017): Return RunHandle (not dict[str, Any]).
        """
        raise NotImplementedError

    async def check_status(self, run_id: str) -> Any:
        """Query the current status of a previously started run.

        TODO(ADR-017): Query ProcessHandle.is_alive() from ProcessRegistry.
        """
        raise NotImplementedError

    async def cancel(self, run_id: str) -> None:
        """Request cancellation of a running execution.

        TODO(ADR-017): Call ProcessHandle.terminate() from ProcessRegistry.
        """
        raise NotImplementedError
