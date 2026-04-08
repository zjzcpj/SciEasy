"""Tests for SRS preprocess blocks (T-SRS-002 ... T-SRS-005)."""

from __future__ import annotations

import numpy as np
import pytest
from scieasy_blocks_srs import SRSBaseline, SRSCalibrate, SRSDenoise, SRSImage, SRSNormalize

from scieasy.blocks.base.block import BlockConfig
from scieasy.core.types.collection import Collection


def _config(**params: object) -> BlockConfig:
    return BlockConfig(params=dict(params))


def _raw_image(
    image_cls: type,
    data: np.ndarray,
    *,
    axes: list[str] | None = None,
    meta: object | None = None,
) -> object:
    arr = np.asarray(data)
    image = image_cls(
        axes=axes or ["y", "x", "lambda"],
        shape=arr.shape,
        dtype=arr.dtype,
        meta=meta,
    )
    image._data = arr  # type: ignore[attr-defined]
    return image


def _srs_image(
    data: np.ndarray,
    *,
    axes: list[str] | None = None,
    meta: SRSImage.Meta | None = None,
) -> SRSImage:
    arr = np.asarray(data)
    image = SRSImage(
        axes=axes or ["y", "x", "lambda"],
        shape=arr.shape,
        dtype=arr.dtype,
        meta=meta or SRSImage.Meta(wavenumbers_cm1=list(np.linspace(2850.0, 2930.0, arr.shape[-1]))),
    )
    image._data = arr  # type: ignore[attr-defined]
    return image


def _spectral_cube(
    *,
    axes: list[str] | None = None,
    shape: tuple[int, ...] = (4, 4, 8),
    baseline_scale: float = 0.3,
) -> SRSImage:
    axes = axes or ["y", "x", "lambda"]
    lambda_axis = axes.index("lambda")
    wavelengths = np.linspace(2850.0, 2930.0, shape[lambda_axis], dtype=np.float32)
    line = np.linspace(0.0, 1.0, shape[lambda_axis], dtype=np.float32)
    baseline = baseline_scale * (0.4 + 0.8 * line + 0.6 * line**2)
    peak = np.exp(-((wavelengths - 2890.0) ** 2) / (2.0 * 8.0**2)).astype(np.float32)
    spectrum = baseline + peak
    reshape = [1] * len(shape)
    reshape[lambda_axis] = shape[lambda_axis]
    cube = np.broadcast_to(spectrum.reshape(reshape), shape).astype(np.float32).copy()
    cube += 0.02 * np.arange(cube.size, dtype=np.float32).reshape(shape)
    return _srs_image(cube, axes=axes, meta=SRSImage.Meta(wavenumbers_cm1=list(wavelengths), laser_power=5.0))


def test_calibrate_smoke_minimal(imaging_types: object) -> None:
    raw = _raw_image(imaging_types.Image, np.arange(12, dtype=np.uint16).reshape(2, 2, 3))
    out = SRSCalibrate().process_item(raw, _config())

    assert isinstance(out, SRSImage)
    assert out.shape == (2, 2, 3)


def test_calibrate_inversion_formula(imaging_types: object) -> None:
    raw = _raw_image(imaging_types.Image, np.array([[[0, 2048, 4096]]], dtype=np.uint16))
    out = SRSCalibrate().process_item(raw, _config(bit_depth=4096, voltage_range=10.0, offset=0.0, scale=1.0))

    np.testing.assert_allclose(np.asarray(out._data), np.array([[[0.0, 5.0, 10.0]]], dtype=np.float32))


def test_calibrate_offset_nonzero(imaging_types: object) -> None:
    raw = _raw_image(imaging_types.Image, np.array([[[4096]]], dtype=np.uint16))
    out = SRSCalibrate().process_item(raw, _config(offset=2.5))

    assert float(np.asarray(out._data)[0, 0, 0]) == pytest.approx(7.5)


def test_calibrate_scale_nonzero(imaging_types: object) -> None:
    raw = _raw_image(imaging_types.Image, np.array([[[4096]]], dtype=np.uint16))
    out = SRSCalibrate().process_item(raw, _config(scale=2.0))

    assert float(np.asarray(out._data)[0, 0, 0]) == pytest.approx(5.0)

    with pytest.raises(ValueError, match="non-zero"):
        SRSCalibrate().process_item(raw, _config(scale=0.0))


def test_calibrate_meta_populated(imaging_types: object) -> None:
    raw = _raw_image(imaging_types.Image, np.ones((2, 2, 4), dtype=np.uint16))
    out = SRSCalibrate().process_item(raw, _config(bit_depth=2048, voltage_range=5.0, offset=0.25, scale=0.5))

    assert out.meta is not None
    assert out.meta.digitizer_bit_depth == 2048
    assert out.meta.digitizer_voltage_range == 5.0
    assert out.meta.digitizer_offset == 0.25
    assert out.meta.digitizer_scale == 0.5


