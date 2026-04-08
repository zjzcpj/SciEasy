"""ConvertDType — uint8 / uint16 / float32 / float64 / bool (T-IMG-009).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-009.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


class ConvertDType(ProcessBlock):
    """Convert image dtype with optional rescaling or clipping."""

    type_name: ClassVar[str] = "imaging.convert_dtype"
    name: ClassVar[str] = "Convert DType"
    description: ClassVar[str] = "Convert image dtype (uint8/uint16/float32/float64/bool)."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "convert_dtype"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "target_dtype": {
                "type": "string",
                "enum": ["uint8", "uint16", "float32", "float64", "bool"],
                "default": "float32",
            },
            "rescale": {
                "type": "string",
                "enum": ["linear", "clip"],
                "default": "linear",
            },
        },
        "required": ["target_dtype"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        """Convert dtype.

        Raises:
            ValueError: For an unsupported ``target_dtype``.
        """
        raise NotImplementedError(
            "T-IMG-009 ConvertDType.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-009."
        )
