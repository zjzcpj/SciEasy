"""ConsumptionSecretionAnalysis — extracellular flux (T-LCMS-018).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-018 (NEW per user).

Computes per-compound delta concentration between spent media and the
average of fresh media controls. Optionally normalizes by per-sample
cell count + a fixed time window to produce per-cell-per-hour flux.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import PeakTable


class ConsumptionSecretionAnalysis(_LCMSBlockMixin, ProcessBlock):
    """Spent vs fresh media delta concentration with optional cell-count flux.

    See spec §9 T-LCMS-018 for the 10 acceptance criteria.
    """

    name: ClassVar[str] = "Consumption / Secretion Analysis"
    type_name: ClassVar[str] = "consumption_secretion_analysis"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "Compute per-compound delta concentration between spent media and "
        "averaged fresh media. Optional cell-count + time normalization "
        "produces per-cell-per-hour flux."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="spent_media",
            accepted_types=[PeakTable],
            required=True,
            description="Spent media intensities",
        ),
        InputPort(
            name="fresh_media",
            accepted_types=[PeakTable],
            required=True,
            description="Fresh media controls (averaged across samples)",
        ),
        InputPort(
            name="cell_count_table",
            accepted_types=[DataFrame],
            required=False,
            description="Optional per-sample cell count for flux normalization",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="flux",
            accepted_types=[DataFrame],
            description="Long-format DataFrame: compound, sample, delta_concentration, consumed_or_secreted, flux_per_cell_per_hour",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "time_hours": {
                "type": "number",
                "title": "Time window (hours)",
                "ui_priority": 1,
            },
            "normalize_per_cell": {
                "type": "boolean",
                "default": False,
                "title": "Normalize by cell count",
                "ui_priority": 2,
            },
            "intensity_column": {
                "type": "string",
                "default": "intensity",
                "title": "Intensity column",
                "ui_priority": 3,
            },
            "compound_column": {
                "type": "string",
                "default": "compound",
                "title": "Compound column",
                "ui_priority": 4,
            },
            "sample_column": {
                "type": "string",
                "default": "sample_id",
                "title": "Sample column",
                "ui_priority": 5,
            },
        },
        "required": ["time_hours"],
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Compute the consumption/secretion long-format DataFrame.

        Implementation must:

        * average fresh media intensities across samples per compound
        * compute ``delta = spent - mean(fresh)`` per (compound, sample)
        * set ``consumed_or_secreted = "consumed" if delta < 0 else "secreted"``
        * compute flux as ``delta / time_hours`` (or
          ``delta / (cell_count * time_hours)`` when normalizing)
        * raise :class:`ValueError` if spent and fresh share no
          compounds
        """
        raise NotImplementedError(
            "T-LCMS-018 ConsumptionSecretionAnalysis.run — impl pending "
            "(skeleton @ c08a885). See docs/specs/phase11-lcms-block-spec.md "
            "§9 T-LCMS-018."
        )