def test_calibrate_wavenumbers_passthrough(imaging_types: object) -> None:
    wavenumbers = [2850.0, 2880.0, 2930.0]
    raw = _raw_image(imaging_types.Image, np.arange(6, dtype=np.uint16).reshape(1, 2, 3))
    out = SRSCalibrate().process_item(raw, _config(wavenumbers_cm1=wavenumbers))

    assert out.meta is not None
    assert out.meta.wavenumbers_cm1 == wavenumbers


def test_calibrate_rejects_srsimage_input() -> None:
    image = _srs_image(np.ones((2, 2, 4), dtype=np.float32))

    with pytest.raises(ValueError, match="SRSImage input"):
        SRSCalibrate().process_item(image, _config())


def test_calibrate_rejects_image_with_digitizer_meta(imaging_types: object) -> None:
    raw = _raw_image(
        imaging_types.Image,
        np.ones((2, 2, 4), dtype=np.uint16),
        meta=SRSImage.Meta(digitizer_bit_depth=4096),
    )

    with pytest.raises(ValueError, match="digitizer fields"):
        SRSCalibrate().process_item(raw, _config())


def test_calibrate_5d_input_with_c_axis(imaging_types: object) -> None:
    data = np.arange(2 * 3 * 6 * 4 * 5, dtype=np.uint16).reshape(2, 3, 6, 4, 5)
    raw = _raw_image(imaging_types.Image, data, axes=["t", "c", "lambda", "y", "x"])
    out = SRSCalibrate().process_item(raw, _config(wavenumbers_cm1=list(np.linspace(2850.0, 2930.0, 6))))

    assert out.axes == ["t", "c", "lambda", "y", "x"]
    assert out.shape == data.shape


def test_calibrate_lambda_axis_required(imaging_types: object) -> None:
    raw = _raw_image(imaging_types.Image, np.ones((4, 4), dtype=np.uint16), axes=["y", "x"])
    collection = Collection(items=[raw], item_type=imaging_types.Image)

    with pytest.raises(ValueError, match="constraint failed"):
        SRSCalibrate().validate({"image": collection})


def test_calibrate_collection_input(imaging_types: object) -> None:
    first = _raw_image(imaging_types.Image, np.ones((2, 2, 3), dtype=np.uint16))
    second = _raw_image(imaging_types.Image, 2 * np.ones((2, 2, 3), dtype=np.uint16))
    result = SRSCalibrate().run(
        {"image": Collection(items=[first, second], item_type=imaging_types.Image)},
        _config(wavenumbers_cm1=[2850.0, 2880.0, 2930.0]),
    )

    assert result["srs_image"].item_type is SRSImage
    assert len(result["srs_image"]) == 2
    assert all(isinstance(item, SRSImage) for item in result["srs_image"])


def test_calibrate_dtype_float32(imaging_types: object) -> None:
    raw = _raw_image(imaging_types.Image, np.arange(12, dtype=np.uint16).reshape(2, 2, 3))
    out = SRSCalibrate().process_item(raw, _config())

    assert out.dtype == np.dtype(np.float32)
    assert np.asarray(out._data).dtype == np.float32


def test_baseline_smoke_polynomial() -> None:
    image = _spectral_cube()
    out = SRSBaseline().process_item(image, _config(method="polynomial", order=2))

    assert out.shape == image.shape
    assert np.asarray(out._data).mean() < np.asarray(image._data).mean()


def test_baseline_default_method_is_polynomial() -> None:
    wavelengths = np.linspace(-1.0, 1.0, 8, dtype=np.float32)
    spectrum = 0.5 + 0.4 * wavelengths + 0.3 * wavelengths**2 + 0.2 * wavelengths**3
    image = _srs_image(spectrum.reshape(1, 1, -1).astype(np.float32))
    out = SRSBaseline().process_item(image, _config())

    np.testing.assert_allclose(np.asarray(out._data), 0.0, atol=1e-5)


def test_baseline_polynomial_order_param() -> None:
    wavelengths = np.linspace(-1.0, 1.0, 10, dtype=np.float32)
    spectrum = 0.5 + 0.25 * wavelengths + 0.5 * wavelengths**2
    image = _srs_image(spectrum.reshape(1, 1, -1).astype(np.float32))

    low_order = np.asarray(SRSBaseline().process_item(image, _config(order=1))._data)
    matched_order = np.asarray(SRSBaseline().process_item(image, _config(order=2))._data)

    assert float(np.abs(matched_order).max()) < float(np.abs(low_order).max())


