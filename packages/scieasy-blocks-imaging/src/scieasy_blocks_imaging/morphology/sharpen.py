"""Sharpen — unsharp mask / laplacian (T-IMG-015).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-015.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


class Sharpen(ProcessBlock):
    """Sharpen 2D ``(y, x)`` slices via unsharp mask or Laplacian."""

    type_name: ClassVar[str] = "imaging.sharpen"
    name: ClassVar[str] = "Sharpen"
    description: ClassVar[str] = "Image sharpening (unsharp mask or Laplacian)."
    category: ClassVar[str] = "morphology"
    algorithm: ClassVar[str] = "sharpen"

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
                "enum": ["unsharp", "laplacian"],
                "default": "unsharp",
            },
            "amount": {"type": "number", "default": 1.0},
            "radius": {"type": "number", "default": 1.0},
        },
        "required": ["method"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-015 Sharpen.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-015."
        )
