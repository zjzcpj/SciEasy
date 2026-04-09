"""Fiji AppBlock wrapper for imaging workflows."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.app.app_block import AppBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import ExecutionMode
from scieasy.core.types.collection import Collection
from scieasy_blocks_imaging.interactive import (
    _collect_outputs,
    _input_images,
    _prepare_image_exchange,
    _resolve_command,
    _resolve_exchange_dir,
    _run_external_app,
)
from scieasy_blocks_imaging.types import Image


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

    app_command: ClassVar[str] = r"C:\Program Files\Fiji\fiji-windows-x64.exe"
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL
    output_patterns: ClassVar[list[str]] = ["*.tif", "*.tiff", "*.zip", "*.roi"]
    watch_timeout: ClassVar[int] = 1800

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], is_collection=True, description="Image(s) to open in Fiji."),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="image",
            accepted_types=[Image],
            is_collection=True,
            required=False,
            description="Image(s) edited / re-saved by the user.",
        )
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
            "macro_path": {
                "type": ["string", "null"],
                "default": None,
                "title": "Optional Fiji macro path",
                "ui_widget": "file_browser",
            },
            "watch_timeout": {"type": "integer", "default": 1800},
        },
    }

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        images = _input_images(inputs, "image", "FijiBlock")
        exchange_dir = _resolve_exchange_dir(config, prefix="scieasy_fiji_")
        staged_paths = _prepare_image_exchange(images, exchange_dir, tool_name=self.type_name, config=config)

        extra_args: list[str] = []
        macro_path = config.get("macro_path")
        if macro_path:
            extra_args.extend(["--headless", "-macro", str(macro_path)])
        command = _resolve_command(
            config, app_command=self.app_command, override_key="fiji_path", extra_args=extra_args
        )

        # When no macro is provided Fiji opens images from its native file-opener.
        # Pass the staged TIFF paths directly so Fiji receives individual file paths
        # rather than the exchange directory root, which it cannot open (#420).
        launch_args: list[str] | None = None
        if not macro_path:
            launch_args = [str(p) for p in staged_paths]

        output_files = _run_external_app(
            self,
            command=command,
            exchange_dir=exchange_dir,
            patterns=self.output_patterns,
            config=config,
            launch_args=launch_args,
        )
        return _collect_outputs(
            output_files, template_image=images[0] if images else None, allowed_ports={"image", "mask", "label"}
        )
