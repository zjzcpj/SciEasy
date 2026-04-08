"""FractionalLabeling — ``1 - M+0`` per compound x sample (T-LCMS-009).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-009.

For multi-tracer experiments the M+0 row is the intersection across all
tracer-atom columns being zero. Output is long format with columns
``compound``, ``sample``, ``fractional_labeling``.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import MIDTable


class FractionalLabeling(_LCMSBlockMixin, ProcessBlock):
    """Compute ``1 - M+0`` per compound per sample.

    See spec §9 T-LCMS-009 for the 8 acceptance criteria.
    """

    name: ClassVar[str] = "Fractional Labeling"
    type_name: ClassVar[str] = "fractional_labeling"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "Compute fractional labeling (1 - M+0) per compound per sample. "
        "Multi-tracer M+0 = intersection of all tracer-atom columns being 0."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="mid_table",
            accepted_types=[MIDTable],
            required=True,
            description="Mass Isotopomer Distribution table (long format)",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="fractional_labeling",
            accepted_types=[DataFrame],
            description="Long-format DataFrame: compound, sample, fractional_labeling",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "compound_column": {
                "type": "string",
                "default": "Compound",
                "title": "Compound column name",
                "ui_priority": 1,
            },
        },
    }

    def process_item(
        self,
        item: MIDTable,
        config: BlockConfig,
        state: Any = None,
    ) -> DataFrame:
        """Emit the long-format fractional labelling DataFrame.

        Implementation must:

        * read ``tracer_atoms`` / ``sample_columns`` from ``item.meta``
        * select rows where every tracer-atom column equals 0 (M+0)
        * raise :class:`ValueError` if any compound is missing an M+0
          row (indicates upstream data corruption)
        * compute ``fractional_labeling = 1 - M+0[sample]`` per row
        """
        raise NotImplementedError(
            "T-LCMS-009 FractionalLabeling.process_item — impl pending "
            "(skeleton @ c08a885). See docs/specs/phase11-lcms-block-spec.md "
            "§9 T-LCMS-009."
        )
