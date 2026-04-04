"""Format adapter: H5AD (AnnData) files (stub)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scieasy.core.storage.ref import StorageReference


class H5ADAdapter:
    """Format adapter for H5AD (AnnData) files.

    Not yet implemented.  Planned to use anndata/h5py for reading/writing.
    """

    def read(self, path: str | Path, **kwargs: Any) -> Any:
        raise NotImplementedError("H5ADAdapter is not yet implemented. Planned for Phase 10 with anndata backend.")

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        raise NotImplementedError("H5ADAdapter write is not yet implemented.")

    def supported_extensions(self) -> list[str]:
        return [".h5ad"]

    def create_reference(self, path: str | Path) -> StorageReference:
        """Build a StorageReference pointing to the file without reading contents (ADR-020-Add2)."""
        return StorageReference(backend="filesystem", path=str(Path(path).resolve()), format="h5ad")
