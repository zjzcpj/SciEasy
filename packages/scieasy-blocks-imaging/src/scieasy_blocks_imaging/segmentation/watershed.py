"""Watershed — distance / gradient / marker-based watershed (T-IMG-018).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-018.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy_blocks_imaging.types import Image, Label, Mask


class Watershed(ProcessBlock):
    """Watershed segmentation producing a :class:`Label` raster."""

    type_name: ClassVar[str] = "imaging.watershed"
    name: ClassVar[str] = "Watershed"
    description: ClassVar[str] = "Watershed segmentation (distance / gradient / markers)."
    category: ClassVar[str] = "segmentation"
    algorithm: ClassVar[str] = "watershed"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
        InputPort(name="mask", accepted_types=[Mask], required=False),
        InputPort(name="markers", accepted_types=[Label], required=False),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="label", accepted_types=[Label]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["distance", "gradient", "markers"],
                "default": "distance",
            },
            "min_distance": {"type": "integer", "default": 10},
            "compactness": {"type": "number", "default": 0.0},
        },
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Run watershed (Tier 2 — multi-input).

        Raises:
            ValueError: For unknown ``method`` or ``method=markers``
                without a ``markers`` input.
        """
        raise NotImplementedError(
            "T-IMG-018 Watershed.run — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-018."
        )
