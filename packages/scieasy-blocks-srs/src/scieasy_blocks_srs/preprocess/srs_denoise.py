"""SRSDenoise - spatio-spectral denoising."""

from __future__ import annotations

from typing import Any, ClassVar, cast

import numpy as np

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.utils.constraints import has_axes
from scieasy_blocks_srs.types import SRSImage

ALLOWED_METHODS: tuple[str, ...] = ("wavelet", "PCA_denoise", "SVD_truncation", "BM4D")


class SRSDenoise(ProcessBlock):
    """Denoise an :class:`SRSImage` along the spectral and spatial axes."""

    name: ClassVar[str] = "SRS Denoise"
    description: ClassVar[str] = "Spatio-spectral denoising via PCA/SVD/wavelet/BM4D."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "preprocessing"
    algorithm: ClassVar[str] = "spectral_denoise"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[SRSImage],
            description="SRSImage with y/x/lambda axes.",
            constraint=has_axes("y", "x", "lambda"),
            constraint_description="image must carry y/x/lambda axes",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="image",
            accepted_types=[SRSImage],
            description="Denoised SRSImage with preserved meta.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": list(ALLOWED_METHODS),
                "default": "PCA_denoise",
            },
            "n_components": {"type": "integer", "default": 10, "minimum": 1},
            "wavelet": {"type": "string", "default": "db4"},
        },
    }

    def process_item(self, item: SRSImage, config: BlockConfig, state: Any = None) -> SRSImage:
        """Reshape, dispatch on ``method``, reconstruct, return new SRSImage."""
        method = str(config.get("method", "PCA_denoise"))
        n_components = int(config.get("n_components", 10))
        wavelet = str(config.get("wavelet", "db4"))

        if method not in ALLOWED_METHODS:
            raise ValueError(f"SRSDenoise: unknown method {method!r}; expected one of {ALLOWED_METHODS}")

        lambda_pos = item.axes.index("lambda")
        moved = np.moveaxis(np.asarray(item.to_memory(), dtype=np.float64), lambda_pos, -1)
        n_w = moved.shape[-1]
        if n_components > n_w:
            raise ValueError(f"SRSDenoise: n_components={n_components} exceeds n_wavenumbers={n_w}")

        if method == "PCA_denoise":
            recon = _denoise_pca(moved, n_components=n_components)
        elif method == "SVD_truncation":
            recon = _denoise_svd(moved, n_components=n_components)
        elif method == "wavelet":
            recon = _denoise_wavelet(moved, wavelet=wavelet)
        else:
            recon = _denoise_bm4d(moved)

        out_data = np.moveaxis(np.asarray(recon, dtype=np.float32), -1, lambda_pos)
        out = SRSImage(
            axes=list(item.axes),
            shape=out_data.shape,
            dtype=out_data.dtype,
            chunk_shape=item.chunk_shape,
            framework=item.framework.derive(),
            meta=item.meta,
            user=dict(item.user),
            storage_ref=None,
        )
        out._data = out_data  # type: ignore[attr-defined]
        return out


def _denoise_pca(spec: np.ndarray, *, n_components: int) -> np.ndarray:
    flat = spec.reshape(-1, spec.shape[-1])
    from sklearn.decomposition import PCA

    pca = PCA(n_components=n_components, random_state=42)
    transformed = pca.fit_transform(flat)
    recon = pca.inverse_transform(transformed)
    return cast(np.ndarray, recon.reshape(spec.shape))


def _denoise_svd(spec: np.ndarray, *, n_components: int) -> np.ndarray:
    flat = spec.reshape(-1, spec.shape[-1])
    u, s, vt = np.linalg.svd(flat, full_matrices=False)
    truncated = np.zeros_like(s)
    truncated[:n_components] = s[:n_components]
    recon = (u * truncated) @ vt
    return cast(np.ndarray, recon.reshape(spec.shape))


def _denoise_wavelet(spec: np.ndarray, *, wavelet: str) -> np.ndarray:
    try:
        import pywt
    except ImportError as exc:
        raise ValueError("SRSDenoise: wavelet method requires pip install scieasy-blocks-srs[pywt]") from exc

    flat = spec.reshape(-1, spec.shape[-1])
    recon = np.empty_like(flat)
    wavelet_obj = pywt.Wavelet(wavelet)
    max_level = min(3, pywt.dwt_max_level(spec.shape[-1], wavelet_obj.dec_len))

    for idx, row in enumerate(flat):
        if max_level == 0:
            recon[idx] = row
            continue
        coeffs = pywt.wavedec(row, wavelet_obj, level=max_level)
        details = coeffs[1:]
        if not details:
            recon[idx] = row
            continue
        sigma = np.median(np.abs(details[-1])) / 0.6745 if details[-1].size else 0.0
        threshold = sigma * np.sqrt(2.0 * np.log(row.size))
        denoised_coeffs = [coeffs[0], *[pywt.threshold(detail, threshold, mode="soft") for detail in details]]
        restored = pywt.waverec(denoised_coeffs, wavelet_obj)
        recon[idx] = restored[: row.size]

    return cast(np.ndarray, recon.reshape(spec.shape))


def _denoise_bm4d(spec: np.ndarray) -> np.ndarray:
    try:
        from bm4d import bm4d
    except ImportError as exc:
        raise ValueError("SRSDenoise: BM4D requires pip install scieasy-blocks-srs[bm4d]") from exc

    if spec.ndim == 3:
        return np.asarray(bm4d(spec, sigma_psd=0.1))

    leading = spec.shape[:-3]
    recon = np.empty_like(spec)
    for idx in np.ndindex(*leading):
        recon[idx] = np.asarray(bm4d(spec[idx], sigma_psd=0.1))
    return recon


__all__ = ["ALLOWED_METHODS", "SRSDenoise"]
