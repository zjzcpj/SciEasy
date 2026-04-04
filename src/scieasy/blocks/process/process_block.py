"""ProcessBlock base — algorithm-driven data transformation."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig


class ProcessBlock(Block):
    """Block for deterministic, algorithm-driven data transformations.

    Subclasses should set *algorithm* to a human-readable identifier for the
    transformation they perform.  The base :meth:`validate` and
    :meth:`postprocess` are pass-through — override if needed.
    """

    algorithm: ClassVar[str] = ""

    # TODO(ADR-020-Add5): Add process_item() method — Tier 1 entry point.
    # Signature: def process_item(self, item: DataObject, config: BlockConfig) -> DataObject
    # 80% of blocks override this. Framework handles iteration, flush, packing.
    #
    # TODO(ADR-020-Add5): Replace current run() with default Collection-aware implementation:
    #   1. Get primary input Collection from inputs.
    #   2. For each item in Collection: call process_item(item, config).
    #   3. _auto_flush() each result to storage.
    #   4. Pack results into output Collection.
    #   Peak memory = O(1 item).
    #
    # TODO(ADR-020): run() receives and returns dict[str, Collection], not dict[str, DataObject].

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        """Execute the processing algorithm."""
        raise NotImplementedError(f"ProcessBlock subclass must implement run() [algorithm={self.algorithm}]")
