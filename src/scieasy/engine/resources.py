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

    Layer 1 (this class): Dispatch gating (ADR-022).
        - GPU: discrete slot counting (declaration-based)
        - CPU: discrete core counting (declaration-based)
        - Memory: OS-level check via psutil.virtual_memory().percent
        - memory_high_watermark=0.80: pause dispatch above 80%
        - memory_critical=0.95: never dispatch above 95%

    Layer 2 (block-internal): _auto_flush, LazyList, parallel_map(max_workers)
        -- operates independently, not managed here.

    Layer 3 (OS + ProcessMonitor): OS kills subprocess on OOM.
        ProcessMonitor detects, emits PROCESS_EXITED. Scheduler marks ERROR.

    EventBus integration (ADR-018): automatic resource release on terminal
    block states via _on_block_terminal callback.
    """

    def __init__(
        self,
        gpu_slots: int = 0,
        cpu_workers: int = 4,
        memory_high_watermark: float = 0.80,
        memory_critical: float = 0.95,
        event_bus: Any | None = None,
    ) -> None:
        self.gpu_slots = gpu_slots
        self.max_cpu_workers = cpu_workers
        self.memory_high_watermark = memory_high_watermark
        self.memory_critical = memory_critical
        self._gpu_in_use: int = 0
        self._cpu_in_use: int = 0
        self._allocations: dict[str, ResourceRequest] = {}

        if event_bus is not None:
            from scieasy.engine.events import (
                BLOCK_CANCELLED,
                BLOCK_DONE,
                BLOCK_ERROR,
                PROCESS_EXITED,
            )

            event_bus.subscribe(BLOCK_DONE, self._on_block_terminal)
            event_bus.subscribe(BLOCK_ERROR, self._on_block_terminal)
            event_bus.subscribe(BLOCK_CANCELLED, self._on_block_terminal)
            event_bus.subscribe(PROCESS_EXITED, self._on_block_terminal)

    def can_dispatch(self, request: ResourceRequest) -> bool:
        """Check if resources are available AND system memory is below watermark.

        Returns False if:
        - GPU is required but all GPU slots are in use
        - Requested CPU cores would exceed the pool
        - System memory percent >= memory_critical (always blocked)
        - System memory percent > memory_high_watermark (paused)
        """
        import psutil

        # GPU check
        if request.requires_gpu and self._gpu_in_use >= self.gpu_slots:
            return False
        # CPU check
        if self._cpu_in_use + request.cpu_cores > self.max_cpu_workers:
            return False
        # Memory check via psutil (ADR-022)
        mem_percent = psutil.virtual_memory().percent / 100.0
        if mem_percent >= self.memory_critical:
            return False
        return not mem_percent > self.memory_high_watermark

    async def acquire(self, request: ResourceRequest, block_id: str = "") -> bool:
        """Reserve GPU slots and CPU cores.

        Memory is not reserved -- it drops naturally when subprocess exits
        (ADR-022). Allocation is tracked by block_id for auto-release
        (ADR-018).

        Returns True if resources were successfully acquired, False otherwise.
        """
        if not self.can_dispatch(request):
            return False
        if request.requires_gpu:
            self._gpu_in_use += 1
        self._cpu_in_use += request.cpu_cores
        if block_id:
            self._allocations[block_id] = request
        return True

    def release(self, request: ResourceRequest, block_id: str = "") -> None:
        """Return previously acquired GPU/CPU resources to the pool.

        Uses max(0, ...) to prevent negative counters in edge cases.
        """
        if request.requires_gpu:
            self._gpu_in_use = max(0, self._gpu_in_use - 1)
        self._cpu_in_use = max(0, self._cpu_in_use - request.cpu_cores)
        if block_id and block_id in self._allocations:
            del self._allocations[block_id]

    def _on_block_terminal(self, event: Any) -> None:
        """Auto-release resources when a block reaches a terminal state.

        Called by EventBus for BLOCK_DONE, BLOCK_ERROR, BLOCK_CANCELLED,
        and PROCESS_EXITED events (ADR-018).
        """
        block_id = event.block_id
        if block_id and block_id in self._allocations:
            self.release(self._allocations[block_id], block_id)

    @property
    def available(self) -> ResourceSnapshot:
        """Return a snapshot including live system_memory_percent from psutil."""
        import psutil

        return ResourceSnapshot(
            available_gpu_slots=max(0, self.gpu_slots - self._gpu_in_use),
            available_cpu_workers=max(0, self.max_cpu_workers - self._cpu_in_use),
            system_memory_percent=psutil.virtual_memory().percent / 100.0,
        )
