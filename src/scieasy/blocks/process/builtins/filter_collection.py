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
    """Keep items whose metadata matches a key/value predicate.

    ADR-021: Filters by ``config.params["predicate_key"]`` and
    ``config.params["predicate_value"]``. Returns a Collection with the
    original item_type (may be empty).
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
        """Filter items by metadata key/value match.

        Config params:
            predicate_key (str): Metadata key to match on.
            predicate_value (Any): Value to compare against.

        Raises:
            TypeError: If input is not a Collection.
            ValueError: If predicate_key is not specified.
        """
        from scieasy.blocks.base.state import BlockState
        from scieasy.core.types.collection import Collection

        self.transition(BlockState.RUNNING)
        try:
            collection = inputs["input"]
            if not isinstance(collection, Collection):
                raise TypeError("FilterCollection requires a Collection input")
            predicate_key = config.params.get("predicate_key")
            if predicate_key is None:
                raise ValueError("FilterCollection requires 'predicate_key' in config.params")
            predicate_value = config.params.get("predicate_value")
            filtered = [item for item in collection if item.metadata.get(predicate_key) == predicate_value]
            result = Collection(filtered, item_type=collection.item_type)
            self.transition(BlockState.DONE)
            return {"output": result}
        except Exception:
            self.transition(BlockState.ERROR)
            raise
