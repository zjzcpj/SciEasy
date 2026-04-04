"""ResourceManager — GPU slots, CPU workers, OS memory monitoring.

ADR-022: OS-level memory monitoring via psutil replaces estimated_memory_gb.
Reactive dispatch gating instead of predictive static estimates.

ADR-018: Auto-release on terminal block states via EventBus subscription.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ResourceRequest:
    """Declares the resources a block needs before it can be scheduled.

    ADR-022: estimated_memory_gb REMOVED. System memory is monitored at OS
    level via psutil, not estimated per-block. GPU memory still declared
    because VRAM is not reliably monitorable cross-platform.
    """

    requires_gpu: bool = False
    gpu_memory_gb: float = 0.0
    cpu_cores: int = 1
    # ADR-022: estimated_memory_gb REMOVED


@dataclass
class ResourceSnapshot:
    """Read-only view of currently available resources.

    ADR-022: available_memory_gb replaced with system_memory_percent (0.0-1.0).
    """

    available_gpu_slots: int = 0
    available_cpu_workers: int = 4
    system_memory_percent: float = 0.0  # ADR-022: 0.0-1.0, from psutil


class ResourceManager:
    """Track and allocate compute resources for block execution.

    TODO(ADR-022): Implement three-layer defence.

    Layer 1 (this class): Dispatch gating.
        - GPU: discrete slot counting (declaration-based)
        - CPU: discrete core counting (declaration-based)
        - Memory: OS-level check via psutil.virtual_memory().percent
        - memory_high_watermark=0.80: pause dispatch above 80%
        - memory_critical=0.95: never dispatch above 95%

    Layer 2 (block-internal): _auto_flush, LazyList, parallel_map(max_workers)
        — operates independently, not managed here.

    Layer 3 (OS + ProcessMonitor): OS kills subprocess on OOM.
        ProcessMonitor detects, emits PROCESS_EXITED. Scheduler marks ERROR.

    TODO(ADR-018): EventBus integration for automatic resource release.
        __init__ accepts event_bus: EventBus | None. If provided, subscribe to
        BLOCK_DONE, BLOCK_ERROR, BLOCK_CANCELLED, PROCESS_EXITED with
        _on_block_terminal callback.

        _on_block_terminal(event): look up allocation by event.block_id,
        call self.release(allocation).

        _allocations: dict[str, ResourceRequest] — maps block_id to allocated.
    """

    def __init__(
        self,
        gpu_slots: int = 0,
        cpu_workers: int = 4,
        memory_high_watermark: float = 0.80,
        memory_critical: float = 0.95,
        event_bus: Any | None = None,
    ) -> None:
        # TODO(ADR-022): Store limits and watermarks.
        # TODO(ADR-018): If event_bus provided, subscribe to terminal events.
        # TODO(ADR-018): Initialize _allocations dict.
        raise NotImplementedError

    def can_dispatch(self, request: ResourceRequest) -> bool:
        """Check if resources are available AND system memory is below watermark.

        TODO(ADR-022): Check discrete GPU/CPU slots AND
        psutil.virtual_memory().percent < memory_high_watermark.
        Never dispatch if percent >= memory_critical.
        """
        raise NotImplementedError

    async def acquire(self, request: ResourceRequest) -> bool:
        """Reserve GPU slots and CPU cores.

        TODO(ADR-022): Reserve discrete resources only. Memory is not reserved —
        it drops naturally when subprocess exits.
        TODO(ADR-018): Store allocation in _allocations[block_id].
        """
        raise NotImplementedError

    def release(self, request: ResourceRequest) -> None:
        """Return previously acquired GPU/CPU resources to the pool.

        TODO(ADR-022): Release discrete resources only.
        TODO(ADR-018): Remove from _allocations.
        """
        raise NotImplementedError

    @property
    def available(self) -> ResourceSnapshot:
        """Return a snapshot including live system_memory_percent.

        TODO(ADR-022): Include psutil.virtual_memory().percent / 100.
        """
        raise NotImplementedError
