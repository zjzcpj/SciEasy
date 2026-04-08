"""SaveImage IO block — persist Collection[Image] to disk.

T-IMG-003 skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-003.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy_blocks_imaging.types import Image


class SaveImage(IOBlock):
    """Persist a ``Collection[Image]`` to disk.

    Length-1 + file path → single file. Length-1 + directory →
    ``image_000.<ext>``. Length-N + directory → indexed files. Length-N
    + file path → ``ValueError``. The TIFF round-trip protocol embeds
    the ``Image.Meta`` JSON in the ``ImageDescription`` tag prefixed
    with ``SCIEASY:``.
    """

    direction: ClassVar[str] = "output"
    type_name: ClassVar[str] = "imaging.save_image"
    name: ClassVar[str] = "Save Image"
    description: ClassVar[str] = "Persist Collection[Image] to disk (TIFF/PNG/JPG/NPY/Zarr)."
    category: ClassVar[str] = "io"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="images", accepted_types=[Collection[Image]]),  # type: ignore[misc]
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "ui_priority": 0},
            "format": {
                "type": "string",
                "enum": ["tif", "png", "jpg", "npy", "zarr"],
                "default": "tif",
                "ui_priority": 1,
            },
        },
        "required": ["path"],
    }

    def save(self, obj: DataObject | Collection, config: BlockConfig) -> None:
        """Write a single image or a Collection to disk.

        Args:
            obj: ``Collection[Image]`` (or a single ``Image``).
            config: BlockConfig with ``path`` and optional ``format``.

        Raises:
            ValueError: If a length-N collection is paired with a single
                file path, if the collection is empty, or if ``format``
                is not in the enum.
        """
        raise NotImplementedError(
            "T-IMG-003 SaveImage.save — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-003."
        )
