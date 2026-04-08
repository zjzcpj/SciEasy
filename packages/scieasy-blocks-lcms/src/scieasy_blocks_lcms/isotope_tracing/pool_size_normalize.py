"""PoolSizeNormalize — IS / TIC / median normalization for PeakTables (T-LCMS-012).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-012.

Three methods:

* **IS** — divide every sample's intensity by the intensity of a
  reference compound in that sample. Requires ``reference_compound``.
* **TIC** — divide every sample's intensity by the total ion current.
* **median** — divide by the per-sample median across all compounds.

Output preserves the input :class:`PeakTable`'s :attr:`Meta` so
downstream blocks still see a typed PeakTable.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import PeakTable


class PoolSizeNormalize(_LCMSBlockMixin, ProcessBlock):
    """Normalize a :class:`PeakTable` by IS / TIC / median.

    See spec §9 T-LCMS-012 for the 8 acceptance criteria.
    """

    name: ClassVar[str] = "Pool Size Normalize"
    type_name: ClassVar[str] = "pool_size_normalize"
    category: ClassVar[str] = "process"
    description: ClassVar[str] = (
        "Normalize a PeakTable by internal standard, total ion current, "
        "or per-sample median. Output is a PeakTable with preserved Meta."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="peak_table",
            accepted_types=[PeakTable],
            required=True,
            description="Peak table to normalize",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="normalized",
            accepted_types=[PeakTable],
            description="Normalized peak table (same Meta as input)",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["IS", "TIC", "median"],
                "default": "TIC",
                "title": "Normalization method",
                "ui_priority": 1,
            },
            "reference_compound": {
                "type": ["string", "null"],
                "default": None,
                "title": "Reference compound (required for IS mode)",
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
        },
    }

    def process_item(
        self,
        item: PeakTable,
        config: BlockConfig,
        state: Any = None,
    ) -> PeakTable:
        """Normalize *item* and return a new :class:`PeakTable`.

        Implementation must:

        * raise :class:`ValueError` if ``method == "IS"`` and
          ``reference_compound`` is unset or absent from the table
        * preserve ``item.meta`` (source, polarity) on the output
        * preserve the :class:`PeakTable` type (Liskov)
        """
        raise NotImplementedError(
            "T-LCMS-012 PoolSizeNormalize.process_item — impl pending "
            "(skeleton @ c08a885). See docs/specs/phase11-lcms-block-spec.md "
            "§9 T-LCMS-012."
        )
