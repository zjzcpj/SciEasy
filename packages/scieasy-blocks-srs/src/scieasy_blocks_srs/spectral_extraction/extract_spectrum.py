"""ExtractSpectrum — ROI / Label / Mask + :class:`SRSImage` → long DataFrame.

Critical-path block for the §11 cross-plugin E2E test. Output schema is
the locked long format ``["region_id", "wavenumber_cm1", "intensity"]``
per spec §8 Question 3.

Skeleton placeholder — T-SRS-011 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-011.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy_blocks_imaging.types import Label, Mask  # type: ignore[import-not-found]

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_srs.types import SRSImage

#: Locked long-format columns for the output DataFrame.
OUTPUT_COLUMNS: tuple[str, ...] = ("region_id", "wavenumber_cm1", "intensity")


class ExtractSpectrum(ProcessBlock):
    """Extract per-region mean spectra into a long-format DataFrame.

    Three input ports (``image``, optional ``labels``, optional ``mask``)
    so the block overrides :meth:`run` directly. Region-id semantics:

    * No ROI → single row block with ``region_id == 0``.
    * Mask → single row block with ``region_id == 1``.
    * Label → one row block per non-zero label value.

    v0.1 limitation: 5D inputs with extra ``c``/``t``/``z`` axes raise a
    ``ValueError`` pointing at ``SelectSlice`` as the upstream remedy.
    """

    name: ClassVar[str] = "Extract Spectrum"
    type_name: ClassVar[str] = "srs.extract_spectrum"
    description: ClassVar[str] = (
        "Extract per-ROI mean spectra into a long-format DataFrame (region_id, wavenumber_cm1, intensity)."
    )
    version: ClassVar[str] = "0.1.0"
    subcategory: ClassVar[str] = "spectral"
    algorithm: ClassVar[str] = "extract_spectrum"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[SRSImage],
            description="SRSImage with y/x/lambda axes only (v0.1 limitation).",
        ),
        InputPort(
            name="labels",
            accepted_types=[Label],
            description="Optional Label raster; non-zero values define regions.",
            required=False,
        ),
        InputPort(
            name="mask",
            accepted_types=[Mask],
            description="Optional boolean Mask; True pixels define region 1.",
            required=False,
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="spectra",
            accepted_types=[DataFrame],
            description="Long-format DataFrame: (region_id, wavenumber_cm1, intensity).",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {},
    }

    def run(
        self,
        inputs: dict[str, Any],
        config: BlockConfig,
    ) -> dict[str, Any]:
        """Iterate the input Collection, extract per-region means, build DataFrame.

        T-SRS-011 impl agent: per spec §8 Question 3, dispatch to label /
        mask / no-ROI branch, build rows with the locked
        :data:`OUTPUT_COLUMNS` schema, wrap with ``DataFrame.from_pandas``.
        """
        raise NotImplementedError(
            "T-SRS-011: ExtractSpectrum.run — impl pending (skeleton). "
            "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-011."
        )


__all__ = ["OUTPUT_COLUMNS", "ExtractSpectrum"]
