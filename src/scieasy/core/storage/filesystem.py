"""Plain filesystem storage backend for Text and Artifact types."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from scieasy.core.storage.ref import StorageReference


class FilesystemBackend:
    """Filesystem-based storage backend for text files and opaque artifacts.

    All methods raise :class:`NotImplementedError` in Phase 1.
    """

    def read(self, ref: StorageReference) -> Any:
        """Read a file from the filesystem at *ref*."""
        raise NotImplementedError

    def write(self, data: Any, ref: StorageReference) -> StorageReference:
        """Write *data* to the filesystem at *ref*."""
        raise NotImplementedError

    def slice(self, ref: StorageReference, *args: Any) -> Any:
        """Return a byte-range or line-range slice from *ref*."""
        raise NotImplementedError

    def iter_chunks(self, ref: StorageReference, chunk_size: int) -> Iterator[Any]:
        """Yield fixed-size byte chunks from *ref*."""
        raise NotImplementedError

    def get_metadata(self, ref: StorageReference) -> dict[str, Any]:
        """Return filesystem metadata (size, mtime, etc.) for *ref*."""
        raise NotImplementedError
