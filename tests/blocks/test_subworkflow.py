"""Tests for SubWorkflowBlock — stub test with sequential executor."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.blocks.subworkflow.subworkflow_block import SubWorkflowBlock, _sequential_execute

# TODO(ADR-020): Update to pass/expect Collections.


class AddOneBlock(ProcessBlock):
    """Trivial block that adds 1 to input value."""

    name = "AddOne"
    algorithm = "add_one"

    input_ports: ClassVar[list[InputPort]] = [InputPort(name="x", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="x", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        self.transition(BlockState.RUNNING)
        result = {"x": inputs["x"] + 1}
        self.transition(BlockState.DONE)
        return result


class DoubleBlock(ProcessBlock):
    """Trivial block that doubles input value."""

    name = "Double"
    algorithm = "double"

    input_ports: ClassVar[list[InputPort]] = [InputPort(name="x", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="x", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        self.transition(BlockState.RUNNING)
        result = {"x": inputs["x"] * 2}
        self.transition(BlockState.DONE)
        return result


class TestSequentialExecute:
    """_sequential_execute — chains blocks in order."""

    def test_single_block(self) -> None:
        blocks = [AddOneBlock()]
        result = _sequential_execute(blocks, {"x": 10})
        assert result["x"] == 11

    def test_chain_two_blocks(self) -> None:
        blocks = [AddOneBlock(), DoubleBlock()]
        result = _sequential_execute(blocks, {"x": 5})
        # (5 + 1) * 2 = 12
        assert result["x"] == 12

    def test_empty_chain(self) -> None:
        result = _sequential_execute([], {"x": 42})
        assert result["x"] == 42


class TestSubWorkflowBlock:
    """SubWorkflowBlock — input/output mapping and child execution."""

    def test_with_child_blocks(self) -> None:
        child_blocks = [AddOneBlock(), DoubleBlock()]
        block = SubWorkflowBlock(
            config={
                "params": {
                    "child_blocks": child_blocks,
                    "input_mapping": {"data": "x"},
                    "output_mapping": {"x": "result"},
                }
            }
        )
        block.transition(BlockState.READY)
        result = block.run({"data": 10}, block.config)
        # (10 + 1) * 2 = 22
        assert result["result"] == 22

    def test_unmapped_passthrough(self) -> None:
        block = SubWorkflowBlock(config={"params": {"child_blocks": [], "input_mapping": {}, "output_mapping": {}}})
        block.transition(BlockState.READY)
        result = block.run({"extra": 99}, block.config)
        assert result["extra"] == 99

    def test_state_transitions(self) -> None:
        block = SubWorkflowBlock(config={"params": {"child_blocks": []}})
        block.transition(BlockState.READY)
        block.run({}, block.config)
        assert block.state == BlockState.DONE
