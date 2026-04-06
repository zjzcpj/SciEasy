"""Format adapter: TIFF / OME-TIFF image files to/from Array.

Per ADR-027 D2 and T-006, the legacy ``Image`` domain subclass has been
removed from ``scieasy.core.types.array``. This adapter now returns a
generic :class:`Array` with ``axes=["y", "x"]`` (2D) or with higher-dim
axes inferred from the TIFF payload. A future imaging-plugin migration
will route through ``scieasy-blocks-imaging``'s ``Image`` subclass; this
module deliberately stays plugin-free so that core tests and the
``blocks/io`` stack keep working without the imaging plugin installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.array import Array

# ADR-027 D1 6D axis alphabet: ``("t", "z", "c", "lambda", "y", "x")``.
# TIFF files are traditionally ordered ``(page, channel?, y, x)``; we
# conservatively assume the trailing two axes are ``y, x`` and leave
# higher-dim inference to the imaging plugin (see TODO below).
_DEFAULT_2D_AXES: list[str] = ["y", "x"]


class TIFFAdapter:
    """Format adapter for TIFF / OME-TIFF image files.

    Uses tifffile for reading/writing. Falls back to a clear error
    message if tifffile is not installed.
    """

    def read(self, path: str | Path, **kwargs: Any) -> Array:
        """Read a TIFF file and return an :class:`Array`.

        The returned array has ``axes=["y", "x"]`` for 2D payloads.
        For higher-dim payloads, generic axes are generated (``"dim0"``,
        ``"dim1"``, ..., ``"y"``, ``"x"``) so that the data remains
        loadable without requiring the imaging plugin. The full imaging
        axis detection (OME-TIFF metadata, ``lambda`` / ``c`` /
        ``z`` / ``t``) belongs to ``scieasy-blocks-imaging``'s
        TIFF adapter.
        """
        # TODO(scieasy-blocks-imaging): move TIFF adapter to the imaging
        # plugin so it can consume OME-TIFF metadata and return a typed
        # ``Image`` instance with the full 6D axis alphabet. Until then
        # core ships this generic fallback.
        tifffile = _import_tifffile()
        path = Path(path)
        data = tifffile.imread(str(path), **kwargs)
        axes = _infer_axes(data.ndim)
        img = Array(
            axes=axes,
            shape=data.shape,
            dtype=data.dtype,
        )
        img._data = data  # type: ignore[attr-defined]
        return img

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        """Write data to a TIFF file."""
        tifffile = _import_tifffile()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, Array) and hasattr(data, "_data"):
            arr = data._data  # type: ignore[attr-defined]
        elif isinstance(data, np.ndarray):
            arr = data
        else:
            raise TypeError(f"Cannot write {type(data).__name__} as TIFF")

        tifffile.imwrite(str(path), arr, **kwargs)
        return path

    def supported_extensions(self) -> list[str]:
        """Return the list of file extensions this adapter handles."""
        return [".tif", ".tiff"]

    def create_reference(self, path: str | Path) -> StorageReference:
        """Build a StorageReference for a TIFF file without reading data."""
        return StorageReference(backend="filesystem", path=str(Path(path)), format="tiff")


def _infer_axes(ndim: int) -> list[str]:
    """Return a conservative axes list for a TIFF payload of rank ``ndim``.

    2D payloads get ``["y", "x"]``; higher-dim payloads get generic
    leading axes ``["dim0", "dim1", ...]`` followed by ``["y", "x"]``.
    The imaging plugin will replace this with OME-TIFF-aware detection.
    """
    if ndim <= 0:
        return []
    if ndim == 1:
        return ["x"]
    if ndim == 2:
        return list(_DEFAULT_2D_AXES)
    leading = [f"dim{i}" for i in range(ndim - 2)]
    return leading + list(_DEFAULT_2D_AXES)


def _import_tifffile() -> Any:
    """Import tifffile, raising a clear error if not installed."""
    try:
        import tifffile

        return tifffile
    except ImportError as exc:
        raise ImportError("TIFFAdapter requires the 'tifffile' package. Install it with: pip install tifffile") from exc
