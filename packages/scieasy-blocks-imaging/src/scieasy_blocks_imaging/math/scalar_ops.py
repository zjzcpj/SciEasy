"""Scalar arithmetic bundle (T-IMG-031).

Four trivially symmetric scalar arithmetic blocks bundled in one module:

- :class:`AddScalar`
- :class:`SubtractScalar`
- :class:`MultiplyScalar`
- :class:`DivideScalar`

Skeleton placeholder — T-IMG-031 implementation agent fills the bodies.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-031.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


def _scalar_schema(default: float = 0.0) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "value": {"type": "number", "default": default},
        },
    }


class AddScalar(ProcessBlock):
    """Add a scalar to every pixel of an :class:`Image`."""

    type_name: ClassVar[str] = "imaging.add_scalar"
    name: ClassVar[str] = "Add Scalar"
    description: ClassVar[str] = "Add a scalar to every pixel."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "math"
    algorithm: ClassVar[str] = "add_scalar"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Input image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image], description="Output image."),
    ]
    config_schema: ClassVar[dict[str, Any]] = _scalar_schema(0.0)

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-031: AddScalar.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-031."
        )


class SubtractScalar(ProcessBlock):
    """Subtract a scalar from every pixel of an :class:`Image`."""

    type_name: ClassVar[str] = "imaging.subtract_scalar"
    name: ClassVar[str] = "Subtract Scalar"
    description: ClassVar[str] = "Subtract a scalar from every pixel."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "math"
    algorithm: ClassVar[str] = "subtract_scalar"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Input image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image], description="Output image."),
    ]
    config_schema: ClassVar[dict[str, Any]] = _scalar_schema(0.0)

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-031: SubtractScalar.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-031."
        )


class MultiplyScalar(ProcessBlock):
    """Multiply every pixel of an :class:`Image` by a scalar."""

    type_name: ClassVar[str] = "imaging.multiply_scalar"
    name: ClassVar[str] = "Multiply Scalar"
    description: ClassVar[str] = "Multiply every pixel by a scalar."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "math"
    algorithm: ClassVar[str] = "multiply_scalar"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Input image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image], description="Output image."),
    ]
    config_schema: ClassVar[dict[str, Any]] = _scalar_schema(1.0)

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-031: MultiplyScalar.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-031."
        )


class DivideScalar(ProcessBlock):
    """Divide every pixel of an :class:`Image` by a scalar."""

    type_name: ClassVar[str] = "imaging.divide_scalar"
    name: ClassVar[str] = "Divide Scalar"
    description: ClassVar[str] = "Divide every pixel by a scalar (impl raises on zero)."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "math"
    algorithm: ClassVar[str] = "divide_scalar"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Input image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image], description="Output image."),
    ]
    config_schema: ClassVar[dict[str, Any]] = _scalar_schema(1.0)

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        raise NotImplementedError(
            "T-IMG-031: DivideScalar.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-031."
        )
