"""ProcessHandle, ProcessExitInfo, ProcessRegistry, spawn_block_process.

ADR-019: Unified abstraction for OS process management across platforms.
ADR-017: spawn_block_process() is the single entry point for ALL subprocess creation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ProcessExitInfo:
    """Exit state of a terminated subprocess.

    TODO(ADR-019): Populated by PlatformOps when process exits.
    """

    exit_code: int | None = None
    signal_number: int | None = None  # Unix only, None on Windows
    was_killed_by_framework: bool = False
    platform_detail: str = ""


class ProcessHandle:
    """Per-process wrapper tracking lifecycle of a block subprocess.

    TODO(ADR-019): Implement all methods using PlatformOps.

    Fields:
        block_id: str — which block owns this process
        pid: int — OS process ID
        start_time: datetime — when the process was spawned
        resource_request: ResourceRequest — what resources were allocated
    """

    def __init__(
        self,
        block_id: str,
        pid: int,
        start_time: datetime,
        resource_request: Any,
    ) -> None:
        # TODO(ADR-019): Store fields. Get platform ops via get_platform_ops().
        raise NotImplementedError

    async def is_alive(self) -> bool:
        """Non-blocking alive check.

        TODO(ADR-019): Delegate to PlatformOps.is_alive(self.pid).
        Linux/macOS: os.kill(pid, 0). Windows: OpenProcess() + GetExitCodeProcess().
        """
        raise NotImplementedError

    async def exit_info(self) -> ProcessExitInfo | None:
        """Return ProcessExitInfo if process has exited, None if still alive.

        TODO(ADR-019): Delegate to PlatformOps.get_exit_info(self.pid).
        """
        raise NotImplementedError

    async def terminate(self, grace_period_sec: float = 5.0) -> ProcessExitInfo:
        """Graceful then forced kill.

        TODO(ADR-019): Send SIGTERM (Unix) or begin graceful shutdown (Windows).
        Wait grace_period_sec. If still alive, call kill().
        Linux/macOS: os.killpg(pgid, SIGTERM) → wait → os.killpg(pgid, SIGKILL).
        Windows: No graceful equivalent; forced termination via TerminateJobObject().
        """
        raise NotImplementedError

    async def kill(self) -> ProcessExitInfo:
        """Immediate forced termination.

        TODO(ADR-019): Delegate to PlatformOps.kill_tree(self.pid).
        Linux/macOS: os.killpg(pgid, SIGKILL). Windows: TerminateJobObject().
        """
        raise NotImplementedError


class ProcessRegistry:
    """Singleton tracking all active block subprocesses.

    TODO(ADR-019): Implement as singleton or module-level instance.
    """

    def register(self, handle: ProcessHandle) -> None:
        """Register a newly spawned process."""
        raise NotImplementedError

    def deregister(self, block_id: str) -> None:
        """Remove a process after it has exited."""
        raise NotImplementedError

    def get_handle(self, block_id: str) -> ProcessHandle | None:
        """Look up the handle for a block."""
        raise NotImplementedError

    def active_handles(self) -> list[ProcessHandle]:
        """Return all currently active process handles."""
        raise NotImplementedError

    async def terminate_all(self, grace_period_sec: float = 5.0) -> None:
        """Terminate all active processes (engine shutdown).

        TODO(ADR-019): Iterate active_handles(), call terminate() on each.
        """
        raise NotImplementedError


def spawn_block_process(
    block_class: Any,
    inputs_refs: dict[str, Any],
    config: dict[str, Any],
    event_bus: Any,
    registry: ProcessRegistry,
) -> ProcessHandle:
    """Single entry point for ALL subprocess creation.

    TODO(ADR-017, ADR-019): Implement subprocess spawning.

    Steps:
        1. Serialize payload: block class path, StorageReference pointers, config.
        2. Create subprocess via Popen:
           - Linux/macOS: start_new_session=True (new process group for killpg).
           - Windows: CREATE_NEW_PROCESS_GROUP + Job Object (kills entire tree).
        3. Create ProcessHandle wrapping the Popen.
        4. Register handle in ProcessRegistry.
        5. Emit PROCESS_SPAWNED event via EventBus.
        6. Return the ProcessHandle.

    The subprocess runs engine/runners/worker.py as entry point.
    """
    raise NotImplementedError
