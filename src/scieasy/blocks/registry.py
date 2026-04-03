"""BlockRegistry — discovers blocks from drop-in files and entry_points.

Per ADR-009, the registry stores :class:`BlockSpec` descriptors (module path,
class name, metadata, file mtime) — never the class object itself.  This
ensures hot-reload safety: a reload updates specs without affecting running
workflow instances.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BlockSpec:
    """Metadata descriptor for a registered block type.

    Stores the *location* of the block class (module path + class name)
    rather than holding a reference to the class object.  See ADR-009.
    """

    name: str
    description: str = ""
    version: str = "0.1.0"
    module_path: str = ""
    class_name: str = ""
    file_path: str | None = None
    file_mtime: float | None = None
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
