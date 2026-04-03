"""Tests for ResourceManager."""

from __future__ import annotations

import pytest

from scieasy.engine.resources import ResourceManager, ResourceRequest


class TestResourceManager:
    """ResourceManager — GPU slots, CPU workers, memory budget."""

    def test_initial_availability(self) -> None:
        rm = ResourceManager(gpu_slots=2, cpu_workers=8, memory_budget_gb=16.0)
        snap = rm.available
        assert snap.available_gpu_slots == 2
        assert snap.available_cpu_workers == 8
        assert snap.available_memory_gb == 16.0

    def test_acquire_cpu_only(self) -> None:
        rm = ResourceManager(cpu_workers=4, memory_budget_gb=8.0)
        req = ResourceRequest(cpu_cores=2, estimated_memory_gb=1.0)
        ok = rm.try_acquire_nowait(req)
        assert ok
        assert rm.available.available_cpu_workers == 2
        assert rm.available.available_memory_gb == pytest.approx(7.0)

    def test_acquire_gpu(self) -> None:
        rm = ResourceManager(gpu_slots=1, cpu_workers=4, memory_budget_gb=16.0)
        req = ResourceRequest(requires_gpu=True, gpu_memory_gb=4.0, cpu_cores=1, estimated_memory_gb=1.0)
        ok = rm.try_acquire_nowait(req)
        assert ok
        assert rm.available.available_gpu_slots == 0
        # 16.0 - 4.0 (gpu) - 1.0 (est) = 11.0
        assert rm.available.available_memory_gb == pytest.approx(11.0)

    def test_acquire_fails_no_gpu(self) -> None:
        rm = ResourceManager(gpu_slots=0, cpu_workers=4, memory_budget_gb=8.0)
        req = ResourceRequest(requires_gpu=True)
        ok = rm.try_acquire_nowait(req)
        assert not ok

    def test_acquire_fails_insufficient_cpu(self) -> None:
        rm = ResourceManager(cpu_workers=2, memory_budget_gb=8.0)
        req = ResourceRequest(cpu_cores=4)
        ok = rm.try_acquire_nowait(req)
        assert not ok

    def test_acquire_fails_insufficient_memory(self) -> None:
        rm = ResourceManager(cpu_workers=4, memory_budget_gb=1.0)
        req = ResourceRequest(estimated_memory_gb=2.0)
        ok = rm.try_acquire_nowait(req)
        assert not ok

    def test_release_restores_resources(self) -> None:
        rm = ResourceManager(gpu_slots=1, cpu_workers=4, memory_budget_gb=8.0)
        req = ResourceRequest(requires_gpu=True, gpu_memory_gb=2.0, cpu_cores=2, estimated_memory_gb=1.0)
        rm.try_acquire_nowait(req)
        rm.release(req)
        snap = rm.available
        assert snap.available_gpu_slots == 1
        assert snap.available_cpu_workers == 4
        assert snap.available_memory_gb == pytest.approx(8.0)

    def test_release_clamps_to_total(self) -> None:
        """Double-release should not exceed total capacity."""
        rm = ResourceManager(cpu_workers=4, memory_budget_gb=8.0)
        req = ResourceRequest(cpu_cores=1, estimated_memory_gb=1.0)
        rm.try_acquire_nowait(req)
        rm.release(req)
        rm.release(req)  # Double release.
        assert rm.available.available_cpu_workers == 4
        assert rm.available.available_memory_gb == pytest.approx(8.0)

    def test_gpu_slot_exhaustion_serial_fallback(self) -> None:
        """With 0 GPU slots, GPU requests should fail — caller should fall back to serial."""
        rm = ResourceManager(gpu_slots=0, cpu_workers=4, memory_budget_gb=8.0)
        gpu_req = ResourceRequest(requires_gpu=True, gpu_memory_gb=4.0)
        cpu_req = ResourceRequest(cpu_cores=1, estimated_memory_gb=0.5)

        assert not rm.try_acquire_nowait(gpu_req)
        assert rm.try_acquire_nowait(cpu_req)

    def test_multiple_sequential_acquires(self) -> None:
        rm = ResourceManager(cpu_workers=4, memory_budget_gb=8.0)
        req = ResourceRequest(cpu_cores=1, estimated_memory_gb=2.0)

        for _ in range(4):
            assert rm.try_acquire_nowait(req)

        # 5th should fail: no CPU left.
        assert not rm.try_acquire_nowait(req)

    @pytest.mark.asyncio
    async def test_async_acquire(self) -> None:
        rm = ResourceManager(cpu_workers=2, memory_budget_gb=8.0)
        req = ResourceRequest(cpu_cores=1, estimated_memory_gb=1.0)
        ok = await rm.acquire(req)
        assert ok
        assert rm.available.available_cpu_workers == 1

    @pytest.mark.asyncio
    async def test_async_acquire_impossible_returns_false(self) -> None:
        rm = ResourceManager(gpu_slots=0, cpu_workers=2, memory_budget_gb=8.0)
        req = ResourceRequest(requires_gpu=True, gpu_memory_gb=4.0)
        ok = await rm.acquire(req)
        assert not ok
