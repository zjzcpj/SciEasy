"""Tests for DAGScheduler -- ADR-018."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from scieasy.blocks.base.state import BlockState
from scieasy.engine.events import (
    BLOCK_DONE,
    CANCEL_BLOCK_REQUEST,
    CANCEL_WORKFLOW_REQUEST,
    WORKFLOW_COMPLETED,
    WORKFLOW_STARTED,
    EngineEvent,
    EventBus,
)
from scieasy.engine.scheduler import DAGScheduler
from scieasy.workflow.definition import EdgeDef, NodeDef, WorkflowDefinition

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wf(
    nodes: list[tuple[str, str]],
    edges: list[tuple[str, str]] | None = None,
) -> WorkflowDefinition:
    """Build a minimal WorkflowDefinition."""
    node_defs = [NodeDef(id=n_id, block_type=bt) for n_id, bt in nodes]
    edge_defs = [EdgeDef(source=s, target=t) for s, t in (edges or [])]
    return WorkflowDefinition(nodes=node_defs, edges=edge_defs)


def _make_scheduler(
    workflow: WorkflowDefinition,
    runner_return: dict | None = None,
    runner_side_effect: list | None = None,
) -> tuple[DAGScheduler, EventBus, AsyncMock]:
    """Create a DAGScheduler with mocked dependencies."""
    event_bus = EventBus()
    resource_manager = MagicMock()
    resource_manager.can_dispatch.return_value = True
    process_registry = MagicMock()
    process_registry.get_handle.return_value = None

    runner = AsyncMock()
    if runner_side_effect is not None:
        runner.run.side_effect = runner_side_effect
    else:
        runner.run.return_value = runner_return or {"output": "mock_result"}

    scheduler = DAGScheduler(
        workflow=workflow,
        event_bus=event_bus,
        resource_manager=resource_manager,
        process_registry=process_registry,
        runner=runner,
    )
    return scheduler, event_bus, runner


# ---------------------------------------------------------------------------
# Linear execution
# ---------------------------------------------------------------------------


class TestSchedulerLinear:
    """Test basic linear workflow execution."""

    def test_scheduler_linear_all_done(self) -> None:
        """A->B->C: all blocks should reach DONE state."""
        wf = _wf(
            nodes=[("A", "proc"), ("B", "proc"), ("C", "proc")],
            edges=[("A:out", "B:in"), ("B:out", "C:in")],
        )
        scheduler, _event_bus, _runner = _make_scheduler(wf)

        asyncio.run(scheduler.execute())

        assert scheduler._block_states["A"] == BlockState.DONE
        assert scheduler._block_states["B"] == BlockState.DONE
        assert scheduler._block_states["C"] == BlockState.DONE

    def test_scheduler_linear_execution_order(self) -> None:
        """A->B->C: runner.run() called in correct order."""
        wf = _wf(
            nodes=[("A", "proc"), ("B", "proc"), ("C", "proc")],
            edges=[("A:out", "B:in"), ("B:out", "C:in")],
        )
        call_order: list[str] = []

        async def track_run(block: object, inputs: dict, config: dict) -> dict:
            call_order.append(block.id)  # type: ignore[attr-defined]
            return {"output": f"result_{block.id}"}  # type: ignore[attr-defined]

        scheduler, _event_bus, runner = _make_scheduler(wf)
        runner.run.side_effect = track_run

        asyncio.run(scheduler.execute())

        assert call_order == ["A", "B", "C"]

    def test_scheduler_runner_called_with_correct_args(self) -> None:
        """Runner receives node, inputs, and config."""
        wf = _wf(nodes=[("A", "proc")])
        wf.nodes[0].config = {"param": "value"}
        scheduler, _event_bus, runner = _make_scheduler(wf)

        asyncio.run(scheduler.execute())

        runner.run.assert_called_once()
        args = runner.run.call_args
        assert args[0][0].id == "A"
        assert args[0][1] == {}
        assert args[0][2] == {"param": "value"}


# ---------------------------------------------------------------------------
# Empty workflow
# ---------------------------------------------------------------------------


class TestSchedulerEmpty:
    """Test empty workflow handling."""

    def test_scheduler_empty_workflow(self) -> None:
        """Empty workflow completes immediately without calling runner."""
        wf = _wf(nodes=[])
        scheduler, event_bus, runner = _make_scheduler(wf)

        events_received: list[str] = []
        event_bus.subscribe(
            WORKFLOW_STARTED,
            lambda e: events_received.append(WORKFLOW_STARTED),
        )
        event_bus.subscribe(
            WORKFLOW_COMPLETED,
            lambda e: events_received.append(WORKFLOW_COMPLETED),
        )

        asyncio.run(scheduler.execute())

        assert WORKFLOW_STARTED in events_received
        assert WORKFLOW_COMPLETED in events_received
        runner.run.assert_not_called()


# ---------------------------------------------------------------------------
# Error and skip propagation
# ---------------------------------------------------------------------------


class TestSchedulerErrorPropagation:
    """Test error handling and skip propagation."""

    def test_scheduler_error_skips_downstream(self) -> None:
        """A(error)->B->C: B and C should be SKIPPED."""
        wf = _wf(
            nodes=[("A", "proc"), ("B", "proc"), ("C", "proc")],
            edges=[("A:out", "B:in"), ("B:out", "C:in")],
        )

        async def fail_on_a(block: object, inputs: dict, config: dict) -> dict:
            if block.id == "A":  # type: ignore[attr-defined]
                raise RuntimeError("Block A failed")
            return {"output": "ok"}

        scheduler, _event_bus, runner = _make_scheduler(wf)
        runner.run.side_effect = fail_on_a

        asyncio.run(scheduler.execute())

        assert scheduler._block_states["A"] == BlockState.ERROR
        assert scheduler._block_states["B"] == BlockState.SKIPPED
        assert scheduler._block_states["C"] == BlockState.SKIPPED
        assert "A" in scheduler.skip_reasons["B"]
        assert "A" in scheduler.skip_reasons["C"]

    def test_scheduler_diamond_partial_error(self) -> None:
        """Diamond A->B,C->D: if B errors but C succeeds, D is skipped."""
        wf = _wf(
            nodes=[
                ("A", "proc"),
                ("B", "proc"),
                ("C", "proc"),
                ("D", "proc"),
            ],
            edges=[
                ("A:out", "B:in"),
                ("A:out", "C:in"),
                ("B:out", "D:in1"),
                ("C:out", "D:in2"),
            ],
        )

        async def fail_on_b(block: object, inputs: dict, config: dict) -> dict:
            if block.id == "B":  # type: ignore[attr-defined]
                raise RuntimeError("Block B failed")
            return {"output": "ok"}

        scheduler, _event_bus, runner = _make_scheduler(wf)
        runner.run.side_effect = fail_on_b

        asyncio.run(scheduler.execute())

        assert scheduler._block_states["A"] == BlockState.DONE
        assert scheduler._block_states["B"] == BlockState.ERROR
        assert scheduler._block_states["C"] == BlockState.DONE
        assert scheduler._block_states["D"] == BlockState.SKIPPED


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------


class TestSchedulerCancellation:
    """Test block and workflow cancellation."""

    def test_scheduler_cancel_block_skips_downstream(self) -> None:
        """Cancel a block -> downstream gets SKIPPED."""
        wf = _wf(
            nodes=[("A", "proc"), ("B", "proc"), ("C", "proc")],
            edges=[("A:out", "B:in"), ("B:out", "C:in")],
        )
        scheduler, event_bus, _runner = _make_scheduler(wf)

        scheduler._block_states["A"] = BlockState.DONE
        scheduler._block_outputs["A"] = {"out": "data"}
        scheduler._block_states["B"] = BlockState.RUNNING

        asyncio.run(event_bus.emit(EngineEvent(event_type=CANCEL_BLOCK_REQUEST, block_id="B")))

        assert scheduler._block_states["B"] == BlockState.CANCELLED
        assert scheduler._block_states["C"] == BlockState.SKIPPED
        assert "B" in scheduler.skip_reasons["C"]

    def test_scheduler_cancel_workflow(self) -> None:
        """Cancel workflow -> non-terminal blocks cancelled/skipped."""
        wf = _wf(
            nodes=[("A", "proc"), ("B", "proc"), ("C", "proc")],
            edges=[("A:out", "B:in"), ("B:out", "C:in")],
        )
        scheduler, event_bus, _runner = _make_scheduler(wf)

        scheduler._block_states["A"] = BlockState.DONE
        scheduler._block_outputs["A"] = {"out": "data"}
        scheduler._block_states["B"] = BlockState.RUNNING
        scheduler._block_states["C"] = BlockState.IDLE

        asyncio.run(event_bus.emit(EngineEvent(event_type=CANCEL_WORKFLOW_REQUEST)))

        assert scheduler._block_states["A"] == BlockState.DONE
        assert scheduler._block_states["B"] == BlockState.CANCELLED
        assert scheduler._block_states["C"] == BlockState.SKIPPED


# ---------------------------------------------------------------------------
# Pause / Resume
# ---------------------------------------------------------------------------


class TestSchedulerPauseResume:
    """Test pause and resume functionality."""

    def test_pause_prevents_dispatch(self) -> None:
        """When paused, _dispatch does not run blocks."""
        wf = _wf(nodes=[("A", "proc")])
        scheduler, _event_bus, runner = _make_scheduler(wf)

        async def _run() -> None:
            await scheduler.pause()
            await scheduler._dispatch("A")

        asyncio.run(_run())

        runner.run.assert_not_called()

    def test_resume_dispatches_ready_blocks(self) -> None:
        """After resume, idle blocks with dependencies met get dispatched."""
        wf = _wf(
            nodes=[("A", "proc"), ("B", "proc")],
            edges=[("A:out", "B:in")],
        )
        scheduler, _event_bus, runner = _make_scheduler(wf)

        scheduler._block_states["A"] = BlockState.DONE
        scheduler._block_outputs["A"] = {"out": "data"}
        scheduler._block_states["B"] = BlockState.IDLE

        asyncio.run(scheduler.resume())

        assert scheduler._block_states["B"] == BlockState.DONE
        runner.run.assert_called_once()


# ---------------------------------------------------------------------------
# Event emission
# ---------------------------------------------------------------------------


class TestSchedulerEvents:
    """Test that the scheduler emits correct lifecycle events."""

    def test_workflow_events_emitted(self) -> None:
        """WORKFLOW_STARTED and WORKFLOW_COMPLETED are emitted."""
        wf = _wf(nodes=[("A", "proc")])
        scheduler, event_bus, _runner = _make_scheduler(wf)

        events_received: list[str] = []
        event_bus.subscribe(
            WORKFLOW_STARTED,
            lambda e: events_received.append(WORKFLOW_STARTED),
        )
        event_bus.subscribe(
            WORKFLOW_COMPLETED,
            lambda e: events_received.append(WORKFLOW_COMPLETED),
        )

        asyncio.run(scheduler.execute())

        assert events_received == [WORKFLOW_STARTED, WORKFLOW_COMPLETED]

    def test_block_done_event_emitted(self) -> None:
        """BLOCK_DONE event is emitted for each completed block."""
        wf = _wf(nodes=[("A", "proc"), ("B", "proc")])
        scheduler, event_bus, _runner = _make_scheduler(wf)

        done_blocks: list[str] = []
        event_bus.subscribe(
            BLOCK_DONE,
            lambda e: done_blocks.append(e.block_id) if e.block_id else None,
        )

        asyncio.run(scheduler.execute())

        assert "A" in done_blocks
        assert "B" in done_blocks


# ---------------------------------------------------------------------------
# Input gathering
# ---------------------------------------------------------------------------


class TestSchedulerInputGathering:
    """Test that inputs are gathered correctly from upstream outputs."""

    def test_inputs_passed_from_upstream(self) -> None:
        """B receives output from A via edge mapping."""
        wf = _wf(
            nodes=[("A", "proc"), ("B", "proc")],
            edges=[("A:result", "B:data")],
        )

        received_inputs: list[dict] = []

        async def capture_inputs(block: object, inputs: dict, config: dict) -> dict:
            if block.id == "B":  # type: ignore[attr-defined]
                received_inputs.append(inputs)
            return {"result": f"output_{block.id}"}  # type: ignore[attr-defined]

        scheduler, _event_bus, runner = _make_scheduler(wf)
        runner.run.side_effect = capture_inputs

        asyncio.run(scheduler.execute())

        assert len(received_inputs) == 1
        assert "data" in received_inputs[0]
        assert received_inputs[0]["data"] == "output_A"


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------


class TestSchedulerState:
    """Test state management helpers."""

    def test_set_state(self) -> None:
        """set_state overrides block state."""
        wf = _wf(nodes=[("A", "proc")])
        scheduler, _, _ = _make_scheduler(wf)

        scheduler.set_state("A", BlockState.DONE)
        assert scheduler._block_states["A"] == BlockState.DONE

    def test_save_checkpoint_does_not_raise(self) -> None:
        """save_checkpoint is a no-op placeholder, should not raise."""
        wf = _wf(nodes=[("A", "proc")])
        scheduler, _, _ = _make_scheduler(wf)
        scheduler.save_checkpoint()
