"""RidgeFilter — frangi / meijering / sato / hessian (T-IMG-014).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-014.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


class RidgeFilter(ProcessBlock):
    """Ridge / vesselness filters on 2D ``(y, x)`` slices."""

    type_name: ClassVar[str] = "imaging.ridge_filter"
    name: ClassVar[str] = "Ridge Filter"
    description: ClassVar[str] = "Ridge / vesselness filtering (Frangi / Meijering / Sato / Hessian)."
    category: ClassVar[str] = "morphology"
    algorithm: ClassVar[str] = "ridge_filter"

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
                "enum": ["frangi", "meijering", "sato", "hessian"],
                "default": "frangi",
            },
            "sigma_min": {"type": "number", "default": 1.0},
            "sigma_max": {"type": "number", "default": 10.0},
            "num_sigma": {"type": "integer", "default": 10},
        },
        "required": ["method"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-014 RidgeFilter.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-014."
        )
