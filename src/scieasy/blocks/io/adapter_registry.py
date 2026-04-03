"""AdapterRegistry — maps file extensions to FormatAdapter classes."""

from __future__ import annotations

from typing import Any


class AdapterRegistry:
    """Registry that maps file extensions to :class:`FormatAdapter` classes.

    Extensions are normalised to lower-case with a leading dot
    (e.g. ``".csv"``).
    """

    def __init__(self) -> None:
        self._adapters: dict[str, type] = {}

    def register(self, adapter_class: type, extensions: list[str] | None = None) -> None:
        """Register *adapter_class* for the given *extensions*."""
        raise NotImplementedError

    def get_for_extension(self, extension: str) -> Any:
        """Return the adapter class registered for *extension*."""
        raise NotImplementedError

    def all_adapters(self) -> dict[str, type]:
        """Return a copy of the full extension-to-adapter mapping."""
        raise NotImplementedError
