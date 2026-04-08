"""Denoise — gaussian / median / bilateral / nlmeans / wavelet (T-IMG-004).

Skeleton (Sprint C continuation A). See
``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-004.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock

from scieasy_blocks_imaging.types import Image


class Denoise(ProcessBlock):
    """Denoise images using one of several 2D algorithms.

    Operates on 2D ``(y, x)`` slices. For N-D inputs, the implementation
    uses :func:`scieasy.utils.axis_iter.iterate_over_axes` to broadcast
    across the extra ``(t, z, c, lambda)`` axes.
    """

    type_name: ClassVar[str] = "imaging.denoise"
    name: ClassVar[str] = "Denoise"
    description: ClassVar[str] = "Remove noise via gaussian/median/bilateral/nlmeans/wavelet."
    category: ClassVar[str] = "preprocess"
    algorithm: ClassVar[str] = "denoise"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="image", accepted_types=[Image], required=True),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="image", accepted_types=[Image]),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["gaussian", "median", "bilateral", "nlmeans", "wavelet"],
                "default": "gaussian",
            },
            "sigma": {"type": "number", "default": 1.0, "minimum": 0.0},
            "radius": {"type": "integer", "default": 3, "minimum": 1},
        },
        "required": ["method"],
    }

    def process_item(self, item: Image, config: BlockConfig, state: Any = None) -> Image:
        """Denoise a single image.

        Args:
            item: Input :class:`Image` carrying ``(y, x)`` (and possibly
                ``(t, z, c, lambda)``).
            config: BlockConfig with ``method`` and method-specific params.
            state: Unused (kept for ADR-027 D7 signature).

        Returns:
            A new :class:`Image` of identical axes / shape / dtype with
            denoised pixel values.

        Raises:
            ValueError: If ``method`` is unknown or ``sigma < 0``.
        """
        raise NotImplementedError(
            "T-IMG-004 Denoise.process_item — impl pending (skeleton continuation A). "
            "See docs/specs/phase11-imaging-block-spec.md §9 T-IMG-004."
        )
