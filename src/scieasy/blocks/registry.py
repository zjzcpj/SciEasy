"""BlockRegistry — discovers blocks from drop-in files and entry_points."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BlockSpec:
    """Metadata descriptor for a registered block type."""

    name: str
    description: str = ""
    version: str = "0.1.0"
    block_class: type = object  # type: ignore[assignment]
    category: str = ""
    input_ports: list[Any] = field(default_factory=list)
    output_ports: list[Any] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    source: str = ""


class BlockRegistry:
    """Central catalogue of available block types.

    The registry is populated via :meth:`scan` (entry-points / drop-in
    directories) and queried by the runtime when constructing workflows.
    """

    def __init__(self) -> None:
        self._registry: dict[str, BlockSpec] = {}

    def scan(self) -> None:
        """Discover block classes from entry-points and drop-in directories."""
        raise NotImplementedError

    def instantiate(self, name: str, config: dict[str, Any] | None = None) -> Any:
        """Create a block instance by registered *name*."""
        raise NotImplementedError

    def hot_reload(self) -> None:
        """Re-scan for blocks that may have been added at runtime."""
        raise NotImplementedError

    def all_specs(self) -> dict[str, BlockSpec]:
        """Return a copy of the full registry mapping."""
        raise NotImplementedError
