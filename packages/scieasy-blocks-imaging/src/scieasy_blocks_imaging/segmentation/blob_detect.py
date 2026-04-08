"""BlobDetect — LoG / DoG / DoH blob detection (T-IMG-020).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-020.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_imaging.types import Image, Label


class BlobDetect(ProcessBlock):
    """Blob detection producing a :class:`Label` raster of disks."""

    type_name: ClassVar[str] = "imaging.blob_detect"
    name: ClassVar[str] = "Blob Detect"
    description: ClassVar[str] = "Blob detection via Laplacian-of-Gaussian / DoG / DoH."
    category: ClassVar[str] = "segmentation"
    algorithm: ClassVar[str] = "blob_detect"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="label", accepted_types=[Label]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["LoG", "DoG", "DoH"],
                "default": "LoG",
            },
            "min_sigma": {"type": "number", "default": 1.0},
            "max_sigma": {"type": "number", "default": 30.0},
            "num_sigma": {"type": "integer", "default": 10},
            "threshold": {"type": "number", "default": 0.1},
        },
        "required": ["method"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Label:
        """Detect blobs and return as a :class:`Label`.

        Raises:
            ValueError: For unknown ``method``.
        """
        raise NotImplementedError(
            "T-IMG-020 BlobDetect.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-020."
        )
