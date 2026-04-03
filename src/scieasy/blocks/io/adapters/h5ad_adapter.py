"""Format adapter: H5AD (AnnData) files (stub)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class H5ADAdapter:
    """Format adapter for H5AD (AnnData) files.

    Not yet implemented.  Planned to use anndata/h5py for reading/writing.
    """

    def read(self, path: str | Path, **kwargs: Any) -> Any:
        raise NotImplementedError(
            "H5ADAdapter is not yet implemented. "
            "Planned for Phase 10 with anndata backend."
        )

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        raise NotImplementedError(
            "H5ADAdapter write is not yet implemented."
        )

    def supported_extensions(self) -> list[str]:
        return [".h5ad"]
