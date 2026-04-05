"""ProcessBlock base — algorithm-driven data transformation."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig

if TYPE_CHECKING:
    from scieasy.core.types.collection import Collection


class ProcessBlock(Block):
    """Block for deterministic, algorithm-driven data transformations.

    Subclasses should set *algorithm* to a human-readable identifier for the
    transformation they perform.

    **Tier 1 (ADR-020-Add5)**: Override ``process_item()`` only. The default
    ``run()`` iterates the primary input Collection, calls ``process_item()``
    per item, auto-flushes each result, and packs into an output Collection.
    Peak memory = O(1 item).

    **Tier 2/3**: Override ``run()`` directly and use ``map_items()``,
    ``parallel_map()``, or ``pack()`` for Collection handling.
    """

    algorithm: ClassVar[str] = ""

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        """Default Collection-aware execution via process_item().

        Iterates the primary input Collection (first value in *inputs*),
        calls ``process_item()`` for each item, auto-flushes each result,
        and packs results into an output Collection on the first output port.

        Subclasses that need custom iteration or multi-port logic should
        override this method directly (Tier 2/3).
        """
        from scieasy.core.types.collection import Collection

        primary = next(iter(inputs.values()))

        # If primary is a Collection, iterate and process each item.
        if isinstance(primary, Collection):
            results = []
            for item in primary:
                result = self.process_item(item, config)
                result = self._auto_flush(result)
                results.append(result)
            output_name = self.output_ports[0].name if self.output_ports else "output"
            return {output_name: Collection(results, item_type=primary.item_type)}

        # Fallback for non-Collection inputs (backward compatibility).
        result = self.process_item(primary, config)
        output_name = self.output_ports[0].name if self.output_ports else "output"
        return {output_name: result}
