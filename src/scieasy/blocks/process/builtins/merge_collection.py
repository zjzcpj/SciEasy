"""MergeCollection — concatenate two same-typed Collections.

ADR-021: Built-in utility block for Collection operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.base import DataObject

if TYPE_CHECKING:
    from scieasy.core.types.collection import Collection


class MergeCollection(ProcessBlock):
    """Concatenate 2 same-typed Collections into 1.

    ADR-021: Validates item_type match between input_a and input_b.
    No dynamic ports. Merge 3+ Collections by chaining two MergeCollection blocks.
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

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        """Concatenate two same-typed Collections.

        Raises:
            TypeError: If inputs are not Collections or have mismatched item_type.
        """
        from scieasy.blocks.base.state import BlockState
        from scieasy.core.types.collection import Collection

        self.transition(BlockState.RUNNING)
        try:
            input_a = inputs["input_a"]
            input_b = inputs["input_b"]
            if not isinstance(input_a, Collection) or not isinstance(input_b, Collection):
                raise TypeError("MergeCollection requires Collection inputs")
            if input_a.item_type != input_b.item_type:
                raise TypeError(
                    f"Cannot merge Collections with different item types: "
                    f"{input_a.item_type.__name__} vs {input_b.item_type.__name__}"
                )
            merged = Collection(list(input_a) + list(input_b), item_type=input_a.item_type)
            self.transition(BlockState.DONE)
            return {"output": merged}
        except Exception:
            self.transition(BlockState.ERROR)
            raise
