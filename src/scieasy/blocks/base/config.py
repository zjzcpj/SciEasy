"""BlockConfig — validated parameter container (Pydantic)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class BlockConfig(BaseModel):
    """Configuration container for a block instance.

    Uses Pydantic's ``extra="allow"`` so that subclasses and plugins can
    attach arbitrary validated fields without modifying this base class.
    """

    model_config = ConfigDict(extra="allow")

    params: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Return a parameter value by *key*, falling back to *default*."""
        return self.params.get(key, default)
