"""AppBlock — bridges external GUI software via file-exchange protocol."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.state import ExecutionMode


class AppBlock(Block):
    """Block that delegates work to an external GUI application.

    Communication happens via a file-exchange directory: the block serialises
    inputs, launches the application, watches for output files, and collects
    the results.
    """

    app_command: ClassVar[str] = ""
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Prepare inputs, launch the external app, and collect outputs."""
        raise NotImplementedError
