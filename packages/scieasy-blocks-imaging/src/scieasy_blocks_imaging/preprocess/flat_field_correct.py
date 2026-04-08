"""FlatFieldCorrect — multi-input flat-field / shading correction (T-IMG-007).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-007.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy_blocks_imaging.types import Image


class FlatFieldCorrect(ProcessBlock):
    """Multi-input flat-field correction.

    Formula: ``out = (image - dark) / (flat - dark) * mean(flat - dark)``,
    where ``dark`` defaults to zeros if not provided. Methods:

    - ``basic``: literal formula above.
    - ``BaSiC``: BaSiC algorithm via the optional ``basicpy`` package.
    """

    type_name: ClassVar[str] = "imaging.flatfield_correct"
    name: ClassVar[str] = "Flat Field Correct"
    description: ClassVar[str] = "Correct uneven illumination using a flat-field reference."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "flatfield_correct"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
        InputPort(name="flat_field", accepted_types=[Image], required=True),
        InputPort(name="dark_frame", accepted_types=[Image], required=False),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["basic", "BaSiC"],
                "default": "basic",
            },
        },
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Apply flat-field correction (Tier 2 — multi-input)."""
        raise NotImplementedError(
            "T-IMG-007 FlatFieldCorrect.run — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-007."
        )