def test_baseline_rubber_band_smoke() -> None:
    spectrum = np.array([1.0, 2.0, 5.0, 2.0, 1.0], dtype=np.float32).reshape(1, 1, 5)
    image = _srs_image(spectrum, meta=SRSImage.Meta(wavenumbers_cm1=[1.0, 2.0, 3.0, 4.0, 5.0]))
    out = SRSBaseline().process_item(image, _config(method="rubber_band"))
    corrected = np.asarray(out._data)

    np.testing.assert_allclose(corrected[..., [0, -1]], 0.0, atol=1e-6)
    assert float(corrected[0, 0, 2]) > 0.0


def test_baseline_rolling_ball_spectral_smoke() -> None:
    spectrum = np.array([1.0, 1.0, 4.0, 1.0, 1.0], dtype=np.float32).reshape(1, 1, 5)
    image = _srs_image(spectrum, meta=SRSImage.Meta(wavenumbers_cm1=[1.0, 2.0, 3.0, 4.0, 5.0]))
    out = SRSBaseline().process_item(image, _config(method="rolling_ball_spectral", window=3))
    corrected = np.asarray(out._data)

    np.testing.assert_allclose(corrected[..., [0, 1, 3, 4]], 0.0, atol=1e-6)
    assert float(corrected[0, 0, 2]) == pytest.approx(3.0)


def test_baseline_rejects_als_method() -> None:
    image = _spectral_cube()

    with pytest.raises(ValueError, match="ALS is intentionally unsupported"):
        SRSBaseline().process_item(image, _config(method="als"))


def test_baseline_unknown_method_raises() -> None:
    image = _spectral_cube()

    with pytest.raises(ValueError, match="method must be one of"):
        SRSBaseline().process_item(image, _config(method="bogus"))


def test_baseline_5d_with_c_axis_iterates() -> None:
    image = _spectral_cube(axes=["t", "c", "lambda", "y", "x"], shape=(2, 3, 8, 4, 5))
    out = SRSBaseline().process_item(image, _config(method="polynomial", order=2))

    assert out.axes == image.axes
    assert out.shape == image.shape


def test_baseline_preserves_meta() -> None:
    image = _spectral_cube()
    out = SRSBaseline().process_item(image, _config())

    assert out.meta == image.meta


def test_baseline_dtype_float32() -> None:
    image = _spectral_cube()
    out = SRSBaseline().process_item(image, _config())

    assert out.dtype == np.dtype(np.float32)
    assert np.asarray(out._data).dtype == np.float32


def test_denoise_smoke_pca() -> None:
    image = _spectral_cube(shape=(6, 6, 12))
    out = SRSDenoise().process_item(image, _config(method="PCA_denoise", n_components=3))

    assert out.shape == image.shape
    assert isinstance(out, SRSImage)


def test_denoise_smoke_svd_truncation() -> None:
    image = _spectral_cube(shape=(6, 6, 12))
    out = SRSDenoise().process_item(image, _config(method="SVD_truncation", n_components=3))

    assert out.shape == image.shape


def test_denoise_smoke_wavelet() -> None:
    pytest.importorskip("pywt")
    image = _spectral_cube(shape=(4, 4, 16))
    out = SRSDenoise().process_item(image, _config(method="wavelet", wavelet="db2"))

    assert out.shape == image.shape


def test_denoise_smoke_bm4d() -> None:
    pytest.importorskip("bm4d")
    image = _spectral_cube(shape=(8, 8, 8))
    out = SRSDenoise().process_item(image, _config(method="BM4D"))

    assert out.shape == image.shape


def test_denoise_unknown_method_raises() -> None:
    image = _spectral_cube()

    with pytest.raises(ValueError, match="unknown method"):
        SRSDenoise().process_item(image, _config(method="bogus"))


def test_denoise_n_components_validation() -> None:
    image = _spectral_cube(shape=(4, 4, 6))

    with pytest.raises(ValueError, match="exceeds"):
        SRSDenoise().process_item(image, _config(method="PCA_denoise", n_components=7))


def test_denoise_meta_preserved() -> None:
    image = _spectral_cube(shape=(6, 6, 12))
    out = SRSDenoise().process_item(image, _config(method="PCA_denoise", n_components=3))

    assert out.meta == image.meta


def test_denoise_dtype_float32() -> None:
    image = _spectral_cube(shape=(6, 6, 12))
    out = SRSDenoise().process_item(image, _config(method="PCA_denoise", n_components=3))

    assert out.dtype == np.dtype(np.float32)
    assert np.asarray(out._data).dtype == np.float32


