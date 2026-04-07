"""AIBlock — LLM-driven processing with prompt templates."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig

if TYPE_CHECKING:
    from scieasy.core.types.collection import Collection


class AIBlock(Block):
    """Block that uses a large language model to process data.

    *model* identifies the LLM backend; *prompt_template* holds the
    template string that is rendered with block inputs before inference.

    TODO(ADR-029): AIBlock is intended to support variadic input and
    output ports — the user designs the workflow with N inputs and M
    outputs by clicking "add port" / "remove port" controls in the GUI
    and declaring each port's name and accepted_types. ADR-029 (status:
    draft, scope pending discussion) reserves the namespace and lists
    the open questions for how variadic ports are stored, edited,
    validated, scheduled, and serialised through the worker subprocess.
    Until ADR-029 is promoted from `draft, scope pending` to `proposed`,
    AIBlock has empty class-level port lists and ``run()`` raises
    NotImplementedError. No method on this class should be added or
    modified to support variadic ports without an explicit ADR-029
    decision; reviewers may cite ADR-029 to reject any such PR.
    """

    model: ClassVar[str] = ""
    prompt_template: ClassVar[str] = ""

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        """Run the LLM inference pipeline.

        Not yet implemented — placeholder for AI-powered block execution.
        Per ADR-020, inputs and outputs will use Collection transport.
        """
        raise NotImplementedError
