"""Format adapter: mzXML mass-spectrometry files (stub)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class MzXMLAdapter:
    """Format adapter for mzXML mass-spectrometry files.

    Not yet implemented.  Planned to use pyteomics or pyopenms for parsing.
    """

    def read(self, path: str | Path, **kwargs: Any) -> Any:
        raise NotImplementedError(
            "MzXMLAdapter is not yet implemented. Planned for Phase 10 with pyteomics or pyopenms backend."
        )

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        raise NotImplementedError("MzXMLAdapter write is not yet implemented.")

    def supported_extensions(self) -> list[str]:
        return [".mzxml", ".mzXML"]

# TODO(ADR-020-Add2): Implement create_reference(path) -> StorageReference.
# Build a StorageReference pointing to the file without reading its contents.
