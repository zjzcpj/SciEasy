"""ComputeRegistration — estimate a Transform aligning a moving Image to a fixed Image.

Skeleton placeholder — T-IMG-027 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-027.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image, Transform


class ComputeRegistration(ProcessBlock):
    """Estimate a :class:`Transform` aligning ``moving`` to ``fixed``."""

    type_name: ClassVar[str] = "imaging.compute_registration"
    name: ClassVar[str] = "Compute Registration"
    description: ClassVar[str] = (
        "Estimate a Transform that aligns a moving Image to a fixed Image (rigid / affine / phase correlation)."
    )
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "registration"
    algorithm: ClassVar[str] = "compute_registration"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="moving", accepted_types=[Image], description="Moving image to be aligned."),
        InputPort(name="fixed", accepted_types=[Image], description="Reference image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="transform", accepted_types=[Transform], description="Estimated transform."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["phase_correlation", "rigid", "affine"],
                "default": "phase_correlation",
            },
        },
    }

    def process_item(
        self,
        item: Image,
        config: BlockConfig,
        state: Any = None,
    ) -> Transform:
        raise NotImplementedError(
            "T-IMG-027: ComputeRegistration.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-027."
        )
