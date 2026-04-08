"""RegionProps — extract per-label measurements as a DataFrame.

Skeleton placeholder — T-IMG-024 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-024.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_imaging.types import Image, Label


class RegionProps(ProcessBlock):
    """Compute per-label region properties (area, centroid, intensity stats, ...).

    Per spec §9 T-IMG-024, accepts a :class:`Label` and an optional
    intensity :class:`Image` and emits a :class:`DataFrame` with one row
    per labelled object. The ``label_id`` column is always first; an
    ``image_index`` column is added when the input is a Collection.
    """

    type_name: ClassVar[str] = "imaging.region_props"
    name: ClassVar[str] = "Region Properties"
    description: ClassVar[str] = "Compute per-label region properties (area, centroid, intensity stats) as a DataFrame."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "measurement"
    algorithm: ClassVar[str] = "region_props"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="label", accepted_types=[Label], description="Label image."),
        InputPort(
            name="intensity_image",
            accepted_types=[Image],
            required=False,
            description="Optional intensity image for intensity_* properties.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="properties",
            accepted_types=[DataFrame],
            description="Per-label measurement table.",
        ),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "properties": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["area", "centroid", "bbox"],
                "description": "skimage.measure.regionprops_table property names.",
            },
        },
    }

    def process_item(
        self,
        item: Label,
        config: BlockConfig,
        state: Any = None,
    ) -> DataFrame:
        raise NotImplementedError(
            "T-IMG-024: RegionProps.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-024."
        )
