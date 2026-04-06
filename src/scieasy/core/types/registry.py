"""TypeRegistry — discovers and manages DataObject types from plugins and drop-in files.

Per ADR-009, the registry stores :class:`TypeSpec` descriptors (module path,
class name, base type) — never the class object itself.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


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
        """Register all built-in DataObject subclasses shipped with SciEasy.

        Per ADR-027 D2, the domain subtypes no longer live in core:

        - T-006 removed the Array family (``Image``, ``FluorImage``,
          ``MSImage``, ``SRSImage``) to ``scieasy-blocks-imaging``.
        - T-007 removed the remaining Series/DataFrame/Composite
          families (``Spectrum``, ``RamanSpectrum``, ``MassSpectrum``,
          ``PeakTable``, ``MetabPeakTable``, ``AnnData``,
          ``SpatialData``) to ``scieasy-blocks-spectral``,
          ``scieasy-blocks-singlecell``, and
          ``scieasy-blocks-spatial-omics`` respectively.

        The registry therefore no longer auto-registers any of them.
        They are re-registered via the ``scieasy.types`` entry-point
        mechanism when the plugin is installed (see
        :meth:`_scan_entrypoint_types`).
        """
        from scieasy.core.types.array import Array
        from scieasy.core.types.artifact import Artifact
        from scieasy.core.types.base import DataObject
        from scieasy.core.types.composite import CompositeData
        from scieasy.core.types.dataframe import DataFrame
        from scieasy.core.types.series import Series
        from scieasy.core.types.text import Text

        builtins: list[type] = [
            DataObject,
            Array,
            Series,
            DataFrame,
            Text,
            Artifact,
            CompositeData,
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

    def _scan_entrypoint_types(self) -> None:
        """Discover and register DataObject subtypes from ``scieasy.types`` entry-points.

        Each entry-point must be a callable that returns a list of type classes
        (subclasses of :class:`DataObject`).  Invalid entries are logged as
        warnings and skipped — they never crash the registry.

        See ADR-025 Section 4 for the protocol specification.
        """
        from scieasy.core.types.base import DataObject

        eps = importlib.metadata.entry_points(group="scieasy.types")
        for ep in eps:
            try:
                factory = ep.load()
            except Exception:
                logger.warning(
                    "Failed to load entry-point '%s' from group 'scieasy.types'",
                    ep.name,
                    exc_info=True,
                )
                continue

            try:
                type_classes = factory()
            except Exception:
                logger.warning(
                    "Entry-point '%s' callable raised an exception",
                    ep.name,
                    exc_info=True,
                )
                continue

            if not isinstance(type_classes, (list, tuple)):
                logger.warning(
                    "Entry-point '%s' returned %s instead of a list of type classes; skipping",
                    ep.name,
                    type(type_classes).__name__,
                )
                continue

            for cls in type_classes:
                if not isinstance(cls, type) or not issubclass(cls, DataObject):
                    logger.warning(
                        "Entry-point '%s' returned item %r which is not a DataObject subclass; skipping",
                        ep.name,
                        cls,
                    )
                    continue

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
                logger.info("Registered external type '%s' from entry-point '%s'", cls.__name__, ep.name)

    def scan_all(self) -> None:
        """Register built-in types and then scan entry-points for external types."""
        self.scan_builtins()
        self._scan_entrypoint_types()
