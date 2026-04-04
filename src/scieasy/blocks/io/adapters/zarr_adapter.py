"""Format adapter: Zarr arrays."""

from __future__ import annotations

from pathlib import Path

from scieasy.core.storage.ref import StorageReference


class ZarrAdapter:
    """Format adapter for Zarr arrays.

    Provides create_reference() for lazy Collection construction.
    Full read() / write() are TODO -- Zarr data is currently
    handled by ZarrBackend directly.
    """

    def read(self, path: str | Path, **kwargs: object) -> object:
        """Read a Zarr array from *path*."""
        raise NotImplementedError(
            "ZarrAdapter.read() is not yet implemented -- use ZarrBackend directly."
        )

    def write(self, data: object, path: str | Path, **kwargs: object) -> Path:
        """Write data to a Zarr store at *path*."""
        raise NotImplementedError(
            "ZarrAdapter.write() is not yet implemented -- use ZarrBackend directly."
        )

    def supported_extensions(self) -> list[str]:
        """Return the list of file extensions this adapter handles."""
        return [".zarr"]

    def create_reference(self, path: str | Path) -> StorageReference:
        """Build a StorageReference for a Zarr store without reading data."""
        return StorageReference(backend="zarr", path=str(Path(path)), format="zarr")
