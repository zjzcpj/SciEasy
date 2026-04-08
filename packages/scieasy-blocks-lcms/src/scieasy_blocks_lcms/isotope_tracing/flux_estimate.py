"""FluxEstimate — simple steady-state flux estimate (T-LCMS-011).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-011.

This is the **simplest possible** flux estimate:
``flux = labeling_rate x pool_size``, where ``labeling_rate`` is the
slope of a linear fit to fractional labelling vs. time and
``pool_size`` is the optional total compound abundance from a
:class:`PeakTable`.

This is **NOT a replacement for INCA, OpenFLUX, or Metran** — those
tools solve elementary metabolite unit (EMU) systems for proper
13C-MFA. Per master plan §2.4, full 13C-MFA is explicitly out of scope
for the SciEasy LC-MS plugin and should be handled by an external
tool.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import MIDTable, PeakTable, SampleMetadata


class FluxEstimate(_LCMSBlockMixin, ProcessBlock):
    """Naive steady-state flux estimate (labelling rate x pool size).

    NOT a replacement for full 13C-MFA — see INCA / OpenFLUX / Metran
    for proper EMU-based flux analysis.

    See spec §9 T-LCMS-011 for the 10 acceptance criteria.
    """

    name: ClassVar[str] = "Flux Estimate"
    type_name: ClassVar[str] = "flux_estimate"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "Naive steady-state flux estimate via linear fit to fractional "
        "labelling vs. time, multiplied by optional pool size. NOT a "
        "13C-MFA replacement; use INCA / OpenFLUX / Metran for that."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="mid_table",
            accepted_types=[MIDTable],
            required=True,
            description="MID table for fractional labelling computation",
        ),
        InputPort(
            name="sample_metadata",
            accepted_types=[SampleMetadata],
            required=True,
            description="Per-sample metadata with the time column",
        ),
        InputPort(
            name="pool_size_table",
            accepted_types=[PeakTable],
            required=False,
            description="Optional peak table providing per-compound pool sizes",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="flux",
            accepted_types=[DataFrame],
            description="Long-format DataFrame: compound, group, labeling_rate, pool_size, estimated_flux",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "time_points_column": {
                "type": "string",
                "default": "time_hours",
                "title": "Time column in sample metadata",
                "ui_priority": 1,
            },
            "group_column": {
                "type": ["string", "null"],
                "default": None,
                "title": "Group column (optional, splits the linear fit)",
                "ui_priority": 2,
            },
        },
        "required": ["time_points_column"],
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Compute the long-format flux estimate DataFrame.

        Implementation must:

        * raise :class:`ValueError` on fewer than 2 distinct timepoints
          per ``(compound, group)``
        * raise :class:`ValueError` on missing ``time_points_column``
        * fit ``fractional_labelling ~ time`` via ``numpy.polyfit``
          (degree 1) and use the slope as ``labeling_rate``
        * multiply by ``pool_size`` (averaged from
          ``pool_size_table`` per compound per group) when provided,
          else fall through to ``estimated_flux = labeling_rate``
        """
        raise NotImplementedError(
            "T-LCMS-011 FluxEstimate.run — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-011."
        )
