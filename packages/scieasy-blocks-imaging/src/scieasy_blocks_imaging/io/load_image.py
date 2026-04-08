"""LoadImage IO block — unified loader for TIFF/OME-TIFF/PNG/JPG/Zarr/CZI/ND2/LIF/npy.

T-IMG-002 skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-002. Body is
``NotImplementedError``; the impl agent fills in the dispatch helpers.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import OutputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.base import DataObject

from scieasy_blocks_imaging.types import Image


class LoadImage(IOBlock):
    """Unified image loader.

    Returns ``Collection[Image]``; length 1 for a single file, length N
    for a directory or glob. Per ADR-028 Addendum 1 §D6' this block is
    STATIC: fixed ``output_ports``, no ``dynamic_ports``. The output
    type is always :class:`Image`.
    """

    direction: ClassVar[str] = "input"
    type_name: ClassVar[str] = "imaging.load_image"
    name: ClassVar[str] = "Load Image"
    description: ClassVar[str] = (
        "Unified image loader auto-detecting TIFF / OME-TIFF / PNG / JPG / "
        "Zarr / CZI / ND2 / LIF / npy."
    )
    category: ClassVar[str] = "io"

    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="images", accepted_types=[Collection[Image]]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "ui_priority": 0},
            "recursive": {"type": "boolean", "default": False, "ui_priority": 1},
        },
        "required": ["path"],
    }

    def load(self, config: BlockConfig) -> DataObject | Collection:
        """Enumerate the configured path and load every image into a Collection.

        Args:
            config: BlockConfig with ``path`` (file, directory, or glob)
                and optional ``recursive``.

        Returns:
            ``Collection[Image]`` of length 1 (single file) or N
            (directory / glob).

        Raises:
            FileNotFoundError: If ``path`` resolves to nothing.
            ValueError: If a file with an unsupported extension is hit.
            ImportError: If a CZI / ND2 / LIF file is requested but the
                optional extra is not installed.
        """
        raise NotImplementedError(
            "T-IMG-002 LoadImage.load — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-002."
        )
