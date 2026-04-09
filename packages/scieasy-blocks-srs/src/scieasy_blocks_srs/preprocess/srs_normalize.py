"""SRSNormalize - per-spectrum intensity normalization."""

from __future__ import annotations

from typing import Any, ClassVar, cast

import numpy as np

from scieasy.blocks.base.block import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.utils.constraints import has_axes
from scieasy_blocks_srs.types import SRSImage

ALLOWED_METHODS: tuple[str, ...] = ("SNV", "MSC", "vector", "area", "peak_area")


class SRSNormalize(ProcessBlock):
    """Normalize each per-pixel spectrum."""

    name: ClassVar[str] = "SRS Normalize"
    type_name: ClassVar[str] = "srs.normalize"
    description: ClassVar[str] = "Per-spectrum intensity normalization (SNV/MSC/vector/area/peak_area)."
    version: ClassVar[str] = "0.1.0"
    category: ClassVar[str] = "preprocessing"
    algorithm: ClassVar[str] = "spectral_normalize"

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
            description="Normalized SRSImage with preserved meta.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": list(ALLOWED_METHODS),
                "default": "SNV",
            },
            "reference_peak_cm1": {"type": ["number", "null"], "default": None},
        },
    }

    def process_item(self, item: SRSImage, config: BlockConfig, state: Any = None) -> SRSImage:
        """Reshape to ``(n_pixels, n_w)`` and dispatch on ``method``."""
        method = str(config.get("method", "SNV"))
        reference_peak_cm1 = config.get("reference_peak_cm1")
        if method not in ALLOWED_METHODS:
            raise ValueError(f"SRSNormalize: unknown method {method!r}; expected one of {ALLOWED_METHODS}")

        lambda_pos = item.axes.index("lambda")
        moved = np.moveaxis(np.asarray(item.to_memory(), dtype=np.float64), lambda_pos, -1)
        flat = moved.reshape(-1, moved.shape[-1])

        if method == "SNV":
            normalized = _normalize_snv(flat)
        elif method == "MSC":
            normalized = _normalize_msc(flat)
        elif method == "vector":
            normalized = _normalize_vector(flat)
        elif method == "area":
            normalized = _normalize_area(flat)
        else:
            if reference_peak_cm1 is None:
                raise ValueError("SRSNormalize: peak_area requires reference_peak_cm1")
            if item.meta is None or item.meta.wavenumbers_cm1 is None:
                raise ValueError("SRSNormalize: peak_area requires item.meta.wavenumbers_cm1")
            normalized = _normalize_peak_area(
                flat,
                wavenumbers=item.meta.wavenumbers_cm1,
                reference_peak_cm1=float(reference_peak_cm1),
            )

        out_data = np.moveaxis(normalized.reshape(moved.shape).astype(np.float32), -1, lambda_pos)
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


def _normalize_snv(flat: np.ndarray) -> np.ndarray:
    means = flat.mean(axis=1, keepdims=True)
    stds = flat.std(axis=1, keepdims=True)
    return cast(np.ndarray, (flat - means) / (stds + 1e-12))


def _normalize_msc(flat: np.ndarray) -> np.ndarray:
    reference = flat.mean(axis=0)
    corrected = np.empty_like(flat)
    for idx, row in enumerate(flat):
        slope, intercept = np.polyfit(reference, row, 1)
        corrected[idx] = (row - intercept) / (slope + 1e-12)
    return cast(np.ndarray, corrected)


def _normalize_vector(flat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(flat, axis=1, keepdims=True)
    return cast(np.ndarray, flat / (norms + 1e-12))


def _normalize_area(flat: np.ndarray) -> np.ndarray:
    sums = flat.sum(axis=1, keepdims=True)
    return cast(np.ndarray, flat / (sums + 1e-12))


def _normalize_peak_area(flat: np.ndarray, *, wavenumbers: list[float], reference_peak_cm1: float) -> np.ndarray:
    idx = int(np.argmin(np.abs(np.asarray(wavenumbers, dtype=np.float64) - reference_peak_cm1)))
    return cast(np.ndarray, flat / (flat[:, [idx]] + 1e-12))


__all__ = ["ALLOWED_METHODS", "SRSNormalize"]
