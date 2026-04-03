"""TypeRegistry — discovers and manages DataObject types from plugins and drop-in files.

Per ADR-009, the registry stores :class:`TypeSpec` descriptors (module path,
class name, base type) — never the class object itself.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any


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
    Supports isinstance-style matching via :meth:`is_instance`.
    """

    def __init__(self) -> None:
        self._registry: dict[str, TypeSpec] = {}

    def register(self, name: str, spec: TypeSpec) -> None:
        """Register *spec* under *name*."""
        self._registry[name] = spec

    def resolve(self, name: str) -> TypeSpec:
        """Return the spec registered under *name*, or raise :class:`KeyError`."""
        if name not in self._registry:
            raise KeyError(f"Type '{name}' is not registered.")
        return self._registry[name]

    def all_types(self) -> dict[str, TypeSpec]:
        """Return a copy of the full registry mapping."""
        return dict(self._registry)

    def load_class(self, name: str) -> type:
        """Import and return the class for the type registered under *name*."""
        spec = self.resolve(name)
        module = importlib.import_module(spec.module_path)
        return getattr(module, spec.class_name)  # type: ignore[no-any-return]

    def is_instance(self, obj: Any, type_name: str) -> bool:
        """Check if *obj* is an instance of the type registered under *type_name*.

        Uses isinstance-style matching that respects inheritance.
        """
        cls = self.load_class(type_name)
        return isinstance(obj, cls)

    def scan_builtins(self) -> None:
        """Register all built-in DataObject subclasses shipped with SciEasy."""
        from scieasy.core.types.array import Array, FluorImage, Image, MSImage, SRSImage
        from scieasy.core.types.artifact import Artifact
        from scieasy.core.types.base import DataObject
        from scieasy.core.types.composite import AnnData, CompositeData, SpatialData
        from scieasy.core.types.dataframe import DataFrame, MetabPeakTable, PeakTable
        from scieasy.core.types.series import MassSpectrum, RamanSpectrum, Series, Spectrum
        from scieasy.core.types.text import Text

        builtins: list[type] = [
            DataObject, Array, Image, MSImage, SRSImage, FluorImage,
            Series, Spectrum, RamanSpectrum, MassSpectrum,
            DataFrame, PeakTable, MetabPeakTable,
            Text, Artifact, CompositeData, AnnData, SpatialData,
        ]
        for cls in builtins:
            base = cls.__mro__[1].__name__ if len(cls.__mro__) > 2 else ""
            self.register(
                cls.__name__,
                TypeSpec(
                    name=cls.__name__,
                    module_path=cls.__module__,
                    class_name=cls.__name__,
                    base_type=base,
                    description=cls.__doc__.split("\n")[0] if cls.__doc__ else "",
                ),
            )
