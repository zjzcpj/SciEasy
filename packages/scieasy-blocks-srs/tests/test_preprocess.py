"""Test stubs for SRS preprocess blocks (T-SRS-002 ... T-SRS-005).

All tests skipped pending implementation. Each ticket's impl agent
replaces the stubs in its corresponding ``class TestT_SRS_NNN`` block
with real assertions.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="SRS preprocess impl pending — skeleton stub")


# ---------------------------------------------------------------------------
# T-SRS-002 — SRSCalibrate
# ---------------------------------------------------------------------------


def test_calibrate_smoke_minimal() -> None:
    """SRSCalibrate runs end-to-end on a minimal Image input."""


def test_calibrate_inversion_formula() -> None:
    """Element-wise (pixel/4096*10 - 0)/1 inversion verified."""


def test_calibrate_offset_nonzero() -> None:
    """Non-zero offset is honoured."""


def test_calibrate_scale_nonzero() -> None:
    """Non-unit scale is honoured; scale=0 raises."""


def test_calibrate_meta_populated() -> None:
    """Output SRSImage.Meta carries the four digitizer parameters."""


def test_calibrate_wavenumbers_passthrough() -> None:
    """wavenumbers_cm1 config is written into output meta."""


def test_calibrate_rejects_srsimage_input() -> None:
    """Re-running on an SRSImage raises ValueError (spec §8 Q1)."""


def test_calibrate_rejects_image_with_digitizer_meta() -> None:
    """Image whose meta already has digitizer fields raises ValueError."""


def test_calibrate_5d_input_with_c_axis() -> None:
    """5D inputs with extra c axis succeed."""


def test_calibrate_lambda_axis_required() -> None:
    """Inputs without a lambda axis are rejected by the port constraint."""


def test_calibrate_collection_input() -> None:
    """Collection of Image is iterated and produces a Collection of SRSImage."""


def test_calibrate_dtype_float32() -> None:
    """Output dtype is always float32."""


# ---------------------------------------------------------------------------
# T-SRS-003 — SRSBaseline
# ---------------------------------------------------------------------------


def test_baseline_smoke_polynomial() -> None:
    """Polynomial baseline subtraction runs and shrinks the residual."""


def test_baseline_default_method_is_polynomial() -> None:
    """Default method is polynomial with order=3."""


def test_baseline_polynomial_order_param() -> None:
    """The order param is honoured."""


def test_baseline_rubber_band_smoke() -> None:
    """Rubber-band baseline runs."""


def test_baseline_rolling_ball_spectral_smoke() -> None:
    """Rolling-ball-spectral baseline runs."""


def test_baseline_rejects_als_method() -> None:
    """method='als' raises ValueError naming the three accepted methods."""


def test_baseline_unknown_method_raises() -> None:
    """Any unknown method string raises ValueError."""


def test_baseline_5d_with_c_axis_iterates() -> None:
    """5D input with extra c axis succeeds via the moveaxis broadcast pattern."""


def test_baseline_preserves_meta() -> None:
    """Output meta is identical to input meta."""


def test_baseline_dtype_float32() -> None:
    """Output dtype is float32."""


# ---------------------------------------------------------------------------
# T-SRS-004 — SRSDenoise
# ---------------------------------------------------------------------------


def test_denoise_smoke_pca() -> None:
    """PCA_denoise runs end-to-end."""


def test_denoise_smoke_svd_truncation() -> None:
    """SVD_truncation runs end-to-end."""


def test_denoise_smoke_wavelet() -> None:
    """Wavelet runs end-to-end (skipped if pywt missing)."""


def test_denoise_smoke_bm4d() -> None:
    """BM4D runs end-to-end (skipped if bm4d missing)."""


def test_denoise_unknown_method_raises() -> None:
    """Unknown method raises ValueError."""


def test_denoise_n_components_validation() -> None:
    """n_components > n_wavenumbers raises ValueError."""


def test_denoise_meta_preserved() -> None:
    """Output meta is identical to input meta."""


def test_denoise_dtype_float32() -> None:
    """Output dtype is float32."""


def test_denoise_5d_with_c() -> None:
    """5D input with extra c axis succeeds."""


def test_denoise_pca_reduces_noise() -> None:
    """PCA denoise on synthetic Gaussian noise lowers RMS error."""


# ---------------------------------------------------------------------------
# T-SRS-005 — SRSNormalize
# ---------------------------------------------------------------------------


def test_normalize_snv() -> None:
    """SNV: per-row mean ≈ 0, std ≈ 1."""


def test_normalize_msc() -> None:
    """MSC corrects synthetic offset/slope."""


def test_normalize_vector() -> None:
    """vector: per-row L2 norm ≈ 1."""


def test_normalize_area() -> None:
    """area: per-row sum ≈ 1."""


def test_normalize_peak_area_with_reference_peak() -> None:
    """peak_area divides each row by intensity at the reference peak."""


def test_normalize_peak_area_requires_wavenumbers() -> None:
    """peak_area without meta.wavenumbers_cm1 raises ValueError."""


def test_normalize_unknown_method_raises() -> None:
    """Unknown method raises ValueError."""


def test_normalize_meta_preserved() -> None:
    """Output meta is identical to input meta."""


def test_normalize_dtype_float32() -> None:
    """Output dtype is float32."""
