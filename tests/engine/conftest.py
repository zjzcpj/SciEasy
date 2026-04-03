"""Shared fixtures and helper blocks for engine tests."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BatchMode, ExecutionMode
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.blocks.registry import BlockRegistry


class AddOneBlock(ProcessBlock):
    """Adds 1 to the input value."""

    name: ClassVar[str] = "AddOne"
    algorithm: ClassVar[str] = "add_one"
    input_ports: ClassVar[list[InputPort]] = [InputPort(name="x", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="x", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {"x": inputs["x"] + 1}


class DoubleBlock(ProcessBlock):
    """Doubles the input value."""

    name: ClassVar[str] = "Double"
    algorithm: ClassVar[str] = "double"
    input_ports: ClassVar[list[InputPort]] = [InputPort(name="x", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="x", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {"x": inputs["x"] * 2}


class SourceBlock(Block):
    """Produces a fixed output value from config."""

    name: ClassVar[str] = "Source"
    input_ports: ClassVar[list[InputPort]] = []
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="data", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {"data": config.get("value", 0)}


class SinkBlock(Block):
    """Consumes input and stores it in config for assertion."""

    name: ClassVar[str] = "Sink"
    input_ports: ClassVar[list[InputPort]] = [InputPort(name="data", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="result", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {"result": inputs.get("data")}


class MergeBlock(Block):
    """Merges two inputs by summing them."""

    name: ClassVar[str] = "MergeSum"
    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="left", accepted_types=[]),
        InputPort(name="right", accepted_types=[]),
    ]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="merged", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {"merged": inputs["left"] + inputs["right"]}


class FailingBlock(ProcessBlock):
    """Always raises an error."""

    name: ClassVar[str] = "Failing"
    algorithm: ClassVar[str] = "fail"
    input_ports: ClassVar[list[InputPort]] = [InputPort(name="x", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="x", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        raise ValueError("intentional failure")


class SerialBlock(ProcessBlock):
    """A block that declares SERIAL batch mode."""

    name: ClassVar[str] = "SerialProc"
    algorithm: ClassVar[str] = "serial"
    batch_mode: ClassVar[BatchMode] = BatchMode.SERIAL
    input_ports: ClassVar[list[InputPort]] = [InputPort(name="x", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="x", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {"x": inputs["x"] * 10}


class InteractiveBlock(ProcessBlock):
    """A block that declares INTERACTIVE execution mode."""

    name: ClassVar[str] = "InteractiveProc"
    algorithm: ClassVar[str] = "interactive"
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.INTERACTIVE
    input_ports: ClassVar[list[InputPort]] = [InputPort(name="x", accepted_types=[])]
    output_ports: ClassVar[list[OutputPort]] = [OutputPort(name="x", accepted_types=[])]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        return {"x": inputs["x"]}


def make_test_registry(*block_classes: type[Block]) -> BlockRegistry:
    """Create a BlockRegistry pre-loaded with the given block classes.

    Uses direct registration rather than file scanning.
    """
    from scieasy.blocks.registry import _spec_from_class

    registry = BlockRegistry()
    for cls in block_classes:
        spec = _spec_from_class(cls, source="test")
        spec.module_path = cls.__module__
        spec.class_name = cls.__name__
        registry._registry[spec.name] = spec
    return registry
