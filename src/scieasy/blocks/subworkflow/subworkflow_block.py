"""SubWorkflowBlock — runs an entire workflow as a single block."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState
from scieasy.core.types.base import DataObject


class SubWorkflowBlock(Block):
    """Block that encapsulates a full workflow as a single composable unit.

    *workflow_ref* points to the nested workflow definition (YAML path or ID).
    *input_mapping* translates parent port names to child workflow input names.
    *output_mapping* translates child workflow output names to parent port names.

    .. note::

        Full DAG scheduling depends on Phase 5 (engine).  This implementation
        uses a simple sequential executor stub that processes child blocks in
        declaration order.
    """

    workflow_ref: ClassVar[str] = ""
    input_mapping: ClassVar[dict[str, str]] = {}
    output_mapping: ClassVar[dict[str, str]] = {}

    name: ClassVar[str] = "Sub-Workflow"
    description: ClassVar[str] = "Encapsulate a full workflow as a single block"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="data", accepted_types=[DataObject], required=False, description="Input to child workflow"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="result", accepted_types=[DataObject], description="Output from child workflow"),
    ]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the referenced sub-workflow.

        Uses a simple sequential executor stub:
        1. Load child workflow definition from *workflow_ref* or config.
        2. Map parent inputs to child inputs via *input_mapping*.
        3. Execute child blocks in order via :func:`_sequential_execute`.
        4. Map child outputs to parent outputs via *output_mapping*.
        """
        self.transition(BlockState.RUNNING)
        try:
            child_blocks = config.get("child_blocks") or []
            in_map = config.get("input_mapping") or self.input_mapping or {}
            out_map = config.get("output_mapping") or self.output_mapping or {}

            # Map parent inputs to child namespace.
            child_inputs: dict[str, Any] = {}
            for parent_key, child_key in in_map.items():
                if parent_key in inputs:
                    child_inputs[child_key] = inputs[parent_key]

            # Also pass through any unmapped inputs.
            for key, value in inputs.items():
                if key not in in_map:
                    child_inputs[key] = value

            # Execute child blocks sequentially (stub — real engine in Phase 5).
            child_outputs = _sequential_execute(child_blocks, child_inputs)

            # Map child outputs to parent outputs.
            results: dict[str, Any] = {}
            for child_key, parent_key in out_map.items():
                if child_key in child_outputs:
                    results[parent_key] = child_outputs[child_key]

            # Also pass through any unmapped outputs.
            for key, value in child_outputs.items():
                if key not in out_map:
                    results[key] = value

            self.transition(BlockState.DONE)
            return results
        except Exception:
            self.transition(BlockState.ERROR)
            raise


def _sequential_execute(
    blocks: list[Block],
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Execute *blocks* in order, threading outputs as inputs to the next.

    This is a temporary stub.  Phase 5 will replace it with the real
    DAG scheduler.  For now, each block's outputs are merged into a
    shared namespace that the next block reads from.
    """
    namespace = dict(inputs)

    for block in blocks:
        block.transition(BlockState.READY)
        block_inputs: dict[str, Any] = {}
        for port in block.input_ports:
            if port.name in namespace:
                block_inputs[port.name] = namespace[port.name]
            elif not port.required and port.default is not None:
                block_inputs[port.name] = port.default

        outputs = block.run(block_inputs, block.config)
        outputs = block.postprocess(outputs)
        namespace.update(outputs)

    return namespace
