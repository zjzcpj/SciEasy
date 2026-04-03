"""Tests for BatchExecutor — parallel, serial, adaptive dispatch."""

from __future__ import annotations

import pytest

from scieasy.blocks.base.state import BatchErrorStrategy
from scieasy.engine.batch import BatchExecutor
from tests.engine.conftest import AddOneBlock, DoubleBlock, FailingBlock, InteractiveBlock, SerialBlock


class TestBatchSerial:
    """execute_serial — one item at a time."""

    @pytest.mark.asyncio
    async def test_serial_10_items(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.SKIP)
        items = [{"x": i} for i in range(10)]
        result = await executor.execute_serial(AddOneBlock, items)
        assert len(result.succeeded) == 10
        assert len(result.failed) == 0
        for idx, outputs in result.succeeded:
            assert outputs["x"] == idx + 1

    @pytest.mark.asyncio
    async def test_serial_stop_on_error(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.STOP)
        items = [{"x": 1}, {"x": 2}, {"x": 3}]
        result = await executor.execute_serial(FailingBlock, items)
        assert len(result.failed) == 1
        assert result.failed[0][0] == 0  # First item failed.

    @pytest.mark.asyncio
    async def test_serial_skip_on_error(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.SKIP)
        items = [{"x": 1}, {"x": 2}]
        result = await executor.execute_serial(FailingBlock, items)
        assert len(result.failed) == 2
        assert len(result.succeeded) == 0

    @pytest.mark.asyncio
    async def test_serial_pause_on_error(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.PAUSE)
        items = [{"x": 1}, {"x": 2}, {"x": 3}]
        result = await executor.execute_serial(FailingBlock, items)
        assert len(result.failed) == 1
        assert len(result.skipped) == 2

    @pytest.mark.asyncio
    async def test_serial_retry_on_error(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.RETRY)
        items = [{"x": 1}]
        result = await executor.execute_serial(FailingBlock, items)
        # Both original and retry should fail.
        assert len(result.failed) == 1


class TestBatchParallel:
    """execute_parallel — concurrent dispatch."""

    @pytest.mark.asyncio
    async def test_parallel_10_items(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.SKIP)
        items = [{"x": i} for i in range(10)]
        result = await executor.execute_parallel(DoubleBlock, items, max_workers=4)
        assert len(result.succeeded) == 10
        values = {idx: out["x"] for idx, out in result.succeeded}
        for i in range(10):
            assert values[i] == i * 2

    @pytest.mark.asyncio
    async def test_parallel_with_failures(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.SKIP)
        items = [{"x": 1}, {"x": 2}]
        result = await executor.execute_parallel(FailingBlock, items, max_workers=2)
        assert len(result.failed) == 2
        assert len(result.succeeded) == 0


class TestBatchAdaptive:
    """execute_adaptive — auto-selects serial or parallel."""

    @pytest.mark.asyncio
    async def test_adaptive_uses_parallel_for_many(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.SKIP)
        items = [{"x": i} for i in range(10)]
        result = await executor.execute_adaptive(AddOneBlock, items)
        assert len(result.succeeded) == 10

    @pytest.mark.asyncio
    async def test_adaptive_serial_for_serial_block(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.SKIP)
        items = [{"x": i} for i in range(5)]
        result = await executor.execute_adaptive(SerialBlock, items)
        assert len(result.succeeded) == 5
        for idx, outputs in result.succeeded:
            assert outputs["x"] == idx * 10

    @pytest.mark.asyncio
    async def test_adaptive_serial_for_interactive(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.SKIP)
        items = [{"x": i} for i in range(3)]
        result = await executor.execute_adaptive(InteractiveBlock, items)
        assert len(result.succeeded) == 3

    @pytest.mark.asyncio
    async def test_adaptive_serial_for_few_items(self) -> None:
        executor = BatchExecutor(error_strategy=BatchErrorStrategy.SKIP)
        items = [{"x": 5}]
        result = await executor.execute_adaptive(AddOneBlock, items)
        assert len(result.succeeded) == 1
        assert result.succeeded[0][1]["x"] == 6
