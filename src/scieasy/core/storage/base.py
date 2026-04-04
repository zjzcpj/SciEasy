"""StorageBackend protocol — read, write, slice, iter_chunks, metadata."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, runtime_checkable

from typing_extensions import Protocol

from scieasy.core.storage.ref import StorageReference


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol that every storage backend must satisfy.

    All methods raise :class:`NotImplementedError` in concrete stub
    implementations (Phase 1).
    """

    def read(self, ref: StorageReference) -> Any:
        """Read the data identified by *ref* and return it."""
        ...

    def write(self, data: Any, ref: StorageReference) -> StorageReference:
        """Write *data* to the location described by *ref*.

        Returns an updated :class:`StorageReference` with any backend-assigned
        metadata (e.g. chunk layout, checksum).

        Concrete implementations should handle both ViewProxy-backed objects
        and raw in-memory DataObjects (ADR-020-Add5).
        """
        ...

    def slice(self, ref: StorageReference, *args: Any) -> Any:
        """Return a sub-selection of the data identified by *ref*."""
        ...

    def iter_chunks(self, ref: StorageReference, chunk_size: int) -> Iterator[Any]:
        """Yield successive chunks of size *chunk_size* from *ref*."""
        ...

    def get_metadata(self, ref: StorageReference) -> dict[str, Any]:
        """Return backend-level metadata for the data at *ref*."""
        ...
