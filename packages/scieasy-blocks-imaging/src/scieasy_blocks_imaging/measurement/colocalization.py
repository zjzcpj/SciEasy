"""Colocalization — Pearson / Manders / Costes colocalization metrics.

Skeleton placeholder — T-IMG-026 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-026.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_imaging.types import Image, Mask


class Colocalization(ProcessBlock):
    """Compute Pearson / Manders / Costes colocalization metrics on two channels."""

    type_name: ClassVar[str] = "imaging.colocalization"
    name: ClassVar[str] = "Colocalization"
    description: ClassVar[str] = "Compute Pearson / Manders / Costes colocalization metrics for two intensity channels."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "measurement"
    algorithm: ClassVar[str] = "colocalization"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="channel_a", accepted_types=[Image], description="First intensity channel."),
        InputPort(name="channel_b", accepted_types=[Image], description="Second intensity channel."),
        InputPort(
            name="mask",
            accepted_types=[Mask],
            required=False,
            description="Optional region-of-interest mask.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="metrics",
            accepted_types=[DataFrame],
            description="One-row DataFrame with Pearson / Manders / Costes columns.",
        ),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "metrics": {
                "type": "array",
                "items": {"type": "string", "enum": ["pearson", "manders", "costes"]},
                "default": ["pearson", "manders"],
            },
        },
    }

    def process_item(
        self,
        item: Image,
        config: BlockConfig,
        state: Any = None,
    ) -> DataFrame:
        raise NotImplementedError(
            "T-IMG-026: Colocalization.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-026."
        )
