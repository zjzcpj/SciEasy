"""ProcessBlock base — algorithm-driven data transformation."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig


class ProcessBlock(Block):
    """Block for deterministic, algorithm-driven data transformations.

    Subclasses should set *algorithm* to a human-readable identifier for the
    transformation they perform.
    """

    algorithm: ClassVar[str] = ""

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the processing algorithm."""
        raise NotImplementedError
