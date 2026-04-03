"""SubWorkflowBlock — runs an entire workflow as a single block."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig


class SubWorkflowBlock(Block):
    """Block that encapsulates a full workflow as a single composable unit.

    *workflow_ref* points to the nested workflow definition.
    *input_mapping* and *output_mapping* translate between the parent
    block's ports and the child workflow's external connections.
    """

    workflow_ref: ClassVar[str] = ""
    input_mapping: ClassVar[dict[str, str]] = {}
    output_mapping: ClassVar[dict[str, str]] = {}

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the referenced sub-workflow."""
        raise NotImplementedError
