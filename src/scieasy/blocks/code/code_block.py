"""CodeBlock — inline and script mode execution with language dispatch."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig


class CodeBlock(Block):
    """Block for executing user-provided scripts in Python, R, or Julia.

    *language* selects the runner; *mode* is ``"inline"`` or ``"script"``.
    """

    language: ClassVar[str] = "python"
    mode: ClassVar[str] = "inline"

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the code block via the appropriate language runner."""
        raise NotImplementedError
