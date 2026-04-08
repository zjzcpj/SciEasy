"""CellProfilerBlock — AppBlock wrapper for CellProfiler.

Skeleton placeholder — T-IMG-036 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-036.
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


class CellProfilerBlock(AppBlock):
    """Run a CellProfiler pipeline on a batch of images."""

    type_name: ClassVar[str] = "imaging.cell_profiler"
    name: ClassVar[str] = "CellProfiler"
    description: ClassVar[str] = (
        "Run a CellProfiler pipeline (.cppipe) on a batch of Image inputs. "
        "Collects exported objects / measurements from the exchange directory."
    )
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "interactive"

    app_command: ClassVar[str] = "cellprofiler"
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL
    output_patterns: ClassVar[list[str]] = ["*.csv", "*.tif", "*.tiff"]
    watch_timeout: ClassVar[int] = 3600

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Images to process."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="measurements",
            accepted_types=[DataFrame],
            required=False,
            description="Per-object measurement table.",
        ),
        OutputPort(
            name="label",
            accepted_types=[Label],
            required=False,
            description="Object label image.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "pipeline_path": {
                "type": ["string", "null"],
                "default": None,
                "title": "CellProfiler pipeline (.cppipe)",
                "ui_widget": "file_browser",
            },
            "cellprofiler_path": {
                "type": ["string", "null"],
                "default": None,
                "title": "CellProfiler executable path (overrides app_command)",
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
            "T-IMG-036: CellProfilerBlock.run — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-036."
        )
