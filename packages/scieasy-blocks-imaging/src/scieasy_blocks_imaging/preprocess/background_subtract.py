"""BackgroundSubtract — rollingball / tophat / polynomial / constant (T-IMG-005).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-005.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock

from scieasy_blocks_imaging.types import Image


class BackgroundSubtract(ProcessBlock):
    """Subtract estimated background from each ``(y, x)`` slice."""

    type_name: ClassVar[str] = "imaging.background_subtract"
    name: ClassVar[str] = "Background Subtract"
    description: ClassVar[str] = (
        "Subtract image background via rolling-ball / top-hat / polynomial / constant."
    )
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "background_subtract"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["rollingball", "tophat", "polynomial", "constant"],
                "default": "rollingball",
            },
            "radius": {"type": "integer", "default": 25, "minimum": 1},
            "degree": {"type": "integer", "default": 2, "minimum": 0},
            "value": {"type": "number", "default": 0.0},
            "clip_to_zero": {"type": "boolean", "default": True},
        },
        "required": ["method"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        """Subtract background slice-wise.

        Raises:
            ValueError: If ``method`` is unknown or ``radius < 1``.
        """
        raise NotImplementedError(
            "T-IMG-005 BackgroundSubtract.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-005."
        )
