"""Tests for DAGScheduler — linear, branching, and diamond DAG execution."""

from __future__ import annotations

import pytest

from scieasy.blocks.base.state import BlockState
from scieasy.engine.events import EventBus
from scieasy.engine.scheduler import DAGScheduler
from scieasy.workflow.definition import EdgeDef, NodeDef, WorkflowDefinition
from tests.engine.conftest import (
    AddOneBlock,
    DoubleBlock,
    FailingBlock,
    MergeBlock,
    SinkBlock,
    SourceBlock,
    make_test_registry,
)


@pytest.fixture()
def registry():
    return make_test_registry(SourceBlock, AddOneBlock, DoubleBlock, SinkBlock, MergeBlock, FailingBlock)


class TestDAGSchedulerLinear:
    """3-block linear pipeline: Source -> AddOne -> Sink."""

    @pytest.mark.asyncio
    async def test_linear_pipeline(self, registry) -> None:
        wf = WorkflowDefinition(
            id="linear",
            nodes=[
                NodeDef(id="src", block_type="Source", config={"params": {"value": 10}}),
                NodeDef(id="add", block_type="AddOne"),
                NodeDef(id="sink", block_type="Sink"),
            ],
            edges=[
                EdgeDef(source="src:data", target="add:x"),
                EdgeDef(source="add:x", target="sink:data"),
            ],
        )
        bus = EventBus()
        scheduler = DAGScheduler(wf, registry=registry, event_bus=bus)
        outputs = await scheduler.execute()

        assert outputs["src"] == {"data": 10}
        assert outputs["add"] == {"x": 11}
        assert outputs["sink"] == {"result": 11}

        # Verify all blocks are DONE.
        for state in scheduler.block_states.values():
            assert state == BlockState.DONE

        # Verify events were emitted.
        event_types = [e.event_type for e in bus.history]
        assert "workflow_started" in event_types
        assert "workflow_complete" in event_types
        assert event_types.count("block_state_changed") >= 3


class TestDAGSchedulerBranching:
    """Branching DAG: Source -> AddOne, Source -> Double, both -> Sink."""

    @pytest.mark.asyncio
    async def test_branching_dag(self, registry) -> None:
        wf = WorkflowDefinition(
            id="branch",
            nodes=[
                NodeDef(id="src", block_type="Source", config={"params": {"value": 5}}),
                NodeDef(id="add", block_type="AddOne"),
                NodeDef(id="dbl", block_type="Double"),
                NodeDef(id="merge", block_type="MergeSum"),
            ],
            edges=[
                EdgeDef(source="src:data", target="add:x"),
                EdgeDef(source="src:data", target="dbl:x"),
                EdgeDef(source="add:x", target="merge:left"),
                EdgeDef(source="dbl:x", target="merge:right"),
            ],
        )
        scheduler = DAGScheduler(wf, registry=registry)
        outputs = await scheduler.execute()

        # Source produces 5; AddOne -> 6; Double -> 10; Merge -> 16.
        assert outputs["src"] == {"data": 5}
        assert outputs["add"] == {"x": 6}
        assert outputs["dbl"] == {"x": 10}
        assert outputs["merge"] == {"merged": 16}


class TestDAGSchedulerDiamond:
    """Diamond DAG: A -> B, A -> C, B -> D, C -> D."""

    @pytest.mark.asyncio
    async def test_diamond_dag(self, registry) -> None:
        wf = WorkflowDefinition(
            id="diamond",
            nodes=[
                NodeDef(id="A", block_type="Source", config={"params": {"value": 3}}),
                NodeDef(id="B", block_type="AddOne"),
                NodeDef(id="C", block_type="Double"),
                NodeDef(id="D", block_type="MergeSum"),
            ],
            edges=[
                EdgeDef(source="A:data", target="B:x"),
                EdgeDef(source="A:data", target="C:x"),
                EdgeDef(source="B:x", target="D:left"),
                EdgeDef(source="C:x", target="D:right"),
            ],
        )
        scheduler = DAGScheduler(wf, registry=registry)
        outputs = await scheduler.execute()

        # A=3, B=4, C=6, D=10.
        assert outputs["D"] == {"merged": 10}


class TestDAGSchedulerError:
    """Error handling in scheduler."""

    @pytest.mark.asyncio
    async def test_block_failure_raises(self, registry) -> None:
        wf = WorkflowDefinition(
            id="fail",
            nodes=[
                NodeDef(id="src", block_type="Source", config={"params": {"value": 1}}),
                NodeDef(id="fail", block_type="Failing"),
            ],
            edges=[EdgeDef(source="src:data", target="fail:x")],
        )
        bus = EventBus()
        scheduler = DAGScheduler(wf, registry=registry, event_bus=bus)

        with pytest.raises(RuntimeError, match="failed"):
            await scheduler.execute()

        assert scheduler.block_states["fail"] == BlockState.ERROR

        event_types = [e.event_type for e in bus.history]
        assert "workflow_error" in event_types


class TestDAGSchedulerPauseResume:
    """Pause/resume semantics."""

    @pytest.mark.asyncio
    async def test_pause_returns_checkpoint(self, registry) -> None:
        wf = WorkflowDefinition(
            id="pause-test",
            nodes=[
                NodeDef(id="src", block_type="Source", config={"params": {"value": 1}}),
            ],
        )
        scheduler = DAGScheduler(wf, registry=registry)
        checkpoint = await scheduler.pause()
        assert checkpoint.workflow_id == "pause-test"
        assert "src" in checkpoint.block_states

    @pytest.mark.asyncio
    async def test_resume_skips_completed(self, registry) -> None:
        wf = WorkflowDefinition(
            id="resume-test",
            nodes=[
                NodeDef(id="src", block_type="Source", config={"params": {"value": 7}}),
                NodeDef(id="add", block_type="AddOne"),
            ],
            edges=[EdgeDef(source="src:data", target="add:x")],
        )
        scheduler = DAGScheduler(wf, registry=registry)

        # Manually mark src as done with outputs, simulating partial completion.
        scheduler.set_state("src", BlockState.DONE)
        scheduler._outputs["src"] = {"data": 7}

        outputs = await scheduler.execute()
        # AddOne should still run, getting data=7 from src.
        assert outputs["add"] == {"x": 8}
