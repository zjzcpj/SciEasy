"""Series type — 1D indexed data (spectra, time series, chromatograms)."""

from __future__ import annotations

from typing import Any

from scieasy.core.types.base import DataObject


class Series(DataObject):
    """One-dimensional indexed data (spectrum, chromatogram, time series).

    Attributes:
        index_name: Label for the index axis (e.g. "wavenumber", "mz").
        value_name: Label for the value axis (e.g. "intensity").
        length: Number of data points, if known.
    """

    def __init__(
        self,
        *,
        index_name: str | None = None,
        value_name: str | None = None,
        length: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.index_name = index_name
        self.value_name = value_name
        self.length = length


class Spectrum(Series):
    """Generic spectrum — a Series with spectral semantics."""


class RamanSpectrum(Spectrum):
    """Raman spectrum (index = wavenumber, value = intensity)."""


class MassSpectrum(Spectrum):
    """Mass spectrum (index = m/z, value = intensity)."""
