"""Test stubs for SRS spectral-extraction blocks (T-SRS-011 and T-SRS-012).

All tests skipped pending implementation.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="SRS spectral_extraction impl pending — skeleton stub")


# ---------------------------------------------------------------------------
# T-SRS-011 — ExtractSpectrum
# ---------------------------------------------------------------------------


def test_extract_no_roi_returns_single_spectrum() -> None:
    """No ROI input → single row block with region_id == 0."""


def test_extract_with_mask(imaging_types: object) -> None:
    """Mask input → single row block with region_id == 1."""


def test_extract_with_label_two_regions(imaging_types: object) -> None:
    """Label input → one row block per non-zero label value."""


def test_extract_label_value_zero_excluded(imaging_types: object) -> None:
    """Label value 0 is treated as background and excluded."""


def test_extract_long_format_columns() -> None:
    """Output columns are exactly ['region_id', 'wavenumber_cm1', 'intensity']."""


def test_extract_uses_meta_wavenumbers() -> None:
    """wavenumber_cm1 column is sourced from item.meta.wavenumbers_cm1."""


def test_extract_dtype_intensity_float() -> None:
    """intensity column dtype is floating-point."""


def test_extract_lambda_axis_required() -> None:
    """Inputs without a lambda axis are rejected."""


def test_extract_5d_with_c_axis_raises() -> None:
    """5D inputs with extra axes raise ValueError pointing at SelectSlice."""


def test_extract_mask_dtype_bool_required(imaging_types: object) -> None:
    """Non-bool Mask raster raises ValueError."""


def test_extract_label_dtype_int_required(imaging_types: object) -> None:
    """Non-integer Label raster raises ValueError."""


def test_extract_collection_input() -> None:
    """Collection of one input emits one DataFrame."""


# ---------------------------------------------------------------------------
# T-SRS-012 — BandRatio
# ---------------------------------------------------------------------------


def test_band_ratio_smoke_ch2_ch3() -> None:
    """Synthetic spectrum with known ratio recovers the expected value."""


def test_band_ratio_output_axes_yx() -> None:
    """Output Image has axes ['y','x'] (lambda is consumed)."""


def test_band_ratio_requires_wavenumbers_meta() -> None:
    """Missing meta.wavenumbers_cm1 raises ValueError."""


def test_band_ratio_band_outside_range_raises() -> None:
    """A band outside the wavenumber range raises ValueError."""


def test_band_ratio_dtype_float32() -> None:
    """Output dtype is float32."""


def test_band_ratio_zero_division_safe() -> None:
    """Zero denominator is protected by an epsilon."""


def test_band_ratio_collection_input() -> None:
    """Collection of one input is iterated correctly."""


def test_band_ratio_lambda_axis_required() -> None:
    """Inputs without a lambda axis are rejected."""
