"""Rendering bundle (T-IMG-033) — five blocks producing :class:`Artifact` outputs.

- :class:`RenderPseudoColor` — false-colour LUT mapping
- :class:`RenderOverlay` — overlay labels / mask outlines on intensity image
- :class:`RenderMontage` — tile a Collection or stack into a montage
- :class:`RenderMovie` — encode a time-series as MP4
- :class:`RenderHistogram` — pixel intensity histogram as PNG/SVG

Skeleton placeholder — T-IMG-033 implementation agent fills the bodies.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-033.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.artifact import Artifact
from scieasy_blocks_imaging.types import Image, Label, Mask


class RenderPseudoColor(ProcessBlock):
    """Map a single-channel :class:`Image` through a colour LUT to a PNG :class:`Artifact`."""

    type_name: ClassVar[str] = "imaging.render_pseudo_color"
    name: ClassVar[str] = "Render Pseudo-color"
    description: ClassVar[str] = "Map a single-channel image through a colour LUT to a PNG artifact."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "visualization"
    algorithm: ClassVar[str] = "render_pseudo_color"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Single-channel image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="artifact", accepted_types=[Artifact], description="Rendered PNG artifact."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "lut": {"type": "string", "default": "viridis"},
            "vmin": {"type": ["number", "null"], "default": None},
            "vmax": {"type": ["number", "null"], "default": None},
        },
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Artifact:
        raise NotImplementedError(
            "T-IMG-033: RenderPseudoColor.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-033."
        )


class RenderOverlay(ProcessBlock):
    """Overlay :class:`Label` or :class:`Mask` outlines on an intensity :class:`Image`."""

    type_name: ClassVar[str] = "imaging.render_overlay"
    name: ClassVar[str] = "Render Overlay"
    description: ClassVar[str] = "Overlay Label / Mask outlines on an intensity image."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "visualization"
    algorithm: ClassVar[str] = "render_overlay"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Background intensity image."),
        InputPort(name="overlay", accepted_types=[Label, Mask], description="Label or Mask to overlay."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="artifact", accepted_types=[Artifact], description="Rendered artifact."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "alpha": {"type": "number", "default": 0.5, "minimum": 0.0, "maximum": 1.0},
            "outline_only": {"type": "boolean", "default": True},
        },
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Artifact:
        raise NotImplementedError(
            "T-IMG-033: RenderOverlay.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-033."
        )


class RenderMontage(ProcessBlock):
    """Tile multiple frames / channels into a single montage :class:`Artifact`."""

    type_name: ClassVar[str] = "imaging.render_montage"
    name: ClassVar[str] = "Render Montage"
    description: ClassVar[str] = "Tile multiple frames / channels into a single montage image."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "visualization"
    algorithm: ClassVar[str] = "render_montage"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Multi-frame image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="artifact", accepted_types=[Artifact], description="Montage PNG."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "axis": {"type": "string", "default": "t"},
            "ncols": {"type": ["integer", "null"], "default": None, "minimum": 1},
        },
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Artifact:
        raise NotImplementedError(
            "T-IMG-033: RenderMontage.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-033."
        )


class RenderMovie(ProcessBlock):
    """Encode a time-series :class:`Image` as an MP4 :class:`Artifact`."""

    type_name: ClassVar[str] = "imaging.render_movie"
    name: ClassVar[str] = "Render Movie"
    description: ClassVar[str] = "Encode a time-series image as an MP4 movie artifact."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "visualization"
    algorithm: ClassVar[str] = "render_movie"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Time-series image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="artifact", accepted_types=[Artifact], description="MP4 artifact."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "fps": {"type": "integer", "default": 10, "minimum": 1},
            "codec": {"type": "string", "default": "libx264"},
        },
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Artifact:
        raise NotImplementedError(
            "T-IMG-033: RenderMovie.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-033."
        )


class RenderHistogram(ProcessBlock):
    """Render a pixel intensity histogram as a PNG / SVG :class:`Artifact`."""

    type_name: ClassVar[str] = "imaging.render_histogram"
    name: ClassVar[str] = "Render Histogram"
    description: ClassVar[str] = "Render a pixel intensity histogram as a PNG / SVG artifact."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "visualization"
    algorithm: ClassVar[str] = "render_histogram"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Input image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="artifact", accepted_types=[Artifact], description="Histogram artifact."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "bins": {"type": "integer", "default": 256, "minimum": 2},
            "format": {"type": "string", "enum": ["png", "svg"], "default": "png"},
        },
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Artifact:
        raise NotImplementedError(
            "T-IMG-033: RenderHistogram.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-033."
        )
