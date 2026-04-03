"""ResourceManager -- GPU slots, CPU workers, memory budget."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResourceRequest:
    """Declares the resources a block needs before it can be scheduled."""

    requires_gpu: bool = False
    gpu_memory_gb: float = 0.0
    estimated_memory_gb: float = 0.5
    cpu_cores: int = 1


@dataclass
class ResourceSnapshot:
    """Read-only view of currently available resources."""

    available_gpu_slots: int = 0
    available_cpu_workers: int = 4
    available_memory_gb: float = 8.0


class ResourceManager:
    """Track and allocate compute resources for block execution.

    The manager maintains a budget of GPU slots, CPU workers, and system
    memory.  Blocks must :meth:`acquire` resources before running and
    :meth:`release` them when finished.
    """

    def __init__(
        self,
        gpu_slots: int = 0,
        cpu_workers: int = 4,
        memory_budget_gb: float = 8.0,
    ) -> None:
        """Initialise the resource manager with capacity limits.

        Parameters
        ----------
        gpu_slots:
            Total number of GPU execution slots.
        cpu_workers:
            Total number of CPU worker slots.
        memory_budget_gb:
            Total memory budget in GiB.
        """
        raise NotImplementedError

    async def acquire(self, request: ResourceRequest) -> bool:
        """Attempt to reserve resources described by *request*.

        Returns
        -------
        bool
            ``True`` if the resources were successfully reserved.
        """
        raise NotImplementedError

    def release(self, request: ResourceRequest) -> None:
        """Return previously acquired resources to the pool."""
        raise NotImplementedError

    @property
    def available(self) -> ResourceSnapshot:
        """Return a snapshot of currently available resources."""
        raise NotImplementedError
