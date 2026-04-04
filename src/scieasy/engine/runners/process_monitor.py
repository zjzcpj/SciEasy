"""ProcessMonitor — background coroutine polling for unexpected process exits.

ADR-019: Polls active ProcessHandles every 1 second. Detects crashes, OOM kills,
and external termination. Emits PROCESS_EXITED events via EventBus.
"""

from __future__ import annotations

from typing import Any


class ProcessMonitor:
    """Background asyncio coroutine that watches for unexpected process death.

    TODO(ADR-019): Implement polling loop.

    Design:
        - Runs as asyncio.Task in the engine event loop.
        - Every 1 second, iterates all active ProcessHandles in ProcessRegistry.
        - For each handle, calls handle.is_alive().
        - If process has exited unexpectedly:
            1. Retrieve exit_info from handle.
            2. Emit PROCESS_EXITED event with ProcessExitInfo details.
            3. Subscribers (DAGScheduler, ResourceManager) react via EventBus.
        - Detects: crashes, OOM kills, user killing via OS task manager.

    Lifecycle:
        start(event_bus, registry) — create and start the background task.
        stop() — cancel the background task.
    """

    def __init__(self) -> None:
        # TODO(ADR-019): Store event_bus and registry references.
        raise NotImplementedError

    async def start(self, event_bus: Any, registry: Any) -> None:
        """Start the background polling coroutine.

        TODO(ADR-019): Create asyncio.Task running _poll_loop().
        """
        raise NotImplementedError

    async def stop(self) -> None:
        """Stop the background polling coroutine.

        TODO(ADR-019): Cancel the asyncio.Task.
        """
        raise NotImplementedError

    async def _poll_loop(self) -> None:
        """Poll all active handles at 1-second intervals.

        TODO(ADR-019): Loop forever with asyncio.sleep(1.0).
        For each handle in registry.active_handles():
            if not await handle.is_alive():
                info = await handle.exit_info()
                emit PROCESS_EXITED event with info
                registry.deregister(handle.block_id)
        """
        raise NotImplementedError
