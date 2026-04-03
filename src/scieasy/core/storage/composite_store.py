"""Directory-of-slots storage for CompositeData types."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from scieasy.core.storage.ref import StorageReference


class CompositeStore:
    """Storage backend for :class:`CompositeData`, persisting each slot independently.

    All methods raise :class:`NotImplementedError` in Phase 1.
    """

    def read(self, ref: StorageReference) -> Any:
        """Read a composite directory structure from *ref*."""
        raise NotImplementedError

    def write(self, data: Any, ref: StorageReference) -> StorageReference:
        """Write composite slots to a directory at *ref*."""
        raise NotImplementedError

    def slice(self, ref: StorageReference, *args: Any) -> Any:
        """Return a subset of slots from the composite at *ref*."""
        raise NotImplementedError

    def iter_chunks(self, ref: StorageReference, chunk_size: int) -> Iterator[Any]:
        """Yield slots from the composite at *ref*."""
        raise NotImplementedError

    def get_metadata(self, ref: StorageReference) -> dict[str, Any]:
        """Return metadata for the composite directory at *ref*."""
        raise NotImplementedError
