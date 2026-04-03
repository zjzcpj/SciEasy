"""Apache Arrow / Parquet storage backend for DataFrame types."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from scieasy.core.storage.ref import StorageReference


class ArrowBackend:
    """Arrow/Parquet-based storage backend for columnar tabular data.

    All methods raise :class:`NotImplementedError` in Phase 1.
    """

    def read(self, ref: StorageReference) -> Any:
        """Read a Parquet/Arrow table from *ref*."""
        raise NotImplementedError

    def write(self, data: Any, ref: StorageReference) -> StorageReference:
        """Write *data* as Parquet to *ref*."""
        raise NotImplementedError

    def slice(self, ref: StorageReference, *args: Any) -> Any:
        """Return a row/column slice from the table at *ref*."""
        raise NotImplementedError

    def iter_chunks(self, ref: StorageReference, chunk_size: int) -> Iterator[Any]:
        """Yield row-group chunks from *ref*."""
        raise NotImplementedError

    def get_metadata(self, ref: StorageReference) -> dict[str, Any]:
        """Return Parquet-level metadata for *ref*."""
        raise NotImplementedError
