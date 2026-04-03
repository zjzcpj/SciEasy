"""TypeRegistry — discovers and manages DataObject types from plugins and drop-in files."""

from __future__ import annotations


class TypeRegistry:
    """Registry of known :class:`DataObject` subclasses.

    Provides registration, lookup by name, and enumeration.
    """

    def __init__(self) -> None:
        self._registry: dict[str, type] = {}

    def register(self, name: str, data_type: type) -> None:
        """Register *data_type* under *name*."""
        raise NotImplementedError

    def resolve(self, name: str) -> type:
        """Return the type registered under *name*, or raise :class:`KeyError`."""
        raise NotImplementedError

    def all_types(self) -> dict[str, type]:
        """Return a copy of the full registry mapping."""
        raise NotImplementedError
