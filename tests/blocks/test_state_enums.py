"""Tests for state enums — BlockState, ExecutionMode, BatchMode, InputDelivery, BatchErrorStrategy."""

from __future__ import annotations

from scieasy.blocks.base.state import (
    BatchErrorStrategy,
    BatchMode,
    BlockState,
    ExecutionMode,
    InputDelivery,
)


class TestBlockStateValues:
    """BlockState — lifecycle state of a block instance."""

    def test_all_values(self) -> None:
        assert BlockState.IDLE.value == "idle"
        assert BlockState.READY.value == "ready"
        assert BlockState.RUNNING.value == "running"
        assert BlockState.PAUSED.value == "paused"
        assert BlockState.DONE.value == "done"
        assert BlockState.ERROR.value == "error"

    def test_member_count(self) -> None:
        assert len(BlockState) == 6


class TestExecutionModeValues:
    """ExecutionMode — how the block is executed."""

    def test_all_values(self) -> None:
        assert ExecutionMode.AUTO.value == "auto"
        assert ExecutionMode.INTERACTIVE.value == "interactive"
        assert ExecutionMode.EXTERNAL.value == "external"

    def test_member_count(self) -> None:
        assert len(ExecutionMode) == 3


class TestBatchModeValues:
    """BatchMode — strategy for processing multiple inputs."""

    def test_all_values(self) -> None:
        assert BatchMode.PARALLEL.value == "parallel"
        assert BatchMode.SERIAL.value == "serial"
        assert BatchMode.ADAPTIVE.value == "adaptive"

    def test_member_count(self) -> None:
        assert len(BatchMode) == 3


class TestInputDeliveryValues:
    """InputDelivery — how input data is delivered to the block."""

    def test_all_values(self) -> None:
        assert InputDelivery.MEMORY.value == "memory"
        assert InputDelivery.PROXY.value == "proxy"
        assert InputDelivery.CHUNKED.value == "chunked"

    def test_member_count(self) -> None:
        assert len(InputDelivery) == 3


class TestBatchErrorStrategyValues:
    """BatchErrorStrategy — what to do when a batch item fails."""

    def test_all_values(self) -> None:
        assert BatchErrorStrategy.STOP.value == "stop"
        assert BatchErrorStrategy.SKIP.value == "skip"
        assert BatchErrorStrategy.RETRY.value == "retry"
        assert BatchErrorStrategy.PAUSE.value == "pause"

    def test_member_count(self) -> None:
        assert len(BatchErrorStrategy) == 4
