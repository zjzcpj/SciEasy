"""BandRatio — two-band intensity ratio image (lambda axis is consumed).

Output port type is :class:`Image` (not :class:`SRSImage`) because the
spectral axis is collapsed by averaging within each band.

Skeleton placeholder — T-SRS-012 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-012.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy_blocks_imaging.types import Image  # type: ignore[import-not-found]

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_srs.types import SRSImage


class BandRatio(ProcessBlock):
    """Compute the intensity ratio between two spectral bands.

    Defaults target the CH2 (lipid, 2850-2855 cm-1) over CH3 (protein,
    2925-2935 cm-1) ratio commonly used in SRS lipid imaging. Both bands
    must fall inside the wavenumber range of ``item.meta.wavenumbers_cm1``,
    which must be set; otherwise the block raises ``ValueError``.
    """

    name: ClassVar[str] = "Band Ratio"
    type_name: ClassVar[str] = "srs.band_ratio"
    description: ClassVar[str] = "Compute intensity ratio between two spectral bands → 2D Image."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "spectral"
    algorithm: ClassVar[str] = "band_ratio"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[SRSImage],
            description="SRSImage with y/x/lambda axes and wavenumbers_cm1 meta.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="ratio",
            accepted_types=[Image],
            description="2D Image (axes=['y','x']) of the per-pixel band ratio.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "numerator_band": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 2,
                "maxItems": 2,
                "default": [2850.0, 2855.0],
            },
            "denominator_band": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 2,
                "maxItems": 2,
                "default": [2925.0, 2935.0],
            },
        },
        "required": ["numerator_band", "denominator_band"],
    }

    def process_item(
        self,
        item: SRSImage,
        config: BlockConfig,
        state: Any = None,
    ) -> Image:
        """Compute ``mean(num_band) / (mean(den_band) + eps)`` and return Image.

        T-SRS-012 impl agent: validate wavenumbers meta, validate bands
        within range, average within each band, divide with epsilon, cast
        to ``float32``, return a 2D :class:`Image` with ``axes=["y","x"]``.
        """
        raise NotImplementedError(
            "T-SRS-012: BandRatio.process_item — impl pending (skeleton). "
            "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-012."
        )


__all__ = ["BandRatio"]
