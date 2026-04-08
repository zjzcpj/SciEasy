"""SRSUnmix — NNLS spectral unmixing with optional auto-VCA fallback.

Two inputs (image, optional references) → two outputs (abundance maps,
endmembers DataFrame). Overrides :meth:`run` directly because the default
``ProcessBlock.run`` only handles a single input port.

Skeleton placeholder — T-SRS-007 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-007.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy_blocks_imaging.types import Image  # type: ignore[import-not-found]

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_srs.types import SRSImage


class SRSUnmix(ProcessBlock):
    """NNLS unmixing of an :class:`SRSImage` against reference spectra.

    If the optional ``references`` input is omitted, falls back to
    :func:`scieasy_blocks_srs.component_analysis.srs_vca._extract_endmembers`
    with ``auto_vca_n_components`` (spec §8 Question 4) and emits an INFO
    log message.
    """

    name: ClassVar[str] = "SRS Unmix"
    description: ClassVar[str] = "NNLS spectral unmixing with optional auto-VCA endmember extraction."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "component_analysis"
    algorithm: ClassVar[str] = "nnls_unmix"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[SRSImage],
            description="SRSImage with y/x/lambda axes.",
        ),
        InputPort(
            name="references",
            accepted_types=[DataFrame],
            description="Optional endmember reference DataFrame; auto-VCA fallback if omitted.",
            required=False,
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="abundance_maps",
            accepted_types=[Collection],
            description="Collection[Image] of per-endmember 2D abundance maps.",
        ),
        OutputPort(
            name="endmembers",
            accepted_types=[DataFrame],
            description="Endmember DataFrame (passthrough or VCA-extracted).",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "auto_vca_n_components": {"type": "integer", "default": 4, "minimum": 2},
        },
    }

    def run(
        self,
        inputs: dict[str, Any],
        config: BlockConfig,
    ) -> dict[str, Any]:
        """Iterate ``inputs["image"]``, dispatch to ``_unmix_one``, pack outputs.

        T-SRS-007 impl agent:

        1. For each :class:`SRSImage` in ``inputs["image"]``, call
           ``_unmix_one(item, inputs.get("references"), config)``.
        2. Collect per-endmember 2D :class:`Image` objects into a
           ``Collection(items, item_type=Image)``.
        3. Return ``{"abundance_maps": collection, "endmembers": last_endmembers_df}``.

        Auto-VCA branch must call
        :func:`scieasy_blocks_srs.component_analysis.srs_vca._extract_endmembers`
        and log at INFO level.
        """
        raise NotImplementedError(
            "T-SRS-007: SRSUnmix.run — impl pending (skeleton). See docs/specs/phase11-srs-block-spec.md §9 T-SRS-007."
        )

    def _unmix_one(
        self,
        item: SRSImage,
        ref_collection: Collection | None,
        config: BlockConfig,
    ) -> tuple[list[Image], DataFrame]:
        """Per-image NNLS solve.

        T-SRS-007 impl agent: build references (passthrough or auto-VCA),
        run ``scipy.optimize.nnls`` per pixel, reshape, emit one
        :class:`Image` per endmember plus the endmember DataFrame.
        """
        raise NotImplementedError(
            "T-SRS-007: SRSUnmix._unmix_one — impl pending (skeleton). "
            "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-007."
        )


__all__ = ["SRSUnmix"]
