"""SubWorkflowBlock — runs an entire workflow as a single block."""

from __future__ import annotations

import asyncio
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

    Uses the DAGScheduler from the engine for real DAG-based execution.
    Falls back to the sequential executor if no WorkflowDefinition is provided.
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

        If a ``workflow_definition`` is present in config, uses the
        DAGScheduler for proper DAG-based execution.  Otherwise, falls
        back to the sequential executor for simple child_blocks lists.
        """
        self.transition(BlockState.RUNNING)
        try:
            workflow_def = config.get("workflow_definition")
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

            if workflow_def is not None:
                child_outputs = _dag_execute(workflow_def, child_inputs)
            else:
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


def _dag_execute(
    workflow_def: Any,
    initial_inputs: dict[str, Any],
) -> dict[str, Any]:
    """Execute a child workflow using the DAGScheduler.

    Runs the scheduler in a new event loop if none is running,
    or uses asyncio.run() for simplicity in synchronous context.
    """
    from scieasy.engine.scheduler import DAGScheduler

    registry = _build_inline_registry(workflow_def, initial_inputs)
    scheduler = DAGScheduler(workflow_def, registry=registry)

    # Inject initial inputs as outputs of source nodes.
    for node_id, outputs in initial_inputs.items():
        if node_id in scheduler._outputs:
            continue
        if isinstance(outputs, dict):
            scheduler._outputs[node_id] = outputs

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            all_outputs = pool.submit(asyncio.run, scheduler.execute()).result()
    else:
        all_outputs = asyncio.run(scheduler.execute())

    # Merge all node outputs into a flat namespace.
    merged: dict[str, Any] = {}
    for _node_id, node_outputs in all_outputs.items():
        if isinstance(node_outputs, dict):
            merged.update(node_outputs)
    return merged


def _build_inline_registry(workflow_def: Any, initial_inputs: Any) -> Any:
    """Build a minimal BlockRegistry if the workflow_def carries inline block classes."""
    # This is a hook for testing and simple cases. Real usage would provide
    # a full BlockRegistry to the DAGScheduler.
    return None


def _sequential_execute(
    blocks: list[Block],
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Execute *blocks* in order, threading outputs as inputs to the next.

    This is a fallback for simple cases where a full WorkflowDefinition
    is not available (e.g. when child_blocks is a list of Block instances).
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
