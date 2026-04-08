"""Label/Mask cleanup bundle (T-IMG-022).

Five small ProcessBlocks bundled in one module per spec §9 T-IMG-022:

- :class:`RemoveSmallObjects` — drop labels/mask blobs below ``min_size`` pixels
- :class:`RemoveBorderObjects` — drop labels touching the image border
- :class:`FillHoles` — fill interior holes in a :class:`Mask`
- :class:`ExpandLabels` — dilate labels by ``distance_px``
- :class:`ShrinkLabels` — erode labels by ``distance_px``

Skeleton placeholder — T-IMG-022 implementation agent fills the bodies.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-022.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Label, Mask


class RemoveSmallObjects(ProcessBlock):
    """Remove connected components smaller than ``min_size`` pixels."""

    type_name: ClassVar[str] = "imaging.remove_small_objects"
    name: ClassVar[str] = "Remove Small Objects"
    description: ClassVar[str] = "Drop labels/mask blobs below min_size pixels."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "segmentation"
    algorithm: ClassVar[str] = "remove_small_objects"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="label", accepted_types=[Label, Mask], description="Label or Mask."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="label", accepted_types=[Label, Mask], description="Filtered Label or Mask."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "min_size": {"type": "integer", "default": 64, "minimum": 1},
        },
    }

    def process_item(self, item: Label | Mask, config: BlockConfig, state: Any = None) -> Label | Mask:
        raise NotImplementedError(
            "T-IMG-022: RemoveSmallObjects.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-022."
        )


class RemoveBorderObjects(ProcessBlock):
    """Remove labels that touch the image border."""

    type_name: ClassVar[str] = "imaging.remove_border_objects"
    name: ClassVar[str] = "Remove Border Objects"
    description: ClassVar[str] = "Drop labels that touch the image border (clear_border)."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "segmentation"
    algorithm: ClassVar[str] = "clear_border"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="label", accepted_types=[Label], description="Input Label image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="label", accepted_types=[Label], description="Border-cleared Label."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {"type": "object", "properties": {}}

    def process_item(self, item: Label, config: BlockConfig, state: Any = None) -> Label:
        raise NotImplementedError(
            "T-IMG-022: RemoveBorderObjects.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-022."
        )


class FillHoles(ProcessBlock):
    """Fill interior holes in a binary :class:`Mask`."""

    type_name: ClassVar[str] = "imaging.fill_holes"
    name: ClassVar[str] = "Fill Holes"
    description: ClassVar[str] = "Fill interior holes of a binary Mask (binary_fill_holes)."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "segmentation"
    algorithm: ClassVar[str] = "binary_fill_holes"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="mask", accepted_types=[Mask], description="Input Mask."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="mask", accepted_types=[Mask], description="Hole-filled Mask."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {"type": "object", "properties": {}}

    def process_item(self, item: Mask, config: BlockConfig, state: Any = None) -> Mask:
        raise NotImplementedError(
            "T-IMG-022: FillHoles.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-022."
        )


class ExpandLabels(ProcessBlock):
    """Dilate labels by ``distance_px`` pixels (skimage expand_labels)."""

    type_name: ClassVar[str] = "imaging.expand_labels"
    name: ClassVar[str] = "Expand Labels"
    description: ClassVar[str] = "Dilate labels outwards by distance_px pixels."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "segmentation"
    algorithm: ClassVar[str] = "expand_labels"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="label", accepted_types=[Label], description="Input Label image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="label", accepted_types=[Label], description="Expanded Label image."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "distance_px": {"type": "integer", "default": 5, "minimum": 1},
        },
    }

    def process_item(self, item: Label, config: BlockConfig, state: Any = None) -> Label:
        raise NotImplementedError(
            "T-IMG-022: ExpandLabels.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-022."
        )


class ShrinkLabels(ProcessBlock):
    """Erode each label inwards by ``distance_px`` pixels."""

    type_name: ClassVar[str] = "imaging.shrink_labels"
    name: ClassVar[str] = "Shrink Labels"
    description: ClassVar[str] = "Erode labels inwards by distance_px pixels."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "segmentation"
    algorithm: ClassVar[str] = "shrink_labels"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="label", accepted_types=[Label], description="Input Label image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="label", accepted_types=[Label], description="Shrunk Label image."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "distance_px": {"type": "integer", "default": 1, "minimum": 1},
        },
    }

    def process_item(self, item: Label, config: BlockConfig, state: Any = None) -> Label:
        raise NotImplementedError(
            "T-IMG-022: ShrinkLabels.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-022."
        )
