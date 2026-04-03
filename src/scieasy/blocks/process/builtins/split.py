"""SplitBlock — filter, subset, train-test split."""

from __future__ import annotations

from typing import Any

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.process.process_block import ProcessBlock


class SplitBlock(ProcessBlock):
    """Filter, subset, or train-test split input data."""

    name = "Split"
    algorithm = "split"

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        raise NotImplementedError
