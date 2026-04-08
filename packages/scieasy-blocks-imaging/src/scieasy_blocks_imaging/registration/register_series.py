"""RegisterSeries — register a time-series or z-stack to a reference frame.

Skeleton placeholder — T-IMG-029 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-029.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


class RegisterSeries(ProcessBlock):
    """Register a time-series or z-stack so all frames align to a reference frame."""

    type_name: ClassVar[str] = "imaging.register_series"
    name: ClassVar[str] = "Register Series"
    description: ClassVar[str] = "Register a time-series or z-stack so each frame aligns to a chosen reference frame."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "registration"
    algorithm: ClassVar[str] = "register_series"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="series", accepted_types=[Image], description="Time-series / z-stack Image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="registered", accepted_types=[Image], description="Aligned series."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "axis": {"type": "string", "enum": ["t", "z"], "default": "t"},
            "reference_frame": {"type": "integer", "default": 0, "minimum": 0},
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
    ) -> Image:
        raise NotImplementedError(
            "T-IMG-029: RegisterSeries.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-029."
        )
