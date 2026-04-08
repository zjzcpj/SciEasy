"""SRSDenoise — spatio-spectral denoising.

Method enum: ``wavelet`` / ``PCA_denoise`` / ``SVD_truncation`` / ``BM4D``.

Skeleton placeholder — T-SRS-004 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-004.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_srs.types import SRSImage

ALLOWED_METHODS: tuple[str, ...] = ("wavelet", "PCA_denoise", "SVD_truncation", "BM4D")


class SRSDenoise(ProcessBlock):
    """Denoise an :class:`SRSImage` along the spectral / spatial axes.

    PCA and SVD methods are always available; ``wavelet`` and ``BM4D`` are
    guarded by ``ImportError`` and re-raise as ``ValueError`` with an
    install-extra hint per spec §9 T-SRS-004.
    """

    name: ClassVar[str] = "SRS Denoise"
    description: ClassVar[str] = "Spatio-spectral denoising via PCA/SVD/wavelet/BM4D."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "preprocessing"
    algorithm: ClassVar[str] = "spectral_denoise"

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
            description="Denoised SRSImage with preserved meta.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": list(ALLOWED_METHODS),
                "default": "PCA_denoise",
            },
            "n_components": {"type": "integer", "default": 10, "minimum": 1},
            "wavelet": {"type": "string", "default": "db4"},
        },
    }

    def process_item(
        self,
        item: SRSImage,
        config: BlockConfig,
        state: Any = None,
    ) -> SRSImage:
        """Reshape, dispatch on ``method``, reconstruct, return new SRSImage.

        T-SRS-004 impl agent: validate ``n_components <= n_wavenumbers``,
        flatten ``(n_pixels, n_w)``, dispatch to PCA / SVD / wavelet / BM4D
        per spec §9 T-SRS-004 implementation details, cast to ``float32``,
        and return a new :class:`SRSImage` with preserved meta.
        """
        raise NotImplementedError(
            "T-SRS-004: SRSDenoise.process_item — impl pending (skeleton). "
            "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-004."
        )


__all__ = ["ALLOWED_METHODS", "SRSDenoise"]
