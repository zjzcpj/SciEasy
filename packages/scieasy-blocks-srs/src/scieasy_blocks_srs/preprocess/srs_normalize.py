"""SRSNormalize — per-spectrum intensity normalization.

Method enum: ``SNV`` / ``MSC`` / ``vector`` / ``area`` / ``peak_area``.

Skeleton placeholder — T-SRS-005 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-005.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_srs.types import SRSImage

ALLOWED_METHODS: tuple[str, ...] = ("SNV", "MSC", "vector", "area", "peak_area")


class SRSNormalize(ProcessBlock):
    """Normalize each per-pixel spectrum.

    ``peak_area`` requires both ``reference_peak_cm1`` config and
    ``item.meta.wavenumbers_cm1``; either missing raises ``ValueError``.
    """

    name: ClassVar[str] = "SRS Normalize"
    description: ClassVar[str] = "Per-spectrum intensity normalization (SNV/MSC/vector/area/peak_area)."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "preprocessing"
    algorithm: ClassVar[str] = "spectral_normalize"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[SRSImage],
            description="SRSImage with y/x/lambda axes.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="image",
            accepted_types=[SRSImage],
            description="Normalized SRSImage with preserved meta.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": list(ALLOWED_METHODS),
                "default": "SNV",
            },
            "reference_peak_cm1": {"type": ["number", "null"], "default": None},
        },
    }

    def process_item(
        self,
        item: SRSImage,
        config: BlockConfig,
        state: Any = None,
    ) -> SRSImage:
        """Reshape to ``(n_pixels, n_w)`` and dispatch on ``method``.

        T-SRS-005 impl agent: implement SNV / MSC / vector / area / peak_area
        per spec §9 T-SRS-005, cast to ``float32``, return a new
        :class:`SRSImage` with preserved meta.
        """
        raise NotImplementedError(
            "T-SRS-005: SRSNormalize.process_item — impl pending (skeleton). "
            "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-005."
        )


__all__ = ["ALLOWED_METHODS", "SRSNormalize"]
