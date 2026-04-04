"""Format adapter: FCS (Flow Cytometry Standard) files (stub)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scieasy.core.storage.ref import StorageReference


class FCSAdapter:
    """Format adapter for FCS flow cytometry files.

    Not yet implemented.  Planned to use fcsparser or FlowIO for parsing.
    """

    def read(self, path: str | Path, **kwargs: Any) -> Any:
        raise NotImplementedError("FCSAdapter is not yet implemented. Planned for Phase 10 with fcsparser backend.")

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        raise NotImplementedError("FCSAdapter write is not yet implemented.")

    def supported_extensions(self) -> list[str]:
        return [".fcs"]

    def create_reference(self, path: str | Path) -> StorageReference:
        """Build a StorageReference pointing to the file without reading contents (ADR-020-Add2)."""
        return StorageReference(backend="filesystem", path=str(Path(path).resolve()), format="fcs")
