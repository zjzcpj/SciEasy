"""MetaboliteMatrix — pivot a long PeakTable into a wide compound x sample matrix (T-LCMS-013).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-013.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import PeakTable, SampleMetadata


class MetaboliteMatrix(_LCMSBlockMixin, ProcessBlock):
    """Pivot a long-format PeakTable to a wide compound x sample matrix.

    See spec §9 T-LCMS-013 for the 8 acceptance criteria.
    """

    name: ClassVar[str] = "Metabolite Matrix"
    type_name: ClassVar[str] = "metabolite_matrix"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "Pivot a long-format PeakTable into a wide compound x sample matrix. "
        "Missing combinations become NaN; imputation is the caller's responsibility."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="peak_table",
            accepted_types=[PeakTable],
            required=True,
            description="Long-format peak table",
        ),
        InputPort(
            name="sample_metadata",
            accepted_types=[SampleMetadata],
            required=False,
            description="Optional metadata to fix the column order",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="matrix",
            accepted_types=[DataFrame],
            description="Wide compound x sample DataFrame",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "value_column": {
                "type": "string",
                "default": "intensity",
                "title": "Value column",
                "ui_priority": 1,
            },
            "compound_column": {
                "type": "string",
                "default": "compound",
                "title": "Compound column",
                "ui_priority": 2,
            },
            "sample_column": {
                "type": "string",
                "default": "sample_id",
                "title": "Sample column",
                "ui_priority": 3,
            },
        },
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Pivot the long PeakTable to wide DataFrame."""
        raise NotImplementedError(
            "T-LCMS-013 MetaboliteMatrix.run — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-013."
        )
