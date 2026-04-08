"""Axis projection bundle (T-IMG-030).

Two related blocks:

- :class:`AxisProjection` — collapse one axis with max/mean/sum/min/std
- :class:`SelectSlice` — single replacement for the OptEasy
  ``SelectChannel`` / ``CropTimeRange`` family; pick a single index
  along an arbitrary axis.

Skeleton placeholder — T-IMG-030 implementation agent fills the bodies.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-030.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


class AxisProjection(ProcessBlock):
    """Collapse one axis of an :class:`Image` using a reducer."""

    type_name: ClassVar[str] = "imaging.axis_projection"
    name: ClassVar[str] = "Axis Projection"
    description: ClassVar[str] = (
        "Collapse one axis (max / mean / sum / min / std) and return a lower-dimensional Image."
    )
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "projection"
    algorithm: ClassVar[str] = "axis_projection"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Input image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="projected", accepted_types=[Image], description="Projected image."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "axis": {"type": "string", "default": "z"},
            "method": {
                "type": "string",
                "enum": ["max", "mean", "sum", "min", "std"],
                "default": "max",
            },
        },
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-030: AxisProjection.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-030."
        )


class SelectSlice(ProcessBlock):
    """Pick a single index (or slice) along an arbitrary axis of an :class:`Image`."""

    type_name: ClassVar[str] = "imaging.select_slice"
    name: ClassVar[str] = "Select Slice"
    description: ClassVar[str] = (
        "Select a single index along an axis (replaces SelectChannel / CropTimeRange / SelectZ)."
    )
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "projection"
    algorithm: ClassVar[str] = "select_slice"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Input image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="slice", accepted_types=[Image], description="Selected slice."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "axis": {"type": "string", "default": "c"},
            "index": {"type": "integer", "default": 0, "minimum": 0},
        },
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-030: SelectSlice.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-030."
        )
