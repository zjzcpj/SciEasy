"""ApplyTransform — warp an Image using a Transform.

Skeleton placeholder — T-IMG-028 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-028.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image, Transform


class ApplyTransform(ProcessBlock):
    """Apply a :class:`Transform` to an :class:`Image`, returning a warped Image."""

    type_name: ClassVar[str] = "imaging.apply_transform"
    name: ClassVar[str] = "Apply Transform"
    description: ClassVar[str] = "Warp an Image using a precomputed Transform."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "registration"
    algorithm: ClassVar[str] = "apply_transform"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Image to warp."),
        InputPort(name="transform", accepted_types=[Transform], description="Transform to apply."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="warped", accepted_types=[Image], description="Warped Image."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "interpolation": {
                "type": "string",
                "enum": ["nearest", "linear", "cubic"],
                "default": "linear",
            },
        },
    }

    def process_item(
        self,
        item: Image,
        config: BlockConfig,
        state: Any = None,
    ) -> Image:
        raise NotImplementedError(
            "T-IMG-028: ApplyTransform.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-028."
        )
