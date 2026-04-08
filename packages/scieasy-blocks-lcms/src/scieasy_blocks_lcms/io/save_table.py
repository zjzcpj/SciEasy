"""SaveTable — generic DataFrame saver (T-LCMS-006 / part 2).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-006.

Generic sink block that writes any :class:`DataFrame` (including the
plugin-specific :class:`PeakTable`, :class:`MIDTable`,
:class:`SampleMetadata` subclasses via Liskov) to CSV / TSV / XLSX.

Per master plan §2.4 there is **NO** dedicated ``SaveMIDTable`` block —
this generic saver covers every output need.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_lcms._base import _LCMSBlockMixin


class SaveTable(_LCMSBlockMixin, IOBlock):
    """Generic CSV / TSV / XLSX sink for any :class:`DataFrame` subclass.

    See spec §9 T-LCMS-006 for the 8 acceptance criteria.
    """

    direction: ClassVar[str] = "output"
    type_name: ClassVar[str] = "save_table"
    name: ClassVar[str] = "Save Table"
    category: ClassVar[str] = "io"
    description: ClassVar[str] = (
        "Save any DataFrame (PeakTable / MIDTable / SampleMetadata / generic) to CSV, TSV, or XLSX."
    )

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="table",
            accepted_types=[DataFrame],
            required=True,
            description="DataFrame to save (any subclass accepted)",
        ),
    ]

    # Sink — produces no downstream artifacts.
    output_ports: ClassVar[list[Any]] = []

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "title": "Output file path",
                "ui_priority": 0,
                "ui_widget": "file_browser",
            },
            "format": {
                "type": "string",
                "enum": ["csv", "tsv", "xlsx"],
                "default": "csv",
                "title": "Format",
                "ui_priority": 1,
            },
            "index": {
                "type": "boolean",
                "default": False,
                "title": "Write row index",
                "ui_priority": 2,
            },
        },
        "required": ["path"],
    }

    def load(self, config: BlockConfig) -> DataObject | Collection:
        """Not supported — :class:`SaveTable` is output-only."""
        raise NotImplementedError("T-LCMS-006 SaveTable is direction='output'; load() is unreachable.")

    def save(self, obj: DataObject | Collection, config: BlockConfig) -> None:
        """Persist *obj* to the configured path.

        Implementation must:

        * create parent directories if they do not exist
        * dispatch to ``df.to_csv`` / ``df.to_csv(sep="\\t")`` /
          ``df.to_excel`` based on ``format``
        * respect ``index`` (default ``False``)
        * raise :class:`ValueError` on unknown ``format``
        * materialise the underlying pandas DataFrame from
          ``obj.user["pandas_df"]`` cache or ``obj.view().to_pandas()``
        """
        raise NotImplementedError(
            "T-LCMS-006 SaveTable.save — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-006."
        )
