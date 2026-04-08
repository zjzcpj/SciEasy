"""FijiBlock — AppBlock wrapper that opens images in Fiji / ImageJ.

Skeleton placeholder — T-IMG-034 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-034.

The :class:`AppBlock.run` lifecycle is reused verbatim per ADR-018 / ADR-019.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.app.app_block import AppBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import ExecutionMode
from scieasy.core.types.collection import Collection
from scieasy_blocks_imaging.types import Image, Label, Mask


class FijiBlock(AppBlock):
    """Open one or more :class:`Image` instances in Fiji / ImageJ."""

    type_name: ClassVar[str] = "imaging.fiji"
    name: ClassVar[str] = "Fiji"
    description: ClassVar[str] = (
        "Open Image inputs in Fiji for interactive review / annotation. "
        "Collects exported TIFFs / ROIs from the exchange directory."
    )
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "interactive"

    #: Default Fiji executable path on Windows. Override via config.
    app_command: ClassVar[str] = r"C:\Program Files\Fiji\fiji-windows-x64.exe"
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL
    output_patterns: ClassVar[list[str]] = ["*.tif", "*.tiff", "*.zip", "*.roi"]
    watch_timeout: ClassVar[int] = 1800

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[Image],
            description="Image(s) to open in Fiji.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="image",
            accepted_types=[Image],
            required=False,
            description="Image(s) edited / re-saved by the user.",
        ),
        OutputPort(
            name="mask",
            accepted_types=[Mask],
            required=False,
            description="Mask exported from Fiji (if any).",
        ),
        OutputPort(
            name="label",
            accepted_types=[Label],
            required=False,
            description="Label exported from Fiji (e.g. ROIs).",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "fiji_path": {
                "type": ["string", "null"],
                "default": None,
                "title": "Fiji executable path (overrides app_command)",
                "ui_widget": "file_browser",
            },
            "watch_timeout": {
                "type": "integer",
                "default": 1800,
            },
        },
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Delegate to :meth:`AppBlock.run`, then route exported files to ports."""
        raise NotImplementedError(
            "T-IMG-034: FijiBlock.run — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-034."
        )
