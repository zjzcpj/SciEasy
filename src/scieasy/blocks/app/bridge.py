"""ExternalAppBridge protocol — serialise, launch, watch, collect."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ExternalAppBridge(Protocol):
    """Structural protocol for bridging external GUI applications.

    The lifecycle is: prepare -> launch -> watch -> collect.
    """

    def prepare(self, inputs: dict[str, Any], exchange_dir: Path) -> None:
        """Serialise *inputs* into *exchange_dir* for the external app."""
        ...

    def launch(self, command: str, exchange_dir: Path) -> Any:
        """Launch the external application with *command*."""
        ...

    def watch(self, exchange_dir: Path, patterns: list[str]) -> list[Path]:
        """Watch *exchange_dir* for output files matching *patterns*."""
        ...

    def collect(self, output_files: list[Path]) -> dict[str, Any]:
        """Collect results from *output_files* into a typed output mapping."""
        ...
