"""SRSBaseline — spectral baseline correction.

Method enum: ``polynomial`` / ``rubber_band`` / ``rolling_ball_spectral``.
**ALS is intentionally unsupported** per master plan §2.4.

Skeleton placeholder — T-SRS-003 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-003.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_srs.types import SRSImage

#: Locked enum of accepted baseline methods. ALS is *intentionally absent*
#: per master plan §2.4 — re-adding it is a §5 scope-violation red flag.
ALLOWED_METHODS: tuple[str, ...] = ("polynomial", "rubber_band", "rolling_ball_spectral")


class SRSBaseline(ProcessBlock):
    """Subtract a fitted baseline from each per-pixel spectrum.

    Default method is ``polynomial`` with ``order=3`` per spec §8 Question 6.
    The block reshapes via ``np.moveaxis`` so any extra leading axes
    (``t``, ``z``, ``c``) broadcast transparently — no explicit
    ``iterate_over_axes`` call is required.
    """

    name: ClassVar[str] = "SRS Baseline Correct"
    description: ClassVar[str] = (
        "Subtract a fitted spectral baseline (polynomial / rubber_band / "
        "rolling_ball_spectral). ALS is intentionally not supported."
    )
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "preprocessing"
    algorithm: ClassVar[str] = "spectral_baseline"

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
            description="Baseline-subtracted SRSImage with preserved meta.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": list(ALLOWED_METHODS),
                "default": "polynomial",
            },
            "order": {"type": "integer", "default": 3, "minimum": 1},
            "window": {"type": "integer", "default": 50, "minimum": 1},
        },
    }

    def process_item(
        self,
        item: SRSImage,
        config: BlockConfig,
        state: Any = None,
    ) -> SRSImage:
        """Dispatch on ``method`` and return a baseline-subtracted SRSImage.

        T-SRS-003 impl agent: validate method against :data:`ALLOWED_METHODS`
        (raise ``ValueError`` for any other value including ``"als"``,
        explicitly naming the three accepted values), move ``lambda`` to
        the last axis, dispatch to ``_baseline_polynomial`` /
        ``_baseline_rubber_band`` / ``_baseline_rolling_ball``, move back,
        cast to ``float32``, and return a new :class:`SRSImage` with
        preserved ``meta`` and ``user``.
        """
        raise NotImplementedError(
            "T-SRS-003: SRSBaseline.process_item — impl pending (skeleton). "
            "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-003."
        )


__all__ = ["ALLOWED_METHODS", "SRSBaseline"]
