"""GraphPadBlock — AppBlock wrapper for GraphPad Prism (T-LCMS-019).

Skeleton @ c08a885. Per ``docs/specs/phase11-lcms-block-spec.md`` §9
T-LCMS-019.

Per §8 Q-8, the block has **no default ``app_command``** — the user
must supply ``graphpad_path`` explicitly because the install location
varies (Prism 9 vs Prism 10) and the application is Windows-only. The
block warns when launched on non-Windows hosts but does not block.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.app.app_block import AppBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import ExecutionMode
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

from scieasy_blocks_lcms._base import _LCMSBlockMixin


class GraphPadBlock(_LCMSBlockMixin, AppBlock):
    """Open input tables in GraphPad Prism for interactive figure polishing.

    See spec §9 T-LCMS-019 for the 9 acceptance criteria.
    """

    name: ClassVar[str] = "GraphPad Prism"
    type_name: ClassVar[str] = "graphpad"
    category: ClassVar[str] = "external"
    description: ClassVar[str] = (
        "Open tables in GraphPad Prism for interactive figure creation. "
        "Exported PNG / PDF / SVG files are collected from the exchange "
        "directory. Windows-only; user must supply graphpad_path."
    )

    #: No default — user must supply ``graphpad_path`` (spec §8 Q-8).
    app_command: ClassVar[str] = ""
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL
    output_patterns: ClassVar[list[str]] = ["*.png", "*.pdf", "*.svg"]
    watch_timeout: ClassVar[int] = 1800

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="tables",
            accepted_types=[DataFrame],
            required=True,
            description="DataFrames to plot in GraphPad",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="figures",
            accepted_types=[Artifact],
            description="Exported figures (PNG / PDF / SVG)",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "graphpad_path": {
                "type": "string",
                "title": "GraphPad executable path",
                "ui_priority": 0,
                "ui_widget": "file_browser",
            },
            "template_path": {
                "type": ["string", "null"],
                "default": None,
                "title": "GraphPad template (.pzfx)",
                "ui_priority": 1,
                "ui_widget": "file_browser",
            },
            "watch_timeout": {
                "type": "integer",
                "default": 1800,
                "title": "Watch timeout (seconds)",
                "ui_priority": 2,
            },
        },
        "required": ["graphpad_path"],
    }

    def run(
        self,
        inputs: dict[str, Collection],
        config: BlockConfig,
    ) -> dict[str, Collection]:
        """Launch GraphPad and collect exported figures.

        Implementation must:

        * warn (do not raise) when ``platform.system() != "Windows"``
        * raise :class:`ValueError` when ``graphpad_path`` is missing
        * serialise input DataFrames to CSV in the exchange directory
        * optionally copy ``template_path`` (.pzfx) into the exchange
        * delegate to :meth:`AppBlock.run` with the resolved command
        * wrap collected figure files in :class:`Artifact` with
          ``mime_type`` per file extension
        """
        raise NotImplementedError(
            "T-LCMS-019 GraphPadBlock.run — impl pending (skeleton @ c08a885). "
            "See docs/specs/phase11-lcms-block-spec.md §9 T-LCMS-019."
        )
