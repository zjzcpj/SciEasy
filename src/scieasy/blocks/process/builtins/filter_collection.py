"""FilterCollection — keep items matching a metadata predicate.

ADR-021: Built-in utility block for Collection operations.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.base import DataObject


class FilterCollection(ProcessBlock):
    """Keep items matching metadata predicate.

    TODO(ADR-021): Implement.
    - Config: predicate: Callable[[DataObject], bool].
    - Static ports: input (Collection), output (Collection).
    """

    name: ClassVar[str] = "Filter Collection"
    algorithm: ClassVar[str] = "filter_collection"
    description: ClassVar[str] = "Filter Collection items by metadata predicate"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="input", accepted_types=[DataObject], description="Collection to filter"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="output", accepted_types=[DataObject], description="Filtered Collection"),
    ]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        # TODO(ADR-021): Apply predicate to each item. Return filtered Collection.
        raise NotImplementedError
