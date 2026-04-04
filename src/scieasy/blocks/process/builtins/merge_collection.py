"""MergeCollection — concatenate two same-typed Collections.

ADR-021: Built-in utility block for Collection operations.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.base import DataObject


class MergeCollection(ProcessBlock):
    """Concatenate 2 same-typed Collections into 1.

    TODO(ADR-021): Implement.
    - Static ports: input_a, input_b (Collection), output (Collection).
    - Validates item_type match between input_a and input_b.
    - No dynamic ports. Merge 3+ Collections by chaining two MergeCollection blocks.
    """

    name: ClassVar[str] = "Merge Collection"
    algorithm: ClassVar[str] = "merge_collection"
    description: ClassVar[str] = "Concatenate two same-typed Collections into one"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="input_a", accepted_types=[DataObject], description="First Collection"),
        InputPort(name="input_b", accepted_types=[DataObject], description="Second Collection"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="output", accepted_types=[DataObject], description="Merged Collection"),
    ]

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        # TODO(ADR-021): Validate item_type match. Concatenate items. Return merged Collection.
        raise NotImplementedError
