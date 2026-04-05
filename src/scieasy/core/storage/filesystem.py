"""Plain filesystem storage backend for Text and Artifact types."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from scieasy.core.storage.ref import StorageReference


class FilesystemBackend:
    """Filesystem-based storage backend for text files and opaque artifacts."""

    def read(self, ref: StorageReference) -> Any:
        """Read a file from the filesystem at *ref*.

        For text formats (format starts with "text" or is "plain"/"markdown"/"json"),
        reads as UTF-8 string. Otherwise reads as bytes.
        """
        path = Path(ref.path)
        text_formats = {"plain", "markdown", "json", "text", "csv"}
        fmt = (ref.format or "").lower()
        if fmt in text_formats or fmt.startswith("text"):
            return path.read_text(encoding="utf-8")
        return path.read_bytes()

    def write(self, data: Any, ref: StorageReference) -> StorageReference:
        """Write *data* (str or bytes) to the filesystem at *ref*."""
        path = Path(ref.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
        elif isinstance(data, bytes):
            path.write_bytes(data)
        else:
            raise TypeError(f"FilesystemBackend.write expects str or bytes, got {type(data).__name__}")
        metadata = dict(ref.metadata) if ref.metadata else {}
        metadata["size"] = path.stat().st_size
        return StorageReference(
            backend="filesystem",
            path=ref.path,
            format=ref.format,
            metadata=metadata,
        )

    def write_from_memory(self, data: Any, path: str) -> StorageReference:
        """Write raw in-memory str/bytes data to the filesystem at *path*."""
        ref = StorageReference(backend="filesystem", path=path)
        return self.write(data, ref)

    def slice(self, ref: StorageReference, *args: Any) -> Any:
        """Return a byte-range slice from *ref*.

        Expects two positional args: (offset, length).
        """
        if len(args) != 2:
            raise ValueError("FilesystemBackend.slice expects (offset, length).")
        offset, length = int(args[0]), int(args[1])
        path = Path(ref.path)
        with path.open("rb") as f:
            f.seek(offset)
            return f.read(length)

    def iter_chunks(self, ref: StorageReference, chunk_size: int) -> Iterator[Any]:
        """Yield fixed-size byte chunks from *ref*."""
        path = Path(ref.path)
        with path.open("rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def get_metadata(self, ref: StorageReference) -> dict[str, Any]:
        """Return filesystem metadata (size, mtime, etc.) for *ref*."""
        path = Path(ref.path)
        stat = path.stat()
        return {
            "size": stat.st_size,
            "mtime": os.path.getmtime(ref.path),
            "name": path.name,
            "suffix": path.suffix,
        }
