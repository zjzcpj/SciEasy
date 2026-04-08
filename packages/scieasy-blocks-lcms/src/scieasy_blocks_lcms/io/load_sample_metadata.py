"""LoadSampleMetadata — sample-level metadata loader (T-LCMS-006 / part 1).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-006.

Mirrors :class:`LoadPeakTable` but wraps the result as
:class:`SampleMetadata` and exposes a configurable
``sample_id_column`` (default ``"sample_id"``).
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import OutputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy_blocks_lcms._base import _LCMSBlockMixin
from scieasy_blocks_lcms.types import SampleMetadata


class LoadSampleMetadata(_LCMSBlockMixin, IOBlock):
    """Load a per-sample metadata file into a :class:`SampleMetadata`.

    See spec §9 T-LCMS-006 for the 6 acceptance criteria.
    """

    direction: ClassVar[str] = "input"
    type_name: ClassVar[str] = "load_sample_metadata"
    name: ClassVar[str] = "Load Sample Metadata"
    category: ClassVar[str] = "io"
    description: ClassVar[str] = (
        "Load per-sample metadata (group, timepoint, replicate, etc.) "
        "from CSV / TSV / XLSX into a typed SampleMetadata."
    )

    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="sample_metadata",
            accepted_types=[SampleMetadata],
            description="Loaded per-sample metadata",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "title": "Sample metadata file",
                "ui_priority": 0,
                "ui_widget": "file_browser",
            },
            "sample_id_column": {
                "type": "string",
                "default": "sample_id",
                "title": "Sample ID column",
                "ui_priority": 1,
            },
            "sheet_name": {
                "type": ["string", "integer", "null"],
                "default": None,
                "title": "XLSX sheet (name or index)",
                "ui_priority": 2,
            },
        },
        "required": ["path"],
    }

    def load(self, config: BlockConfig) -> DataObject | Collection:
        """Read the metadata file and return :class:`SampleMetadata`.

        Implementation must:

        * raise :class:`FileNotFoundError` on missing file
        * raise :class:`ValueError` if the configured
          ``sample_id_column`` is not present in the loaded DataFrame
        * preserve column order
        """
        raise NotImplementedError(
            "T-LCMS-006 LoadSampleMetadata.load — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-006."
        )

    def save(self, obj: DataObject | Collection, config: BlockConfig) -> None:
        """Not supported — use :class:`SaveTable` for output."""
        raise NotImplementedError("T-LCMS-006 LoadSampleMetadata is direction='input'; use SaveTable to write.")
