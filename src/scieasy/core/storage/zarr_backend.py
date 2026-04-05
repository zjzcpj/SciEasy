"""Zarr storage backend for Array types (chunked, compressed, lazy)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import numpy as np
import zarr

from scieasy.core.storage.ref import StorageReference


class ZarrBackend:
    """Zarr-based storage backend for chunked N-dimensional arrays."""

    def read(self, ref: StorageReference) -> Any:
        """Read a Zarr array from *ref* and return it as a numpy array."""
        arr = zarr.open_array(ref.path, mode="r")
        return np.asarray(arr)

    def write(self, data: Any, ref: StorageReference) -> StorageReference:
        """Write *data* (numpy array) as a Zarr array to *ref*.

        Returns an updated :class:`StorageReference` with shape/dtype metadata.
        """
        arr = np.asarray(data)
        z = zarr.open_array(ref.path, mode="w", shape=arr.shape, dtype=arr.dtype)
        z[:] = arr
        # Persist axis metadata in Zarr attrs for round-trip fidelity.
        if ref.metadata and "axes" in ref.metadata:
            z.attrs["axes"] = ref.metadata["axes"]
        metadata = dict(ref.metadata) if ref.metadata else {}
        metadata.update({"shape": list(arr.shape), "dtype": str(arr.dtype)})
        return StorageReference(
            backend="zarr",
            path=ref.path,
            format=ref.format,
            metadata=metadata,
        )

    def slice(self, ref: StorageReference, *args: Any) -> Any:
        """Return a sub-array slice from the Zarr store at *ref*.

        *args* should be valid numpy-style index expressions (slices, ints).
        """
        arr = zarr.open_array(ref.path, mode="r")
        return np.asarray(arr[args])

    def iter_chunks(self, ref: StorageReference, chunk_size: int) -> Iterator[Any]:
        """Yield chunks along axis 0 of the Zarr array at *ref*."""
        arr = zarr.open_array(ref.path, mode="r")
        total = arr.shape[0]
        for start in range(0, total, chunk_size):
            end = min(start + chunk_size, total)
            yield np.asarray(arr[start:end])

    def write_from_memory(self, data: Any, path: str) -> StorageReference:
        """Write raw in-memory numpy data to a Zarr store at *path*."""
        ref = StorageReference(backend="zarr", path=path)
        return self.write(data, ref)

    def get_metadata(self, ref: StorageReference) -> dict[str, Any]:
        """Return Zarr-level metadata for *ref*."""
        arr = zarr.open_array(ref.path, mode="r")
        meta: dict[str, Any] = {
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
            "chunks": list(arr.chunks),
            "ndim": arr.ndim,
        }
        axes = arr.attrs.get("axes")
        if axes is not None:
            meta["axes"] = axes
        return meta
