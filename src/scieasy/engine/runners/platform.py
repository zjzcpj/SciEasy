"""Platform abstraction for process group management.

ADR-019: PlatformOps protocol + PosixOps + WindowsOps implementations.
Isolates all OS-specific process management behind a single protocol.
"""

from __future__ import annotations

import sys
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PlatformOps(Protocol):
    """Protocol for cross-platform process management.

    TODO(ADR-019): Implement 5 methods per platform.

    | Operation             | Linux / macOS                      | Windows                                  |
    |-----------------------|------------------------------------|------------------------------------------|
    | Process group creation| start_new_session=True             | CREATE_NEW_PROCESS_GROUP + Job Object    |
    | Graceful termination  | os.killpg(pgid, SIGTERM) + grace   | No equivalent; forced termination        |
    | Forced termination    | os.killpg(pgid, SIGKILL)           | TerminateJobObject() or TerminateProcess |
    | Process tree kill     | os.killpg()                        | Job Object                               |
    | Alive check           | os.kill(pid, 0)                    | OpenProcess() + GetExitCodeProcess()     |
    | Zombie cleanup        | os.waitpid(pid, WNOHANG)           | Not applicable                           |
    """

    def create_process_group(self, popen_kwargs: dict[str, Any]) -> dict[str, Any]:
        """Add platform-specific args to Popen kwargs for process group creation."""
        ...

    def terminate_tree(self, pid: int, grace_sec: float) -> Any:
        """Graceful termination of process tree. Returns ProcessExitInfo."""
        ...

    def kill_tree(self, pid: int) -> Any:
        """Immediate forced termination of process tree. Returns ProcessExitInfo."""
        ...

    def is_alive(self, pid: int) -> bool:
        """Non-blocking alive check."""
        ...

    def get_exit_info(self, pid: int) -> Any:
        """Return ProcessExitInfo if exited, None if still alive."""
        ...


class PosixOps:
    """Linux/macOS implementation.

    TODO(ADR-019): Implement using:
        - start_new_session=True for process group
        - os.killpg(pgid, signal.SIGTERM) for graceful
        - os.killpg(pgid, signal.SIGKILL) for forced
        - os.kill(pid, 0) for alive check (raises OSError if dead)
        - os.waitpid(pid, os.WNOHANG) for zombie cleanup
    """

    def create_process_group(self, popen_kwargs: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def terminate_tree(self, pid: int, grace_sec: float) -> Any:
        raise NotImplementedError

    def kill_tree(self, pid: int) -> Any:
        raise NotImplementedError

    def is_alive(self, pid: int) -> bool:
        raise NotImplementedError

    def get_exit_info(self, pid: int) -> Any:
        raise NotImplementedError


class WindowsOps:
    """Windows implementation.

    TODO(ADR-019): Implement using:
        - CREATE_NEW_PROCESS_GROUP flag for Popen
        - CreateJobObject() + AssignProcessToJobObject() for tree management
        - TerminateJobObject() for forced tree kill
        - TerminateProcess() as fallback
        - OpenProcess() + GetExitCodeProcess() for alive/exit check
        - psutil as helper for reliable tree termination

    Note: psutil used as helper, but custom Job Object handling required
    for reliable tree termination on Windows (ADR-019).
    """

    def create_process_group(self, popen_kwargs: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def terminate_tree(self, pid: int, grace_sec: float) -> Any:
        raise NotImplementedError

    def kill_tree(self, pid: int) -> Any:
        raise NotImplementedError

    def is_alive(self, pid: int) -> bool:
        raise NotImplementedError

    def get_exit_info(self, pid: int) -> Any:
        raise NotImplementedError


def get_platform_ops() -> PlatformOps:
    """Return the correct PlatformOps implementation for the current OS."""
    # TODO(ADR-019): Return PosixOps for Linux/macOS, WindowsOps for Windows.
    if sys.platform == "win32":
        return WindowsOps()
    return PosixOps()
