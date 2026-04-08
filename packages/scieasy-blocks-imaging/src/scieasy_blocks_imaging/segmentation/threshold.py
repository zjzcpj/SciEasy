"""Threshold — otsu / li / yen / isodata / mean / triangle / adaptive_otsu / manual (T-IMG-017).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-017.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image, Mask


class Threshold(ProcessBlock):
    """Single threshold block with multiple methods. Outputs a :class:`Mask`."""

    type_name: ClassVar[str] = "imaging.threshold"
    name: ClassVar[str] = "Threshold"
    description: ClassVar[str] = (
        "Threshold an image into a binary mask (otsu/li/yen/isodata/mean/triangle/adaptive_otsu/manual)."
    )
    category: ClassVar[str] = "segmentation"
    algorithm: ClassVar[str] = "threshold"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="mask", accepted_types=[Mask]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": [
                    "otsu",
                    "li",
                    "yen",
                    "isodata",
                    "mean",
                    "triangle",
                    "adaptive_otsu",
                    "manual",
                ],
                "default": "otsu",
            },
            "value": {
                "type": "number",
                "description": "Manual threshold value (for method=manual).",
            },
            "block_size": {
                "type": "integer",
                "default": 35,
                "description": "Window size for adaptive_otsu.",
            },
        },
        "required": ["method"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Mask:
        """Threshold to a binary mask.

        Raises:
            ValueError: For unknown ``method`` or ``manual`` without ``value``.
        """
        raise NotImplementedError(
            "T-IMG-017 Threshold.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-017."
        )
