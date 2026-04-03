"""TypeRegistry — discovers and manages DataObject types from plugins and drop-in files.

Per ADR-009, the registry stores :class:`TypeSpec` descriptors (module path,
class name, base type) — never the class object itself.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TypeSpec:
    """Metadata descriptor for a registered DataObject subtype.

    Stores the *location* of the type class (module path + class name)
    rather than holding a reference to the class object.  See ADR-009.
    """

    name: str
    module_path: str = ""
    class_name: str = ""
    base_type: str = ""
    description: str = ""


class TypeRegistry:
    """Registry of known :class:`DataObject` subclasses.

    Provides registration, lookup by name, and enumeration.
    """

    def __init__(self) -> None:
        self._registry: dict[str, TypeSpec] = {}

    def register(self, name: str, spec: TypeSpec) -> None:
        """Register *spec* under *name*."""
        raise NotImplementedError

    def resolve(self, name: str) -> TypeSpec:
        """Return the spec registered under *name*, or raise :class:`KeyError`."""
        raise NotImplementedError

    def all_types(self) -> dict[str, TypeSpec]:
        """Return a copy of the full registry mapping."""
        raise NotImplementedError
