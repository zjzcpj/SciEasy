"""QuPathBlock — AppBlock wrapper for QuPath digital pathology.

Skeleton placeholder — T-IMG-037 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-037.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.app.app_block import AppBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import ExecutionMode
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_imaging.types import Image, Label


class QuPathBlock(AppBlock):
    """Open whole-slide :class:`Image` instances in QuPath for annotation."""

    type_name: ClassVar[str] = "imaging.qupath"
    name: ClassVar[str] = "QuPath"
    description: ClassVar[str] = (
        "Open whole-slide images in QuPath for interactive annotation. "
        "Collects exported annotations / measurements from the exchange directory."
    )
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "interactive"

    app_command: ClassVar[str] = "qupath"
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL
    output_patterns: ClassVar[list[str]] = ["*.geojson", "*.qpdata", "*.csv"]
    watch_timeout: ClassVar[int] = 3600

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Whole-slide image(s) to open in QuPath."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="label",
            accepted_types=[Label],
            required=False,
            description="Annotations exported as Label.",
        ),
        OutputPort(
            name="measurements",
            accepted_types=[DataFrame],
            required=False,
            description="Per-object measurement table.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "qupath_path": {
                "type": ["string", "null"],
                "default": None,
                "title": "QuPath executable path (overrides app_command)",
                "ui_widget": "file_browser",
            },
            "watch_timeout": {"type": "integer", "default": 3600},
        },
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        raise NotImplementedError(
            "T-IMG-037: QuPathBlock.run — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-037."
        )
