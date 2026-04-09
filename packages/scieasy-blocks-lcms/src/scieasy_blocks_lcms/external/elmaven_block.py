"""ElMAVENBlock — AppBlock wrapper for ElMAVEN (T-LCMS-007 / part 1).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-007.

Reuses :meth:`AppBlock.run` verbatim (per ADR-018 / ADR-019) and only
specialises ClassVars + the export classifier. Per spec §8 Q-2 the
block does **not** script ElMAVEN's UI — the user opens files, runs
peak detection, and exports manually; :class:`FileWatcher` collects the
exports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, cast

from scieasy.blocks.app.app_block import AppBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState, ExecutionMode
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.io.load_mid_table import LoadMIDTable
from scieasy_blocks_lcms.io.load_peak_table import LoadPeakTable
from scieasy_blocks_lcms.types import MIDTable, MSRawFile, PeakTable

try:
    from pandas.errors import EmptyDataError as _PandasEmptyDataErrorImported
except ModuleNotFoundError:

    class _PandasEmptyDataErrorFallbackError(Exception):
        """Fallback when pandas is not installed."""

    _PandasEmptyDataErrorImported = _PandasEmptyDataErrorFallbackError

EmptyDataError = _PandasEmptyDataErrorImported


class ElMAVENBlock(_LCMSBlockMixin, AppBlock):
    """Launch ElMAVEN for interactive peak picking on a batch of raw files.

    See spec §9 T-LCMS-007 for the 7 acceptance criteria.
    """

    name: ClassVar[str] = "ElMAVEN"
    type_name: ClassVar[str] = "lcms.elmaven"
    category: ClassVar[str] = "external"
    description: ClassVar[str] = (
        "Open a batch of MSRawFiles in ElMAVEN for interactive peak picking. "
        "Collects exported peak tables (and optional MID tables) from the "
        "exchange directory."
    )

    app_command: ClassVar[str] = "elmaven"
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL
    output_patterns: ClassVar[list[str]] = ["*.csv", "*.tsv", "*.xlsx"]
    #: 30-minute window — ElMAVEN is interactive and slow.
    watch_timeout: ClassVar[int] = 1800

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="raw_files",
            accepted_types=[MSRawFile],
            required=True,
            description="Raw acquisition files to open in ElMAVEN",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="peak_table",
            accepted_types=[PeakTable],
            description="Exported peak table from ElMAVEN",
        ),
        OutputPort(
            name="mid_table",
            accepted_types=[MIDTable],
            required=False,
            description="Exported MID table from ElMAVEN (optional)",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "elmaven_path": {
                "type": ["string", "null"],
                "default": None,
                "title": "ElMAVEN executable path (overrides app_command)",
                "ui_priority": 0,
                "ui_widget": "file_browser",
            },
            "watch_timeout": {
                "type": "integer",
                "default": 1800,
                "title": "Watch timeout (seconds)",
                "ui_priority": 1,
            },
        },
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Delegate to :meth:`AppBlock.run`, then route exports.

        Implementation must apply :func:`_classify_export` to each
        emitted file and route it to either ``peak_table`` or
        ``mid_table`` based on the column-header heuristic.
        """
        raw_items = list(inputs.get("raw_files", Collection(items=[], item_type=MSRawFile)))
        raw_paths = [str(item.file_path) for item in raw_items if item.file_path is not None]

        patched_params = dict(config.params)
        elmaven_path = patched_params.pop("elmaven_path", None)
        if elmaven_path:
            patched_params["app_command"] = elmaven_path
        if self.state == BlockState.IDLE:
            self.transition(BlockState.READY)
        if self.state == BlockState.READY:
            self.transition(BlockState.RUNNING)
        delegated = super().run(cast(Any, {"raw_files": raw_paths}), BlockConfig(params=patched_params))

        peak_tables: list[PeakTable] = []
        mid_tables: list[MIDTable] = []
        for artifacts in delegated.values():
            if not isinstance(artifacts, Collection):
                continue
            for artifact in artifacts:
                file_path = getattr(artifact, "file_path", None)
                if file_path is None:
                    continue
                if _classify_export(file_path) == "mid_table":
                    loaded = LoadMIDTable().load(BlockConfig(params={"path": str(file_path)}))
                    if isinstance(loaded, Collection):
                        mid_tables.extend(cast(list[MIDTable], list(loaded)))
                    else:
                        mid_tables.append(cast(MIDTable, loaded))
                else:
                    loaded = LoadPeakTable().load(BlockConfig(params={"path": str(file_path), "source": "auto"}))
                    if isinstance(loaded, Collection):
                        peak_tables.extend(cast(list[PeakTable], list(loaded)))
                    else:
                        peak_tables.append(cast(PeakTable, loaded))

        return {
            "peak_table": Collection(items=cast(list[DataObject], peak_tables), item_type=PeakTable),
            "mid_table": Collection(items=cast(list[DataObject], mid_tables), item_type=MIDTable),
        }


def _classify_export(path: Path) -> str:
    """Return ``'mid_table'`` if *path* looks like a MID table, else ``'peak_table'``.

    Heuristic: MID tables have a column named ``C13`` or ``H2`` in the
    header row; peak tables typically have ``medMz`` / ``mz`` instead.

    Implementation deferred to T-LCMS-007 impl ticket
    (skeleton @ c08a885).
    """
    import pandas as pd

    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            columns = pd.read_csv(path, nrows=0).columns
        elif suffix == ".tsv":
            columns = pd.read_csv(path, sep="\t", nrows=0).columns
        elif suffix in {".xlsx", ".xls"}:
            columns = pd.read_excel(path, nrows=0).columns
        else:
            return "peak_table"
    except (EmptyDataError, ValueError):
        return "peak_table"

    names = {str(column) for column in columns}
    if {"C13", "H2"} & names:
        return "mid_table"
    return "peak_table"
