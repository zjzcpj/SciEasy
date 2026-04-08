"""AxisSplit / AxisMerge — split or merge images along an axis (T-IMG-010).

Two related blocks bundled in a single module. Skeleton (Sprint C
continuation A). See ``docs/specs/phase11-imaging-block-spec.md`` §9
T-IMG-010.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy_blocks_imaging.types import Image


class AxisSplit(ProcessBlock):
    """Split an :class:`Image` along one axis into a Collection of (N-1)D images."""

    type_name: ClassVar[str] = "imaging.axis_split"
    name: ClassVar[str] = "Axis Split"
    description: ClassVar[str] = "Split an image along an axis into a Collection."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "axis_split"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="images", accepted_types=[Collection[Image]]),  # type: ignore[misc]
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "axis": {
                "type": "string",
                "enum": ["t", "z", "c", "lambda"],
            },
        },
        "required": ["axis"],
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Split the image (Tier 2 — emits a Collection of new objects)."""
        raise NotImplementedError(
            "T-IMG-010 AxisSplit.run — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-010."
        )


class AxisMerge(ProcessBlock):
    """Merge a Collection of (N-1)D :class:`Image` objects along a new axis."""

    type_name: ClassVar[str] = "imaging.axis_merge"
    name: ClassVar[str] = "Axis Merge"
    description: ClassVar[str] = "Merge a Collection of images into a single N-D image."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "axis_merge"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="images", accepted_types=[Collection[Image]], required=True),  # type: ignore[misc]
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "axis": {
                "type": "string",
                "enum": ["t", "z", "c", "lambda"],
            },
        },
        "required": ["axis"],
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Merge the collection (Tier 2 — many-to-one).

        Raises:
            ValueError: If shapes are inconsistent or axis ordering is invalid.
        """
        raise NotImplementedError(
            "T-IMG-010 AxisMerge.run — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-010."
        )
