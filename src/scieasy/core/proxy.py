"""ViewProxy — lazy-loading accessor injected into block run() inputs."""

from __future__ import annotations

import warnings
from collections.abc import Iterator
from typing import Any

from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.base import TypeSignature

# Warn when to_memory() would load more than this many bytes (2 GB).
_SIZE_WARNING_THRESHOLD = 2 * 1024 * 1024 * 1024


def _get_backend(ref: StorageReference) -> Any:
    """Return the appropriate backend instance for *ref*."""
    from scieasy.core.storage.arrow_backend import ArrowBackend
    from scieasy.core.storage.composite_store import CompositeStore
    from scieasy.core.storage.filesystem import FilesystemBackend
    from scieasy.core.storage.zarr_backend import ZarrBackend

    backends: dict[str, Any] = {
        "zarr": ZarrBackend(),
        "arrow": ArrowBackend(),
        "filesystem": FilesystemBackend(),
        "composite": CompositeStore(),
    }
    if ref.backend not in backends:
        raise ValueError(f"Unknown backend: {ref.backend}")
    return backends[ref.backend]


class ViewProxy:
    """Lazy accessor that wraps a :class:`StorageReference` and defers I/O.

    Blocks receive ``ViewProxy`` instances as inputs so that data is only
    materialised when explicitly requested.
    """

    def __init__(
        self,
        storage_ref: StorageReference,
        dtype_info: TypeSignature,
    ) -> None:
        self._storage_ref = storage_ref
        self._dtype_info = dtype_info
        self._metadata_cache: dict[str, Any] | None = None

    @property
    def storage_ref(self) -> StorageReference:
        """Return the underlying storage reference."""
        return self._storage_ref

    @property
    def dtype_info(self) -> TypeSignature:
        """Return the type signature of the wrapped data object."""
        return self._dtype_info

    def _cached_metadata(self) -> dict[str, Any]:
        """Fetch and cache backend metadata (no data loaded)."""
        if self._metadata_cache is None:
            backend = _get_backend(self._storage_ref)
            self._metadata_cache = backend.get_metadata(self._storage_ref)
        return self._metadata_cache

    # -- properties ----------------------------------------------------------

    @property
    def shape(self) -> tuple[int, ...] | None:
        """Return the shape of the underlying data, if applicable.

        For Zarr-backed arrays, reads shape from metadata without loading data.
        Returns None for backends that don't have a shape concept.
        """
        meta = self._cached_metadata()
        raw_shape = meta.get("shape")
        if raw_shape is not None:
            return tuple(raw_shape)
        return None

    @property
    def axes(self) -> list[str] | None:
        """Return the axis labels of the underlying data, if applicable.

        Reads from the StorageReference metadata (set when writing an Array
        with named axes). Returns None if no axes metadata is available.
        """
        if self._storage_ref.metadata:
            return self._storage_ref.metadata.get("axes")
        return None

    # -- data access ---------------------------------------------------------

    def slice(self, *args: Any) -> Any:
        """Return a sub-selection of the data without full materialisation.

        For Zarr arrays: pass numpy-style index expressions.
        For Arrow tables: pass a list of column names.
        For filesystem: pass (offset, length).
        """
        backend = _get_backend(self._storage_ref)
        return backend.slice(self._storage_ref, *args)

    def to_memory(self) -> Any:
        """Materialise the full data into memory.

        Emits a warning if the data is larger than 2 GB.
        """
        meta = self._cached_metadata()
        # Estimate size for warning
        size = meta.get("size")
        if size is None:
            shape = meta.get("shape")
            if shape is not None:
                import math

                # Rough estimate: 8 bytes per element (float64)
                size = math.prod(shape) * 8
        if size is not None and size > _SIZE_WARNING_THRESHOLD:
            warnings.warn(
                f"Loading {size / (1024**3):.1f} GB into memory. Consider using .slice() or .iter_chunks() instead.",
                ResourceWarning,
                stacklevel=2,
            )
        backend = _get_backend(self._storage_ref)
        return backend.read(self._storage_ref)

    def iter_chunks(self, chunk_size: int) -> Iterator[Any]:
        """Yield successive chunks of the data."""
        backend = _get_backend(self._storage_ref)
        yield from backend.iter_chunks(self._storage_ref, chunk_size)
