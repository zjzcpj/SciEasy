"""LoadMSRawFiles — batch loader for raw LC-MS acquisition files (T-LCMS-003).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-003.

Records paths only — does NOT parse scan data. Reads minimal header
bytes from each ``.mzML`` / ``.mzXML`` to populate
:attr:`MSRawFile.Meta` (format, polarity, instrument,
acquisition_date, sample_id). The actual data stays in the file and is
processed externally by ElMAVEN.

See spec §8 Q-10 for the plural-only-no-singular-variant rationale.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import OutputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import MSRawFile


class LoadMSRawFiles(_LCMSBlockMixin, IOBlock):
    """Batch loader that records paths to raw LC-MS acquisition files.

    See spec §9 T-LCMS-003 for the full specification, including the
    16 acceptance-criteria checkboxes covered by
    ``tests/test_io/test_load_ms_raw_files.py``.
    """

    direction: ClassVar[str] = "input"
    type_name: ClassVar[str] = "load_ms_raw_files"
    name: ClassVar[str] = "Load MS Raw Files"
    category: ClassVar[str] = "io"
    description: ClassVar[str] = (
        "Batch loader for raw LC-MS acquisition files (mzML/mzXML/raw/d). "
        "Records paths and minimal header metadata; does not parse scan data."
    )

    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="raw_files",
            accepted_types=[MSRawFile],
            description="Collection of loaded raw file handles",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "title": "Directory path",
                "ui_priority": 0,
                "ui_widget": "directory_browser",
            },
            "pattern": {
                "type": "string",
                "title": "Glob pattern",
                "default": "*.mzML",
                "ui_priority": 1,
            },
            "recursive": {
                "type": "boolean",
                "title": "Recursive",
                "default": False,
                "ui_priority": 2,
            },
            "format_hint": {
                "type": ["string", "null"],
                "enum": [None, "mzML", "mzXML", "raw", "d"],
                "default": None,
                "title": "Format hint",
                "ui_priority": 3,
            },
        },
        "required": ["path"],
    }

    def load(self, config: BlockConfig) -> DataObject | Collection:
        """Glob the configured path and return ``Collection[MSRawFile]``.

        Implementation must:

        * raise :class:`FileNotFoundError` on missing directory
        * respect ``recursive`` (``glob`` vs ``rglob``)
        * call ``_probe_header`` to populate ``MSRawFile.Meta`` for
          mzML/mzXML and skip header parsing for ``.raw``/``.d``
        * fall back to ``path.stem`` for ``sample_id``

        Returns:
            ``Collection[MSRawFile]`` (possibly empty).
        """
        raise NotImplementedError(
            "T-LCMS-003 LoadMSRawFiles.load — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-003."
        )

    def save(self, obj: DataObject | Collection, config: BlockConfig) -> None:
        """Not supported — :class:`LoadMSRawFiles` is input-only."""
        raise NotImplementedError("T-LCMS-003 LoadMSRawFiles is direction='input'; save() is unreachable.")
