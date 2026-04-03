"""IOBlock — loads and saves data in any supported format."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig


class IOBlock(Block):
    """Block for data ingress and egress with pluggable format adapters.

    Subclasses should set *direction* to ``"input"`` or ``"output"`` and
    *format* to the target file format identifier.
    """

    direction: ClassVar[str] = "input"
    format: ClassVar[str] = ""

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the IO operation (read or write)."""
        raise NotImplementedError
