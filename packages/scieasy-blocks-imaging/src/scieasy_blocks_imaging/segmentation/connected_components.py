"""ConnectedComponents — label connected components in a binary :class:`Mask`.

Skeleton placeholder — T-IMG-021 implementation agent fills the body.
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-021.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Label, Mask


class ConnectedComponents(ProcessBlock):
    """Label connected foreground components of a :class:`Mask` into :class:`Label`.

    Per spec §9 T-IMG-021, ``connectivity=1`` is 4-connectivity (2D) and
    ``connectivity=2`` is 8-connectivity. Returns a :class:`Label` with
    the raster slot populated and ``Label.meta.n_objects`` set.
    """

    type_name: ClassVar[str] = "imaging.connected_components"
    name: ClassVar[str] = "Connected Components"
    description: ClassVar[str] = "Label connected foreground components in a binary Mask, returning a Label."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "segmentation"
    algorithm: ClassVar[str] = "connected_components"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="mask",
            accepted_types=[Mask],
            description="Binary mask whose foreground will be labelled.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="label",
            accepted_types=[Label],
            description="Label image with raster slot populated.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "connectivity": {
                "type": "integer",
                "enum": [1, 2],
                "default": 1,
                "description": "1 = 4-connectivity (2D) / face; 2 = 8-connectivity / corner",
            },
        },
    }

    def process_item(
        self,
        item: Mask,
        config: BlockConfig,
        state: Any = None,
    ) -> Label:
        """Run skimage connected-component labelling and wrap as :class:`Label`."""
        raise NotImplementedError(
            "T-IMG-021: ConnectedComponents.process_item — impl pending (skeleton continuation B). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-021."
        )
