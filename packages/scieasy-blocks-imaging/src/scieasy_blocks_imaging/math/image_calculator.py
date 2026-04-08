"""ImageCalculator — two-port image calculator with AST-restricted expression.

Per spec §9 T-IMG-032, 0.1.0 ships a 2-port FIXED block (inputs ``a`` and
``b``). Variadic inputs are deferred to ADR-029. The expression is parsed
through a restricted AST allowing only the names ``a`` and ``b`` plus
arithmetic operators.

Skeleton placeholder — T-IMG-032 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-032.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image


class ImageCalculator(ProcessBlock):
    """Two-input image calculator: ``out = expr(a, b)``.

    0.1.0: 2-port FIXED. Variadic deferred (see ADR-029).
    """

    type_name: ClassVar[str] = "imaging.image_calculator"
    name: ClassVar[str] = "Image Calculator"
    description: ClassVar[str] = "Two-input image calculator. Evaluate an AST-restricted expression in 'a' and 'b'."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "math"
    algorithm: ClassVar[str] = "image_calculator"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="a", accepted_types=[Image], description="Left operand."),
        InputPort(name="b", accepted_types=[Image], description="Right operand."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="result", accepted_types=[Image], description="Result image."),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "default": "a + b",
                "description": "AST-restricted expression in names 'a' and 'b'.",
            },
        },
    }

    def process_item(
        self,
        item: Image,
        config: BlockConfig,
        state: Any = None,
    ) -> Image:
        raise NotImplementedError(
            "T-IMG-032: ImageCalculator.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-032."
        )
