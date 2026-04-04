"""Format adapter: generic binary files to/from Artifact."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.artifact import Artifact


class GenericAdapter:
    """Fallback adapter that treats any file as an opaque Artifact.

    This adapter handles file extensions that are not covered by more
    specific adapters.  It reads files as binary blobs and wraps them
    in an Artifact data object.
    """

    def read(self, path: str | Path, **kwargs: Any) -> Artifact:
        """Read a file and return it as an Artifact."""
        path = Path(path)
        return Artifact(
            file_path=path,
            mime_type=_guess_mime(path),
            description=path.name,
        )

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        """Write data to a file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, Artifact) and data.file_path:
            import shutil

            shutil.copy2(data.file_path, path)
        elif isinstance(data, bytes):
            path.write_bytes(data)
        elif isinstance(data, str):
            path.write_text(data, encoding="utf-8")
        else:
            raise TypeError(f"Cannot write {type(data).__name__} as generic file")
        return path

    def supported_extensions(self) -> list[str]:
        """Return the list of file extensions this adapter handles."""
        return [".bin", ".dat", ".pdf", ".png", ".jpg", ".jpeg"]

    def create_reference(self, path: str | Path) -> StorageReference:
        """Build a StorageReference for a generic file without reading data."""
        return StorageReference(
            backend="filesystem",
            path=str(Path(path)),
            format=Path(path).suffix.lstrip("."),
        )


def _guess_mime(path: Path) -> str:
    """Guess MIME type from file extension."""
    mapping = {
        ".csv": "text/csv",
        ".json": "application/json",
        ".txt": "text/plain",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tif": "image/tiff",
        ".tiff": "image/tiff",
        ".pdf": "application/pdf",
        ".bin": "application/octet-stream",
        ".dat": "application/octet-stream",
    }
    return mapping.get(path.suffix.lower(), "application/octet-stream")
