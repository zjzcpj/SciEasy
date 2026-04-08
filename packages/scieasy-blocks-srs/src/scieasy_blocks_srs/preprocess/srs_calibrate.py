"""SRSCalibrate — digitizer inversion + ``Image`` → :class:`SRSImage` conversion.

The entry point of the SRS pipeline. Users chain ``LoadImage`` (imaging
plugin) → :class:`SRSCalibrate` to obtain an :class:`SRSImage`. There is no
separate SRS Load block per master plan §2.4.

Skeleton placeholder — T-SRS-002 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-002.
"""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy_blocks_imaging.types import Image  # type: ignore[import-not-found]

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy_blocks_srs.types import SRSImage


class SRSCalibrate(ProcessBlock):
    """Invert the digitizer formula and re-type ``Image`` → :class:`SRSImage`.

    Per master plan §2.4 / spec §9 T-SRS-002 the inversion is::

        signal = (pixel / bit_depth * voltage_range - offset) / scale

    The block accepts the imaging-plugin :class:`Image` base class so the
    very first call right after ``LoadImage`` succeeds, then converts to
    :class:`SRSImage` and writes the four digitizer parameters plus the
    optional wavenumber array into the typed :class:`SRSImage.Meta`.

    Re-running on an already-calibrated :class:`SRSImage` (or an
    :class:`Image` whose meta already carries digitizer fields) raises
    ``ValueError`` per spec §8 Question 1.
    """

    name: ClassVar[str] = "SRS Calibrate"
    description: ClassVar[str] = (
        "Invert digitizer formula and convert Image → SRSImage. Entry point of the SRS preprocessing pipeline."
    )
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "preprocessing"
    algorithm: ClassVar[str] = "digitizer_inversion"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[Image],
            description="Raw digitizer-counts Image with y/x/lambda axes.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="srs_image",
            accepted_types=[SRSImage],
            description="Calibrated SRSImage with digitizer meta populated.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "bit_depth": {"type": "integer", "default": 4096, "minimum": 1},
            "voltage_range": {"type": "number", "default": 10.0},
            "offset": {"type": "number", "default": 0.0},
            "scale": {"type": "number", "default": 1.0},
            "wavenumbers_cm1": {
                "type": ["array", "null"],
                "items": {"type": "number"},
                "default": None,
            },
        },
    }

    def process_item(
        self,
        item: Image,
        config: BlockConfig,
        state: Any = None,
    ) -> SRSImage:
        """Apply digitizer inversion and return a typed :class:`SRSImage`.

        Steps (T-SRS-002 impl agent):

        1. Reject if ``isinstance(item, SRSImage)`` (re-run guard).
        2. Reject if ``item.meta.digitizer_bit_depth is not None``.
        3. Reject if ``scale == 0``.
        4. Compute ``signal = (pixel / bit_depth * voltage_range - offset) / scale``.
        5. Cast to ``float32``.
        6. Validate ``len(wavenumbers_cm1) == item.shape[lambda_axis]`` if set.
        7. Build ``new_meta = SRSImage.Meta(**old_meta.model_dump(),
           wavenumbers_cm1=..., digitizer_*=...)``.
        8. Construct and return ``SRSImage(...)`` with ``out._data = signal``.
        """
        raise NotImplementedError(
            "T-SRS-002: SRSCalibrate.process_item — impl pending (skeleton). "
            "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-002."
        )


__all__ = ["SRSCalibrate"]
