"""MorphologyOp — erode/dilate/open/close/tophat/bottomhat (T-IMG-012).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-012.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


class MorphologyOp(ProcessBlock):
    """Morphological operations on 2D ``(y, x)`` slices."""

    type_name: ClassVar[str] = "imaging.morphology_op"
    name: ClassVar[str] = "Morphology Op"
    description: ClassVar[str] = "Morphological operations: erode/dilate/open/close/tophat/bottomhat."
    category: ClassVar[str] = "morphology"
    algorithm: ClassVar[str] = "morphology"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "op": {
                "type": "string",
                "enum": ["erode", "dilate", "open", "close", "tophat", "bottomhat"],
                "default": "erode",
            },
            "selem_shape": {
                "type": "string",
                "enum": ["disk", "square", "cross"],
                "default": "disk",
            },
            "selem_size": {"type": "integer", "default": 3, "minimum": 1},
        },
        "required": ["op"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        """Apply a morphological operation per-slice.

        Raises:
            ValueError: For an unknown ``op``.
        """
        raise NotImplementedError(
            "T-IMG-012 MorphologyOp.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-012."
        )
