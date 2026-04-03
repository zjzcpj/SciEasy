"""MergeBlock — merge, join, concatenate multi-input data."""

from __future__ import annotations

from typing import Any

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.process.process_block import ProcessBlock


class MergeBlock(ProcessBlock):
    """Merge, join, or concatenate multiple inputs."""

    name = "Merge"
    algorithm = "merge"

    def run(self, inputs: dict[str, Any], config: BlockConfig) -> dict[str, Any]:
        raise NotImplementedError
