"""SubWorkflowBlock — runs an entire workflow as a single block."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig

if TYPE_CHECKING:
    from scieasy.core.types.collection import Collection
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState
from scieasy.core.types.base import DataObject


class SubWorkflowBlock(Block):
    """Block that encapsulates a full workflow as a single composable unit.

    *workflow_ref* points to the nested workflow definition (YAML path or ID).
    *input_mapping* translates parent port names to child workflow input names.
    *output_mapping* translates child workflow output names to parent port names.

    The engine layer injects ``_scheduler_factory`` at startup so that child
    workflows can use the real DAG scheduler without blocks/ importing engine/.
    When no factory is injected, execution falls back to the sequential stub.

    .. note::

        Full async DAG scheduling requires the engine's event loop (Phase 5.2b
        worker.py).  The ``_run_with_scheduler`` method currently delegates to
        ``_sequential_execute`` as a placeholder until the worker integration
        is complete.
    """

    workflow_ref: ClassVar[str] = ""
    input_mapping: ClassVar[dict[str, str]] = {}
    output_mapping: ClassVar[dict[str, str]] = {}

    # Engine injects this at startup (avoids import-linter violation:
    # blocks cannot import engine).
    _scheduler_factory: ClassVar[Any] = None

    name: ClassVar[str] = "Sub-Workflow"
    description: ClassVar[str] = "Encapsulate a full workflow as a single block"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="data", accepted_types=[DataObject], required=False, description="Input to child workflow"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="result", accepted_types=[DataObject], description="Output from child workflow"),
    ]

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        """Execute the referenced sub-workflow.

        1. Load child workflow definition from *workflow_ref* or config.
        2. Map parent inputs to child inputs via *input_mapping*.
        3. Use real scheduler if ``_scheduler_factory`` is set, else fallback
           to :func:`_sequential_execute`.
        4. Map child outputs to parent outputs via *output_mapping*.

        .. note::

            ADR-017 requires child block execution to use subprocess isolation.
            This is enforced by the engine's LocalRunner, not by the block itself.
        """
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

        # Use real scheduler if available, else fallback to sequential.
        if self._scheduler_factory is not None:
            child_outputs = self._run_with_scheduler(child_inputs, config)
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

        return results

    def _run_with_scheduler(self, child_inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute child workflow using injected scheduler factory.

        The engine layer sets ``_scheduler_factory`` at startup, avoiding
        the import-linter constraint (blocks cannot import engine).

        For now, delegates to ``_sequential_execute`` as the real async
        scheduler integration requires the engine's event loop (Phase 5.2b
        worker.py).  The worker recognises ``SubWorkflowBlock`` and creates
        a child scheduler.
        """
        child_blocks = config.get("child_blocks") or []
        return _sequential_execute(child_blocks, child_inputs)


def _sequential_execute(
    blocks: list[Block],
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Execute *blocks* in order, threading outputs as inputs to the next.

    Collections (ADR-020) flow through the shared namespace unchanged —
    child blocks receive them as-is without unwrapping.

    This is a fallback executor.  The real DAG scheduler is injected via
    ``SubWorkflowBlock._scheduler_factory`` by the engine layer.
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
