"""Format adapter: TIFF / OME-TIFF image files to/from Image."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from scieasy.core.types.array import Image


class TIFFAdapter:
    """Format adapter for TIFF / OME-TIFF image files.

    Uses :mod:`tifffile` for reading/writing.  Falls back to a clear error
    message if tifffile is not installed.
    """

    def read(self, path: str | Path, **kwargs: Any) -> Image:
        """Read a TIFF file and return an :class:`Image`."""
        tifffile = _import_tifffile()
        path = Path(path)
        data = tifffile.imread(str(path), **kwargs)
        img = Image(
            shape=data.shape,
            ndim=data.ndim,
            dtype=data.dtype,
        )
        img._data = data  # type: ignore[attr-defined]
        return img

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        """Write data to a TIFF file."""
        tifffile = _import_tifffile()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, Image) and hasattr(data, "_data"):
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


def _import_tifffile() -> Any:
    """Import tifffile, raising a clear error if not installed."""
    try:
        import tifffile

        return tifffile
    except ImportError as exc:
        raise ImportError(
            "TIFFAdapter requires the 'tifffile' package. "
            "Install it with: pip install tifffile"
        ) from exc
