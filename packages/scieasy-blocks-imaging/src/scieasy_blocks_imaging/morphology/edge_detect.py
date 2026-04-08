"""EdgeDetect — sobel / scharr / canny / prewitt (T-IMG-013).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-013.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


class EdgeDetect(ProcessBlock):
    """Edge detection on 2D ``(y, x)`` slices."""

    type_name: ClassVar[str] = "imaging.edge_detect"
    name: ClassVar[str] = "Edge Detect"
    description: ClassVar[str] = "Detect edges via Sobel / Scharr / Canny / Prewitt."
    category: ClassVar[str] = "morphology"
    algorithm: ClassVar[str] = "edge_detect"

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
                "enum": ["sobel", "scharr", "canny", "prewitt"],
                "default": "sobel",
            },
            "sigma": {"type": "number", "default": 1.0},
            "low_threshold": {"type": "number", "default": 0.1},
            "high_threshold": {"type": "number", "default": 0.2},
        },
        "required": ["method"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-013 EdgeDetect.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-013."
        )
