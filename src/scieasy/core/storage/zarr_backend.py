"""Zarr storage backend for Array types (chunked, compressed, lazy)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from scieasy.core.storage.ref import StorageReference


class ZarrBackend:
    """Zarr-based storage backend for chunked N-dimensional arrays.

    All methods raise :class:`NotImplementedError` in Phase 1.
    """

    def read(self, ref: StorageReference) -> Any:
        """Read a Zarr array from *ref*."""
        raise NotImplementedError

    def write(self, data: Any, ref: StorageReference) -> StorageReference:
        """Write *data* as a Zarr array to *ref*."""
        raise NotImplementedError

    def slice(self, ref: StorageReference, *args: Any) -> Any:
        """Return a sub-array slice from the Zarr store at *ref*."""
        raise NotImplementedError

    def iter_chunks(self, ref: StorageReference, chunk_size: int) -> Iterator[Any]:
        """Yield chunks of the Zarr array at *ref*."""
        raise NotImplementedError

    def get_metadata(self, ref: StorageReference) -> dict[str, Any]:
        """Return Zarr-level metadata for *ref*."""
        raise NotImplementedError
