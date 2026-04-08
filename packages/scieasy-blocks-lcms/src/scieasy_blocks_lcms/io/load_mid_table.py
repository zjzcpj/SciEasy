"""LoadMIDTable — AccuCor MID table loader (T-LCMS-005).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-005.

Loads the long-format MID table produced by AccuCor (or any tool that
emits the same shape) and auto-detects sample columns by excluding the
known identity columns and the known tracer-atom columns.

Spec sections referenced:

* §8 Q-3 — long format is canonical.
* §8 Q-4 — sample-column detection heuristic.
* §8 Q-5 — tracer atoms (single vs multi-tracer).
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import OutputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection

from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import MIDTable

#: Identity columns dropped from sample-column auto-detection.
_KNOWN_IDENTITY_COLUMNS = frozenset(
    {
        "Compound",
        "compound",
        "formula",
        "Formula",
        "mz",
        "MZ",
        "m/z",
        "rt",
        "RT",
        "retentionTime",
        "Adduct",
        "adduct",
        "name",
        "Name",
    }
)

#: Known tracer-atom columns dropped from sample-column auto-detection.
_KNOWN_ATOM_COLUMNS = frozenset(
    {
        "C13",
        "H2",
        "N15",
        "O18",
        "D",
        "S34",
        "Cl37",
    }
)


class LoadMIDTable(_LCMSBlockMixin, IOBlock):
    """Load an AccuCor-style long-format MID table into a :class:`MIDTable`.

    See spec §9 T-LCMS-005 for the 14 acceptance criteria, including
    the user's verbatim cytosine fixture.
    """

    direction: ClassVar[str] = "input"
    type_name: ClassVar[str] = "load_mid_table"
    name: ClassVar[str] = "Load MID Table"
    category: ClassVar[str] = "io"
    description: ClassVar[str] = (
        "Load a long-format Mass Isotopomer Distribution (MID) table from "
        "AccuCor output (CSV/TSV/XLSX) into a typed MIDTable."
    )

    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="mid_table",
            accepted_types=[MIDTable],
            description="Loaded MID table with detected sample columns",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "title": "MID table file",
                "ui_priority": 0,
                "ui_widget": "file_browser",
            },
            "tracer_atoms": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["C13"],
                "title": "Tracer atoms",
                "ui_priority": 1,
            },
            "sample_column_pattern": {
                "type": ["string", "null"],
                "default": None,
                "title": "Sample-column regex (override default heuristic)",
                "ui_priority": 2,
            },
            "sheet_name": {
                "type": ["string", "integer", "null"],
                "default": None,
                "title": "XLSX sheet (name or index)",
                "ui_priority": 3,
            },
        },
        "required": ["path"],
    }

    def load(self, config: BlockConfig) -> DataObject | Collection:
        """Read the MID table and return a :class:`MIDTable`.

        Implementation must:

        * raise :class:`FileNotFoundError` on missing file
        * raise :class:`ValueError` on missing ``Compound`` column
        * raise :class:`ValueError` on empty sample-column detection
        * apply the regex override when ``sample_column_pattern`` is set
        * fall back to the default heuristic
          (``columns - _KNOWN_IDENTITY_COLUMNS - _KNOWN_ATOM_COLUMNS -
          tracer_atoms``)
        * preserve ``corrected=True`` and
          ``correction_tool="AccuCor"`` defaults on the resulting
          :class:`MIDTable.Meta`
        """
        raise NotImplementedError(
            "T-LCMS-005 LoadMIDTable.load — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-005."
        )

    def save(self, obj: DataObject | Collection, config: BlockConfig) -> None:
        """Not supported — use :class:`SaveTable` for output."""
        raise NotImplementedError(
            "T-LCMS-005 LoadMIDTable is direction='input'; use SaveTable to write."
        )
