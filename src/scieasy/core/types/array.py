"""Array type — wraps ndarray-like data, Zarr-backed for large datasets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from scieasy.core.types.base import DataObject

if TYPE_CHECKING:
    pass


class Array(DataObject):
    """N-dimensional array, optionally chunked and backed by Zarr.

    Attributes:
        axes: Class-level axis labels (e.g. ``["y", "x"]`` for images).
        shape: Shape of the array.
        ndim: Number of dimensions.
        dtype: Element data type.
        chunk_shape: Chunk dimensions for lazy/chunked storage.
    """

    axes: ClassVar[list[str] | None] = None

    def __init__(
        self,
        *,
        shape: tuple[int, ...] | None = None,
        ndim: int | None = None,
        dtype: Any = None,
        chunk_shape: tuple[int, ...] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.shape = shape
        self.ndim = ndim
        self.dtype = dtype
        self.chunk_shape = chunk_shape


class Image(Array):
    """2-D spatial image (y, x)."""

    axes: ClassVar[list[str] | None] = ["y", "x"]


class MSImage(Array):
    """Mass-spectrometry imaging hypercube (y, x, mz)."""

    axes: ClassVar[list[str] | None] = ["y", "x", "mz"]


class SRSImage(Image):
    """Stimulated Raman scattering image (y, x, wavenumber)."""

    axes: ClassVar[list[str] | None] = ["y", "x", "wavenumber"]


class FluorImage(Image):
    """Fluorescence multichannel image (y, x, channel)."""

    axes: ClassVar[list[str] | None] = ["y", "x", "channel"]
