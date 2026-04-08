"""SRSICA — FastICA on per-pixel spectra.

Structurally identical to :class:`SRSPCA` with FastICA in place of PCA.
The ``method`` enum has only one valid value (``"fastica"``); the
single-element enum is intentional and reserves the field for future
addenda.

Skeleton placeholder — T-SRS-009 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-009.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_srs.types import SRSImage

ALLOWED_METHODS: tuple[str, ...] = ("fastica",)


class SRSICA(ProcessBlock):
    """Independent Component Analysis on per-pixel spectra (FastICA only)."""

    name: ClassVar[str] = "SRS ICA"
    description: ClassVar[str] = "FastICA on per-pixel spectra."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "component_analysis"
    algorithm: ClassVar[str] = "fastica"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[SRSImage],
            description="SRSImage with y/x/lambda axes.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="ic_maps",
            accepted_types=[Collection],
            description="Collection[Image] of per-IC 2D score maps.",
        ),
        OutputPort(
            name="components",
            accepted_types=[DataFrame],
            description="Component DataFrame with `ic_id` index and wavenumber columns.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "n_components": {"type": "integer", "default": 4, "minimum": 1},
            "method": {
                "type": "string",
                "enum": list(ALLOWED_METHODS),
                "default": "fastica",
            },
        },
    }

    def run(
        self,
        inputs: dict[str, Any],
        config: BlockConfig,
    ) -> dict[str, Any]:
        """Run ``FastICA(random_state=42)`` and emit IC maps + components.

        T-SRS-009 impl agent: validate ``method`` against
        :data:`ALLOWED_METHODS` (raise ``ValueError`` for any other), then
        the same lambda-to-last reshape / spatial reconstruction loop as
        :class:`SRSPCA`. The DataFrame index is named ``ic_id``.
        """
        raise NotImplementedError(
            "T-SRS-009: SRSICA.run — impl pending (skeleton). See docs/specs/phase11-srs-block-spec.md §9 T-SRS-009."
        )


__all__ = ["ALLOWED_METHODS", "SRSICA"]
