"""FormatAdapter protocol — read file to DataObject, write DataObject to file."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


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
