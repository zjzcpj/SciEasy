"""Block runner implementations.

ADR-019: New submodules for cross-platform process lifecycle management.
"""

from scieasy.engine.runners.platform import PlatformOps, get_platform_ops
from scieasy.engine.runners.process_handle import (
    ProcessExitInfo,
    ProcessHandle,
    ProcessRegistry,
    spawn_block_process,
)

# TODO(ADR-019): Uncomment once ProcessMonitor is implemented.
# from scieasy.engine.runners.process_monitor import ProcessMonitor

__all__ = [
    "PlatformOps",
    "ProcessExitInfo",
    "ProcessHandle",
    "ProcessRegistry",
    "get_platform_ops",
    "spawn_block_process",
]
