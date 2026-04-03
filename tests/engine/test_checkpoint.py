"""Tests for checkpoint save/load and pause-resume-resume correctness."""

from __future__ import annotations

import pytest

from scieasy.blocks.base.state import BlockState
from scieasy.engine.checkpoint import WorkflowCheckpoint, load_checkpoint, save_checkpoint
from scieasy.engine.scheduler import DAGScheduler
from scieasy.workflow.definition import EdgeDef, NodeDef, WorkflowDefinition
from tests.engine.conftest import AddOneBlock, DoubleBlock, SourceBlock, make_test_registry


class TestCheckpointSerialization:
    """save_checkpoint / load_checkpoint round-trip."""

    def test_round_trip(self, tmp_path) -> None:
        from datetime import datetime

        ckpt = WorkflowCheckpoint(
            workflow_id="wf-1",
            timestamp=datetime(2025, 1, 15, 12, 0, 0),
            block_states={"A": "done", "B": "idle"},
            intermediate_refs={"A": {"data": 42}},
            pending_block="B",
            config_snapshot={"key": "value"},
        )
        path = tmp_path / "checkpoint.json"
        save_checkpoint(ckpt, path)
        loaded = load_checkpoint(path)

        assert loaded.workflow_id == "wf-1"
        assert loaded.timestamp == datetime(2025, 1, 15, 12, 0, 0)
        assert loaded.block_states == {"A": "done", "B": "idle"}
        assert loaded.intermediate_refs == {"A": {"data": 42}}
        assert loaded.pending_block == "B"
        assert loaded.config_snapshot == {"key": "value"}

    def test_round_trip_no_optional_fields(self, tmp_path) -> None:
        from datetime import datetime

        ckpt = WorkflowCheckpoint(
            workflow_id="minimal",
            timestamp=datetime.now(),
            block_states={"X": "idle"},
        )
        path = tmp_path / "ckpt2.json"
        save_checkpoint(ckpt, path)
        loaded = load_checkpoint(path)
        assert loaded.workflow_id == "minimal"
        assert loaded.pending_block is None


class TestPauseResumeCorrectResult:
    """Pause mid-execution -> serialise -> resume -> correct result."""

    @pytest.mark.asyncio
    async def test_pause_serialize_resume(self, tmp_path) -> None:
        registry = make_test_registry(SourceBlock, AddOneBlock, DoubleBlock)

        wf = WorkflowDefinition(
            id="pause-resume",
            nodes=[
                NodeDef(id="src", block_type="Source", config={"params": {"value": 5}}),
                NodeDef(id="add", block_type="AddOne"),
                NodeDef(id="dbl", block_type="Double"),
            ],
            edges=[
                EdgeDef(source="src:data", target="add:x"),
                EdgeDef(source="add:x", target="dbl:x"),
            ],
        )

        # Run full, then simulate pause after src.
        scheduler = DAGScheduler(wf, registry=registry)

        # Manually run first node and mark done.
        scheduler.set_state("src", BlockState.DONE)
        scheduler._outputs["src"] = {"data": 5}

        # Create checkpoint after partial execution.
        checkpoint = scheduler._make_checkpoint()
        ckpt_path = tmp_path / "ckpt.json"
        save_checkpoint(checkpoint, ckpt_path)

        # Load checkpoint into a fresh scheduler.
        loaded = load_checkpoint(ckpt_path)
        scheduler2 = DAGScheduler(wf, registry=registry)
        outputs = await scheduler2.resume(checkpoint=loaded)

        # src was done (skipped), add and dbl should run.
        assert outputs["add"] == {"x": 6}
        assert outputs["dbl"] == {"x": 12}
