"""SplitCollection — split a Collection by index or condition.

ADR-021: Built-in utility block for Collection operations.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.base import DataObject


class SplitCollection(ProcessBlock):
    """Split Collection by index or condition into 2 Collections.

    TODO(ADR-021): Implement.
    - Config: split_index: int or condition: Callable.
    - Static ports: input (Collection), output_a (Collection), output_b (Collection).
    """

    name: ClassVar[str] = "Split Collection"
    algorithm: ClassVar[str] = "split_collection"
    description: ClassVar[str] = "Split a Collection by index or condition"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="input", accepted_types=[DataObject], description="Collection to split"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="output_a", accepted_types=[DataObject], description="First split"),
        OutputPort(name="output_b", accepted_types=[DataObject], description="Second split"),
    ]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        # TODO(ADR-021): Split by split_index or condition. Return two Collections.
        raise NotImplementedError
