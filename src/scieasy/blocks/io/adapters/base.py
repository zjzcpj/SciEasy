"""FormatAdapter protocol -- read file to DataObject, write DataObject to file."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from scieasy.core.storage.ref import StorageReference


@runtime_checkable
class FormatAdapter(Protocol):
    """Structural protocol for pluggable file-format adapters.

    Implementations translate between on-disk file representations and
    in-memory data objects.
    """

    def read(self, path: str | Path, **kwargs: Any) -> Any:
        """Read data from *path* and return a typed data object."""
        ...

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        """Write *data* to *path* and return the resulting file path."""
        ...

    def supported_extensions(self) -> list[str]:
        """Return the list of file extensions this adapter handles."""
        ...

    def create_reference(self, path: str | Path) -> StorageReference:
        """Build a StorageReference pointing to *path* without reading data.

        This enables lazy Collection construction: IOBlock creates references
        for each file without loading contents into memory.  Actual data reading
        happens later when a downstream block calls ViewProxy.to_memory().
        """
        ...
