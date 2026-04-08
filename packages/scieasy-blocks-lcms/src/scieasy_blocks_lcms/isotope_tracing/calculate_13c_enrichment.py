"""Calculate13CEnrichment — average tracer enrichment per compound × sample (T-LCMS-008).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-008.

This is the **flagship block** of the LC-MS plugin's isotope-tracing
USP. Formula (single tracer)::

    E[c, s] = sum_n(n * M+n[c, s]) / n_max[c]

where ``n_max[c]`` is the maximum tracer atom count row for compound
``c``. Multi-tracer case: one enrichment column per tracer atom. The
output is **long format** (one row per ``(compound, sample)``) per spec
§8 Q-3.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame

from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import MIDTable


class Calculate13CEnrichment(_LCMSBlockMixin, ProcessBlock):
    """Average 13C (or other tracer) enrichment per compound per sample.

    See spec §9 T-LCMS-008 for the 12 acceptance criteria, including
    the user's verbatim cytosine fixture.
    """

    name: ClassVar[str] = "Calculate 13C Enrichment"
    type_name: ClassVar[str] = "calculate_13c_enrichment"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "Average 13C (or other tracer) enrichment per compound per sample, "
        "computed as the weighted sum of M+n fractional abundances divided "
        "by the compound's maximum tracer atom count."
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
            name="enrichment",
            accepted_types=[DataFrame],
            description="Per-compound per-sample average enrichment (long format)",
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
        """Compute the long-format enrichment DataFrame.

        Implementation must:

        * read ``tracer_atoms`` and ``sample_columns`` from
          ``item.meta`` (single source of truth)
        * raise :class:`ValueError` on missing compound column
        * raise :class:`ValueError` on missing tracer-atom column
        * short-circuit ``n_max == 0`` to ``enrichment == 0.0``
        * emit columns ``compound``, ``sample``, ``enrichment`` (single
          tracer) or ``compound``, ``sample``, ``enrichment_{atom}``
          for each tracer (multi-tracer)
        """
        raise NotImplementedError(
            "T-LCMS-008 Calculate13CEnrichment.process_item — impl pending "
            "(skeleton @ c08a885). See docs/specs/phase11-lcms-block-spec.md "
            "§9 T-LCMS-008."
        )
