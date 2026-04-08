"""SRS plugin types — :class:`SRSImage` (subclass of imaging plugin's ``Image``).

Per master plan §2.4, the SRS plugin defines exactly one type:

* :class:`SRSImage` — an imaging-plugin :class:`Image` with the spectral
  ``lambda`` axis required, plus an SRS-specific :class:`SRSImage.Meta`
  Pydantic model carrying digitizer parameters and laser/wavenumber metadata.

**There is intentionally no** ``RamanSpectrum(Series)`` **type** —
spectra are passed around as long-format DataFrames per master plan §2.4.

Skeleton placeholder — T-SRS-001 implementation agent fills the body.
See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-001.
"""

from __future__ import annotations

from typing import ClassVar

# Cross-plugin import per standards doc §Q5. The imaging plugin lands its
# real ``Image`` class in T-IMG-001 (Sprint C, parallel skeleton agent). At
# skeleton time the symbol may be a placeholder; the impl agent revisits.
from scieasy_blocks_imaging.types import Image  # type: ignore[import-not-found]


class SRSImage(Image):  # type: ignore[misc,valid-type]
    """Stimulated Raman Scattering image with required spectral axis.

    Extends the imaging plugin's :class:`Image` by:

    * tightening :attr:`required_axes` to ``frozenset({"y", "x", "lambda"})``;
    * inheriting :attr:`allowed_axes` from :class:`Image` so any combination
      of ``{t, z, c, lambda, y, x}`` remains valid as long as ``y/x/lambda``
      are present;
    * declaring an inner :class:`Meta` Pydantic model that extends
      ``Image.Meta`` with the nine SRS-specific fields locked in master
      plan §2.4 (wavenumbers, laser power, integration time, four
      digitizer parameters, pump/Stokes wavelengths).

    See ``docs/specs/phase11-srs-block-spec.md`` §9 T-SRS-001 for the full
    field table and acceptance criteria.
    """

    required_axes: ClassVar[frozenset[str]] = frozenset({"y", "x", "lambda"})
    canonical_order: ClassVar[tuple[str, ...]] = ("t", "z", "c", "lambda", "y", "x")

    # NOTE(T-SRS-001 impl agent): declare ``class Meta(Image.Meta)`` here with
    # ``model_config = ConfigDict(frozen=True, extra="forbid")`` and the nine
    # fields from master plan §2.4:
    #   - wavenumbers_cm1: list[float] | None = None
    #   - laser_power: float | None = None        # mW
    #   - integration_time: PhysicalQuantity | None = None
    #   - digitizer_bit_depth: int | None = None
    #   - digitizer_voltage_range: float | None = None
    #   - digitizer_offset: float | None = None
    #   - digitizer_scale: float | None = None
    #   - pump_wavelength_nm: float | None = None
    #   - stokes_wavelength_nm: float | None = None

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError(
            "T-SRS-001: SRSImage construction — impl pending (skeleton). "
            "See docs/specs/phase11-srs-block-spec.md §9 T-SRS-001."
        )


def get_types() -> list[type]:
    """Plugin entry point — return the list of types contributed by this plugin.

    Returns ``[SRSImage]`` once T-SRS-001 lands; currently returns ``[]``
    while the type is a skeleton placeholder. T-SRS-013 wires the final
    entry-point registration.
    """
    # TODO(T-SRS-001 impl agent): return [SRSImage]
    return []


__all__ = ["SRSImage", "get_types"]
