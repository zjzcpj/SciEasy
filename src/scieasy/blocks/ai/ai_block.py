"""AIBlock — LLM-driven processing with prompt templates."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig


class AIBlock(Block):
    """Block that uses a large language model to process data.

    *model* identifies the LLM backend; *prompt_template* holds the
    template string that is rendered with block inputs before inference.
    """

    model: ClassVar[str] = ""
    prompt_template: ClassVar[str] = ""

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Run the LLM inference pipeline.

        Not yet implemented — placeholder for AI-powered block execution.
        Per ADR-020, inputs and outputs will use Collection transport.
        """
        raise NotImplementedError
