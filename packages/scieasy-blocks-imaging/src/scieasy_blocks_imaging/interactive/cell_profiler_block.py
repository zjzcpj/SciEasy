"""CellProfiler AppBlock wrapper for imaging workflows."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.app.app_block import AppBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import ExecutionMode
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_imaging.interactive import (
    _collect_outputs,
    _input_images,
    _prepare_image_exchange,
    _resolve_command,
    _resolve_exchange_dir,
    _run_external_app,
)
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
            name="measurements", accepted_types=[DataFrame], required=False, description="Per-object measurement table."
        ),
        OutputPort(name="label", accepted_types=[Label], required=False, description="Object label image."),
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

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        images = _input_images(inputs, "image", "CellProfilerBlock")
        exchange_dir = _resolve_exchange_dir(config, prefix="scieasy_cellprofiler_")
        _prepare_image_exchange(images, exchange_dir, tool_name=self.type_name, config=config)

        extra_args: list[str] = []
        pipeline_path = config.get("pipeline_path")
        if pipeline_path:
            extra_args.extend(["-c", "-r", "-p", str(pipeline_path)])
        command = _resolve_command(
            config, app_command=self.app_command, override_key="cellprofiler_path", extra_args=extra_args
        )
        output_files = _run_external_app(
            self, command=command, exchange_dir=exchange_dir, patterns=self.output_patterns, config=config
        )
        return _collect_outputs(
            output_files, template_image=images[0] if images else None, allowed_ports={"measurements", "label"}
        )
