"""Normalize — minmax / zscore / percentile / histogram_match (T-IMG-006).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-006.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


class Normalize(ProcessBlock):
    """Intensity normalization with several methods."""

    type_name: ClassVar[str] = "imaging.normalize"
    name: ClassVar[str] = "Normalize"
    description: ClassVar[str] = "Rescale image intensities (minmax / zscore / percentile / histogram_match)."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "normalize"

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
                "enum": ["minmax", "zscore", "percentile", "histogram_match"],
                "default": "minmax",
            },
            "low_pct": {"type": "number", "default": 1.0},
            "high_pct": {"type": "number", "default": 99.0},
            "per_slice": {"type": "boolean", "default": True},
        },
        "required": ["method"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        """Normalize image intensities.

        Raises:
            ValueError: For unknown ``method``.
        """
        raise NotImplementedError(
            "T-IMG-006 Normalize.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-006."
        )
