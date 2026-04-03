"""ResourceManager -- GPU slots, CPU workers, memory budget."""

from __future__ import annotations

import threading
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

    Thread-safe: all mutations are protected by a lock.
    """

    def __init__(
        self,
        gpu_slots: int = 0,
        cpu_workers: int = 4,
        memory_budget_gb: float = 8.0,
    ) -> None:
        self._total_gpu = gpu_slots
        self._total_cpu = cpu_workers
        self._total_memory = memory_budget_gb

        self._avail_gpu = gpu_slots
        self._avail_cpu = cpu_workers
        self._avail_memory = memory_budget_gb

        self._lock = threading.Lock()

    async def acquire(self, request: ResourceRequest) -> bool:
        """Attempt to reserve resources described by *request*.

        Returns ``False`` immediately if the request can never be satisfied
        (e.g. requesting a GPU when none are configured).  Otherwise,
        tries to acquire and returns ``True`` on success.

        For simplicity this does not wait — callers should retry or use
        :meth:`try_acquire_nowait` in a polling loop.
        """
        if not self._can_ever_satisfy(request):
            return False
        return self.try_acquire_nowait(request)

    def try_acquire_nowait(self, request: ResourceRequest) -> bool:
        """Try to acquire resources without waiting.

        Returns ``True`` if acquired, ``False`` otherwise.
        """
        with self._lock:
            if request.requires_gpu and self._avail_gpu < 1:
                return False
            if request.cpu_cores > self._avail_cpu:
                return False
            total_mem = request.estimated_memory_gb
            if request.requires_gpu:
                total_mem += request.gpu_memory_gb
            if total_mem > self._avail_memory:
                return False

            # Commit.
            if request.requires_gpu:
                self._avail_gpu -= 1
                self._avail_memory -= request.gpu_memory_gb
            self._avail_cpu -= request.cpu_cores
            self._avail_memory -= request.estimated_memory_gb
            return True

    def release(self, request: ResourceRequest) -> None:
        """Return previously acquired resources to the pool."""
        with self._lock:
            if request.requires_gpu:
                self._avail_gpu += 1
                self._avail_memory += request.gpu_memory_gb
            self._avail_cpu += request.cpu_cores
            self._avail_memory += request.estimated_memory_gb

            # Clamp to totals (guard against double-release).
            self._avail_gpu = min(self._avail_gpu, self._total_gpu)
            self._avail_cpu = min(self._avail_cpu, self._total_cpu)
            self._avail_memory = min(self._avail_memory, self._total_memory)

    @property
    def available(self) -> ResourceSnapshot:
        """Return a snapshot of currently available resources."""
        with self._lock:
            return ResourceSnapshot(
                available_gpu_slots=self._avail_gpu,
                available_cpu_workers=self._avail_cpu,
                available_memory_gb=self._avail_memory,
            )

    def _can_ever_satisfy(self, request: ResourceRequest) -> bool:
        """Check if a request could ever be satisfied given total capacity."""
        if request.requires_gpu and self._total_gpu < 1:
            return False
        if request.cpu_cores > self._total_cpu:
            return False
        total_mem = request.estimated_memory_gb
        if request.requires_gpu:
            total_mem += request.gpu_memory_gb
        return total_mem <= self._total_memory
