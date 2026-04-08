"""PairwiseDistance — pairwise distances between labelled objects.

Skeleton placeholder — T-IMG-025 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-025.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_imaging.types import Label


class PairwiseDistance(ProcessBlock):
    """Compute pairwise distances between labelled objects in a :class:`Label`.

    Returns a long-format :class:`DataFrame` with columns
    ``label_id_a``, ``label_id_b``, ``distance``.
    """

    type_name: ClassVar[str] = "imaging.pairwise_distance"
    name: ClassVar[str] = "Pairwise Distance"
    description: ClassVar[str] = "Compute pairwise distances between labelled objects (centroid or edge metric)."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "measurement"
    algorithm: ClassVar[str] = "pairwise_distance"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="label", accepted_types=[Label], description="Label image."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="distances",
            accepted_types=[DataFrame],
            description="Long-format distance table (label_id_a, label_id_b, distance).",
        ),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "metric": {
                "type": "string",
                "enum": ["centroid", "edge"],
                "default": "centroid",
            },
            "max_distance": {
                "type": ["number", "null"],
                "default": None,
                "description": "Optional cutoff; pairs above this are dropped.",
            },
        },
    }

    def process_item(
        self,
        item: Label,
        config: BlockConfig,
        state: Any = None,
    ) -> DataFrame:
        raise NotImplementedError(
            "T-IMG-025: PairwiseDistance.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-025."
        )
