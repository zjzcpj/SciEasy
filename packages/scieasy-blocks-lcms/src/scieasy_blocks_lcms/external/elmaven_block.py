"""ElMAVENBlock — AppBlock wrapper for ElMAVEN (T-LCMS-007 / part 1).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-007.

Per spec §8 Q-2 the block does **not** script ElMAVEN's UI — the user
opens files, runs peak detection, and exports manually;
:class:`FileWatcher` collects the exports.

Issue #526: ElMAVEN does not accept positional file CLI args (unlike
Fiji). Raw file paths are staged as symlinks in the exchange directory
and recorded in the manifest. The PIPE deadlock from bridge.py is fixed
by switching to DEVNULL.
"""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any, ClassVar, cast

from scieasy.blocks.app.app_block import AppBlock, _PopenProcessAdapter
from scieasy.blocks.app.bridge import FileExchangeBridge
from scieasy.blocks.app.watcher import FileWatcher, ProcessExitedWithoutOutputError
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import BlockState, ExecutionMode
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.io.load_mid_table import LoadMIDTable
from scieasy_blocks_lcms.io.load_peak_table import LoadPeakTable
from scieasy_blocks_lcms.types import MIDTable, MSRawFile, PeakTable

logger = logging.getLogger(__name__)

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

    app_command: ClassVar[str] = ""
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL
    output_patterns: ClassVar[list[str]] = ["*.csv", "*.tsv", "*.xlsx"]

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
                "title": "Executable Path",
                "ui_priority": 0,
                "ui_widget": "file_browser",
            },
        },
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Stage raw files and launch ElMAVEN for interactive peak picking.

        Issue #526: ElMAVEN's CLI does not accept positional file args
        (unlike Fiji), so we stage the raw file paths as symlinks in the
        exchange directory and write them to the manifest. The user opens
        files manually from the exchange dir.

        After the user runs peak detection and exports results,
        :func:`_classify_export` routes each output file to either
        ``peak_table`` or ``mid_table`` based on the column-header
        heuristic.
        """
        raw_items = list(inputs.get("raw_files", Collection(items=[], item_type=MSRawFile)))
        raw_paths = [str(item.file_path) for item in raw_items if item.file_path is not None]

        # Resolve command.
        patched_params = dict(config.params)
        elmaven_path = patched_params.pop("elmaven_path", None)
        command = elmaven_path or self.app_command

        # Resolve exchange directory.
        explicit_dir = config.get("exchange_dir")
        if explicit_dir:
            exchange_dir = Path(str(explicit_dir))
        else:
            project_dir = config.get("project_dir")
            block_id = config.get("block_id", "")
            if project_dir and block_id:
                exchange_dir = Path(str(project_dir)) / "data" / "exchange" / str(block_id)
            else:
                exchange_dir = Path(tempfile.mkdtemp(prefix="scieasy_elmaven_"))
        exchange_dir.mkdir(parents=True, exist_ok=True)
        (exchange_dir / "inputs").mkdir(exist_ok=True)
        output_dir = exchange_dir / "outputs"
        output_dir.mkdir(exist_ok=True)

        # Write manifest for traceability.
        manifest = {
            "tool": self.type_name,
            "input_files": raw_paths,
            "output_dir": str(output_dir),
            "config": patched_params,
        }
        (exchange_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")

        # State transitions.
        if self.state == BlockState.IDLE:
            self.transition(BlockState.READY)
        if self.state == BlockState.READY:
            self.transition(BlockState.RUNNING)
        self.transition(BlockState.PAUSED)

        # Stage raw file paths into the exchange directory so the user
        # can easily locate them.  ElMAVEN's CLI does not accept positional
        # file arguments (unlike Fiji), so we do NOT pass argv_override.
        # See issue #526.
        for rp in raw_paths:
            src = Path(rp)
            if src.exists():
                link = exchange_dir / "inputs" / src.name
                if not link.exists():
                    with suppress(OSError):
                        link.symlink_to(src)

        bridge = FileExchangeBridge()
        proc = bridge.launch(command, exchange_dir)
        logger.info(
            "ElMAVEN launched. Raw files staged in exchange dir. Save exports to: %s",
            output_dir,
        )

        # Watch for exported files.
        stability_period = float(config.get("stability_period", 2.0))
        done_marker = config.get("done_marker")
        watcher = FileWatcher(
            directory=output_dir,
            patterns=self.output_patterns,
            timeout=None,
            process_handle=_PopenProcessAdapter(proc),
            stability_period=stability_period,
            done_marker=str(done_marker) if done_marker is not None else None,
        )
        watcher.start()
        try:
            output_files = watcher.wait_for_output()
        except ProcessExitedWithoutOutputError:
            self.transition(BlockState.CANCELLED)
            return {
                "peak_table": Collection(items=[], item_type=PeakTable),
                "mid_table": Collection(items=[], item_type=MIDTable),
            }
        finally:
            watcher.stop()
            with suppress(subprocess.TimeoutExpired):
                proc.wait(timeout=5)

        if self.state == BlockState.PAUSED:
            self.transition(BlockState.RUNNING)

        # Classify and load exported files.
        peak_tables: list[PeakTable] = []
        mid_tables: list[MIDTable] = []
        for file_path in output_files:
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

        if self.state == BlockState.RUNNING:
            self.transition(BlockState.DONE)

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
