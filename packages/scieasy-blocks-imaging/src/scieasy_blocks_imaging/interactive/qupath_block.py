"""QuPath AppBlock wrapper for imaging workflows."""

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
    output_patterns: ClassVar[list[str]] = ["*.geojson", "*.qpdata", "*.csv", "*.tif", "*.tiff"]
    watch_timeout: ClassVar[int] = 3600

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], description="Whole-slide image(s) to open in QuPath."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="label", accepted_types=[Label], required=False, description="Annotations exported as Label."),
        OutputPort(
            name="measurements", accepted_types=[DataFrame], required=False, description="Per-object measurement table."
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
            "script_path": {
                "type": ["string", "null"],
                "default": None,
                "title": "Optional QuPath script file",
                "ui_widget": "file_browser",
            },
            "watch_timeout": {"type": "integer", "default": 3600},
        },
    }

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        images = _input_images(inputs, "image", "QuPathBlock")
        exchange_dir = _resolve_exchange_dir(config, prefix="scieasy_qupath_")
        _prepare_image_exchange(images, exchange_dir, tool_name=self.type_name, config=config)

        extra_args: list[str] = []
        script_path = config.get("script_path")
        if script_path:
            extra_args.extend(["script", str(script_path)])
        command = _resolve_command(
            config, app_command=self.app_command, override_key="qupath_path", extra_args=extra_args
        )
        output_files = _run_external_app(
            self, command=command, exchange_dir=exchange_dir, patterns=self.output_patterns, config=config
        )
        return _collect_outputs(
            output_files, template_image=images[0] if images else None, allowed_ports={"label", "measurements"}
        )
