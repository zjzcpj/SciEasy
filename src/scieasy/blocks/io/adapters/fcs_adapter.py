"""Format adapter: FCS (Flow Cytometry Standard) files (stub)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


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
