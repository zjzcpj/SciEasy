"""SliceCollection — extract a sub-range from a Collection.

ADR-021: Built-in utility block for Collection operations.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.base import DataObject


class SliceCollection(ProcessBlock):
    """Extract sub-range [start:end] from a Collection.

    TODO(ADR-021): Implement.
    - Config: start: int, end: int.
    - Static ports: input (Collection), output (Collection).
    """

    name: ClassVar[str] = "Slice Collection"
    algorithm: ClassVar[str] = "slice_collection"
    description: ClassVar[str] = "Extract a sub-range from a Collection"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="input", accepted_types=[DataObject], description="Collection to slice"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="output", accepted_types=[DataObject], description="Sliced Collection"),
    ]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        # TODO(ADR-021): Slice items[start:end]. Return sliced Collection.
        raise NotImplementedError
