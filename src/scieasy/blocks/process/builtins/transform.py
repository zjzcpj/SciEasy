"""Simple built-in process block used by the API/frontend scaffolding."""

from __future__ import annotations

import time
from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.base import DataObject


class TransformBlock(ProcessBlock):
    """A minimal pass-through Process block with optional delay."""

    type_name: ClassVar[str] = "process_block"
    name: ClassVar[str] = "Process Block"
    description: ClassVar[str] = "A simple transform block for execution and frontend smoke tests."
    algorithm: ClassVar[str] = "transform"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="input", accepted_types=[DataObject], description="Primary input"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="output", accepted_types=[DataObject], description="Primary output"),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "sleep_seconds": {"type": "number", "default": 0, "title": "Sleep Seconds", "ui_priority": 1},
            "label": {"type": "string", "default": "", "title": "Label", "ui_priority": 2},
        },
    }

    def process_item(self, item: Any, config: BlockConfig) -> Any:
        """Return the item unchanged after an optional sleep."""
        sleep_seconds = float(config.get("sleep_seconds", 0) or 0)
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
        return item
