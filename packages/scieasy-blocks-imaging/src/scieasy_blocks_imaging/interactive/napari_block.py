"""NapariBlock — AppBlock wrapper that opens images in napari.

Skeleton placeholder — T-IMG-035 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-035.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.app.app_block import AppBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import ExecutionMode
from scieasy.core.types.collection import Collection
from scieasy_blocks_imaging.types import Image, Label, Mask


class NapariBlock(AppBlock):
    """Open :class:`Image` inputs in napari for interactive review / annotation."""

    type_name: ClassVar[str] = "imaging.napari"
    name: ClassVar[str] = "Napari"
    description: ClassVar[str] = (
        "Open Image inputs in napari for interactive review. Collects exported layers from the exchange directory."
    )
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "interactive"

    app_command: ClassVar[str] = "napari"
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL
    output_patterns: ClassVar[list[str]] = ["*.tif", "*.tiff", "*.npy", "*.zarr"]
    watch_timeout: ClassVar[int] = 1800

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Image(s) to open in napari."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image], required=False, description="Edited image."),
        OutputPort(name="mask", accepted_types=[Mask], required=False, description="Exported mask."),
        OutputPort(name="label", accepted_types=[Label], required=False, description="Exported labels."),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "napari_path": {
                "type": ["string", "null"],
                "default": None,
                "title": "napari executable path (overrides app_command)",
                "ui_widget": "file_browser",
            },
            "watch_timeout": {"type": "integer", "default": 1800},
        },
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        raise NotImplementedError(
            "T-IMG-035: NapariBlock.run — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-035."
        )
