"""Geometry bundle — Rotate / Flip / Crop / Pad / Resize (T-IMG-008).

Five small geometric transformation blocks bundled into a single
module per the imaging spec. Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-008.

Per Q-IMG-3, ``Resize`` updates ``Image.Meta.pixel_size`` proportionally
to the shape change.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock

from scieasy_blocks_imaging.types import Image, Mask


class Rotate(ProcessBlock):
    """Rotate by an arbitrary angle (degrees)."""

    type_name: ClassVar[str] = "imaging.rotate"
    name: ClassVar[str] = "Rotate"
    description: ClassVar[str] = "Rotate image by an arbitrary angle (degrees)."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "rotate"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "angle": {"type": "number", "default": 90.0},
            "interpolation": {
                "type": "string",
                "enum": ["nearest", "bilinear", "bicubic"],
                "default": "bilinear",
            },
        },
        "required": ["angle"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-008 Rotate.process_item — impl pending (skeleton continuation A)."
        )


class Flip(ProcessBlock):
    """Flip along a single axis (``t``/``z``/``c``/``lambda``/``y``/``x``)."""

    type_name: ClassVar[str] = "imaging.flip"
    name: ClassVar[str] = "Flip"
    description: ClassVar[str] = "Flip an image along one axis."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "flip"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "axis": {
                "type": "string",
                "enum": ["t", "z", "c", "lambda", "y", "x"],
            },
        },
        "required": ["axis"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-008 Flip.process_item — impl pending (skeleton continuation A)."
        )


class Crop(ProcessBlock):
    """Crop to a bounding box, optionally derived from a Mask input."""

    type_name: ClassVar[str] = "imaging.crop"
    name: ClassVar[str] = "Crop"
    description: ClassVar[str] = "Crop image to bounding box (or mask bbox)."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "crop"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
        InputPort(name="mask", accepted_types=[Mask], required=False),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "bbox": {
                "type": "array",
                "description": "[y_start, y_end, x_start, x_end]",
            },
        },
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-008 Crop.process_item — impl pending (skeleton continuation A)."
        )


class Pad(ProcessBlock):
    """Pad an image with constant / reflect / edge mode."""

    type_name: ClassVar[str] = "imaging.pad"
    name: ClassVar[str] = "Pad"
    description: ClassVar[str] = "Pad image edges (constant / reflect / edge)."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "pad"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "pad": {
                "type": "array",
                "description": "[top, bottom, left, right]",
            },
            "mode": {
                "type": "string",
                "enum": ["constant", "reflect", "edge"],
                "default": "constant",
            },
            "value": {"type": "number", "default": 0.0},
        },
        "required": ["pad"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-008 Pad.process_item — impl pending (skeleton continuation A)."
        )


class Resize(ProcessBlock):
    """Resize image; updates ``pixel_size`` per Q-IMG-3."""

    type_name: ClassVar[str] = "imaging.resize"
    name: ClassVar[str] = "Resize"
    description: ClassVar[str] = "Resize image to a target shape or scale factor."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "resize"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "target_shape": {"type": "array"},
            "factor": {"type": "number"},
            "interpolation": {
                "type": "string",
                "enum": ["nearest", "bilinear", "bicubic"],
                "default": "bilinear",
            },
        },
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-008 Resize.process_item — impl pending (skeleton continuation A). "
            "Per Q-IMG-3 the impl must update Image.Meta.pixel_size."
        )
