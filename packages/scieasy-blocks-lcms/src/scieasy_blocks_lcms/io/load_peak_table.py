"""LoadPeakTable — CSV/TSV/XLSX peak table loader (T-LCMS-004).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-004.

Reads a peak table from CSV / TSV / XLSX, auto-detects the source tool
(ElMAVEN / MZmine / XCMS) from column-name markers, and wraps the
result as a :class:`PeakTable`.

Source autodetection signatures (per spec):

* **ElMAVEN**: any of ``{"compound", "formula", "medMz", "medRt",
  "expectedRtDiff"}``.
* **MZmine**: any of ``{"row ID", "row m/z", "row retention time"}``.
* **XCMS**: any of ``{"mzmed", "rtmed", "mzmin", "mzmax"}``.
* Fallback: ``ElMAVEN`` (the user's primary tool).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import pandas as pd

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import OutputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import PeakTable

_ELMAVEN_COLUMNS = frozenset({"compound", "formula", "medMz", "medRt", "expectedRtDiff"})
_MZMINE_COLUMNS = frozenset({"row ID", "row m/z", "row retention time"})
_XCMS_COLUMNS = frozenset({"mzmed", "rtmed", "mzmin", "mzmax"})


class LoadPeakTable(_LCMSBlockMixin, IOBlock):
    """CSV/TSV/XLSX peak table loader with source autodetection.

    See spec §9 T-LCMS-004 for the 14 acceptance criteria.
    """

    direction: ClassVar[str] = "input"
    type_name: ClassVar[str] = "load_peak_table"
    name: ClassVar[str] = "Load Peak Table"
    category: ClassVar[str] = "io"
    description: ClassVar[str] = (
        "Load a peak table (CSV/TSV/XLSX) into a typed PeakTable. "
        "Auto-detects ElMAVEN / MZmine / XCMS column-name conventions."
    )

    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="peak_table",
            accepted_types=[PeakTable],
            description="Loaded peak table with source-tool tagged Meta",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "title": "Peak table file",
                "ui_priority": 0,
                "ui_widget": "file_browser",
            },
            "source": {
                "type": "string",
                "enum": ["auto", "ElMAVEN", "MZmine", "XCMS"],
                "default": "auto",
                "title": "Source tool",
                "ui_priority": 1,
            },
            "sheet_name": {
                "type": ["string", "integer", "null"],
                "default": None,
                "title": "XLSX sheet (name or index)",
                "ui_priority": 2,
            },
            "polarity": {
                "type": ["string", "null"],
                "enum": [None, "+", "-"],
                "default": None,
                "title": "Polarity (optional)",
                "ui_priority": 3,
            },
        },
        "required": ["path"],
    }

    def load(self, config: BlockConfig) -> DataObject | Collection:
        """Read the peak table file and return a :class:`PeakTable`.

        Implementation must:

        * raise :class:`FileNotFoundError` on missing file
        * raise :class:`ValueError` on empty table
        * detect ``.csv`` / ``.tsv`` / ``.xlsx`` / ``.xls`` by suffix
        * resolve ``source="auto"`` via the heuristics in the module
          docstring
        * cache the pandas DataFrame under
          ``peak_table.user["pandas_df"]`` for downstream reuse
        """
        path = Path(config.get("path"))
        if not path.exists():
            raise FileNotFoundError(f"LoadPeakTable: source file not found: {path}")

        frame = _read_table(path, sheet_name=config.get("sheet_name"))
        if frame.empty:
            raise ValueError(f"LoadPeakTable: table is empty: {path}")

        source = str(config.get("source", "auto"))
        resolved_source = _detect_source(frame.columns) if source == "auto" else source
        table = PeakTable(
            columns=[str(col) for col in frame.columns],
            row_count=len(frame),
            schema={str(col): str(dtype) for col, dtype in frame.dtypes.items()},
            meta=PeakTable.Meta(
                source=resolved_source,
                polarity=config.get("polarity"),
            ),
        )
        table.user["pandas_df"] = frame.copy()
        return Collection(items=[table], item_type=PeakTable)

    def save(self, obj: DataObject | Collection, config: BlockConfig) -> None:
        """Not supported — use :class:`SaveTable` for output."""
        raise NotImplementedError("T-LCMS-004 LoadPeakTable is direction='input'; use SaveTable to write.")


def _read_table(path: Path, *, sheet_name: str | int | None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=0 if sheet_name is None else sheet_name)
    raise ValueError(f"LoadPeakTable: unsupported file format: {path.suffix}")


def _detect_source(columns: pd.Index) -> str:
    names = {str(column) for column in columns}
    if names & _ELMAVEN_COLUMNS:
        return "ElMAVEN"
    if names & _MZMINE_COLUMNS:
        return "MZmine"
    if names & _XCMS_COLUMNS:
        return "XCMS"
    return "ElMAVEN"