def test_denoise_5d_with_c() -> None:
    image = _spectral_cube(axes=["t", "c", "lambda", "y", "x"], shape=(2, 3, 10, 4, 5))
    out = SRSDenoise().process_item(image, _config(method="SVD_truncation", n_components=3))

    assert out.axes == image.axes
    assert out.shape == image.shape


def test_denoise_pca_reduces_noise() -> None:
    wavelengths = np.linspace(2850.0, 2930.0, 20, dtype=np.float32)
    clean = np.sin(np.linspace(0.0, np.pi, 20, dtype=np.float32))
    base = np.tile(clean, (8, 8, 1)).astype(np.float32)
    rng = np.random.default_rng(42)
    noisy = base + rng.normal(0.0, 0.2, size=base.shape).astype(np.float32)
    image = _srs_image(noisy, meta=SRSImage.Meta(wavenumbers_cm1=list(wavelengths)))

    denoised = np.asarray(SRSDenoise().process_item(image, _config(method="PCA_denoise", n_components=2))._data)
    noisy_error = float(np.sqrt(np.mean((noisy - base) ** 2)))
    denoised_error = float(np.sqrt(np.mean((denoised - base) ** 2)))

    assert denoised_error < noisy_error


def test_normalize_snv() -> None:
    data = np.array(
        [
            [[1.0, 2.0, 3.0, 4.0], [2.0, 3.0, 4.0, 5.0]],
            [[4.0, 5.0, 6.0, 7.0], [5.0, 6.0, 7.0, 8.0]],
        ],
        dtype=np.float32,
    )
    out = SRSNormalize().process_item(_srs_image(data), _config(method="SNV"))
    flat = np.asarray(out._data).reshape(-1, 4)

    np.testing.assert_allclose(flat.mean(axis=1), 0.0, atol=1e-6)
    np.testing.assert_allclose(flat.std(axis=1), 1.0, atol=1e-6)


def test_normalize_msc() -> None:
    reference = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
    data = np.stack(
        [
            2.0 * reference + 5.0,
            0.5 * reference - 1.5,
        ],
        axis=0,
    ).reshape(1, 2, 4)
    out = SRSNormalize().process_item(_srs_image(data), _config(method="MSC"))
    corrected = np.asarray(out._data).reshape(2, 4)

    np.testing.assert_allclose(corrected[0], corrected[1], atol=1e-5)


def test_normalize_vector() -> None:
    out = SRSNormalize().process_item(_srs_image(np.array([[[3.0, 4.0]]], dtype=np.float32)), _config(method="vector"))
    norm = float(np.linalg.norm(np.asarray(out._data).reshape(-1, 2), axis=1)[0])

    assert norm == pytest.approx(1.0)


def test_normalize_area() -> None:
    out = SRSNormalize().process_item(
        _srs_image(np.array([[[1.0, 1.0, 2.0]]], dtype=np.float32)), _config(method="area")
    )
    total = float(np.asarray(out._data).sum())

    assert total == pytest.approx(1.0)


def test_normalize_peak_area_with_reference_peak() -> None:
    data = np.array([[[2.0, 4.0, 8.0]]], dtype=np.float32)
    image = _srs_image(data, meta=SRSImage.Meta(wavenumbers_cm1=[2850.0, 2880.0, 2930.0]))
    out = SRSNormalize().process_item(image, _config(method="peak_area", reference_peak_cm1=2880.0))

    np.testing.assert_allclose(np.asarray(out._data), np.array([[[0.5, 1.0, 2.0]]], dtype=np.float32))


def test_normalize_peak_area_requires_wavenumbers() -> None:
    image = _srs_image(np.array([[[2.0, 4.0, 8.0]]], dtype=np.float32), meta=SRSImage.Meta())

    with pytest.raises(ValueError, match="wavenumbers_cm1"):
        SRSNormalize().process_item(image, _config(method="peak_area", reference_peak_cm1=2880.0))


def test_normalize_unknown_method_raises() -> None:
    image = _spectral_cube()

    with pytest.raises(ValueError, match="unknown method"):
        SRSNormalize().process_item(image, _config(method="bogus"))


def test_normalize_meta_preserved() -> None:
    image = _spectral_cube()
    out = SRSNormalize().process_item(image, _config(method="SNV"))

    assert out.meta == image.meta


def test_normalize_dtype_float32() -> None:
    image = _spectral_cube()
    out = SRSNormalize().process_item(image, _config(method="SNV"))

    assert out.dtype == np.dtype(np.float32)
    assert np.asarray(out._data).dtype == np.float32
