"""Format adapter: mzxml_adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class MzXMLAdapter:
    """Format adapter for mzXML mass-spectrometry files."""

    def read(self, path: str | Path, **kwargs: Any) -> Any:
        raise NotImplementedError

    def write(self, data: Any, path: str | Path, **kwargs: Any) -> Path:
        raise NotImplementedError

    def supported_extensions(self) -> list[str]:
        raise NotImplementedError
