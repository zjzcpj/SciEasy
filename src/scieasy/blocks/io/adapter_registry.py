"""AdapterRegistry -- maps file extensions to FormatAdapter classes."""

from __future__ import annotations

import importlib.metadata
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Extensions owned by the core package.  External adapters registered via
# entry-points are **not** allowed to override these -- see ADR-025 Section 6.
BUILTIN_EXTENSIONS: frozenset[str] = frozenset({".csv", ".parquet", ".tiff", ".tif", ".zarr", ".json", ".npy", ".npz"})


class AdapterRegistry:
    """Registry that maps file extensions to FormatAdapter classes."""

    def __init__(self) -> None:
        self._adapters: dict[str, type] = {}

    def register(self, adapter_class: type, extensions: list[str] | None = None) -> None:
        """Register *adapter_class* for the given *extensions*."""
        if extensions is None:
            instance = adapter_class()
            extensions = instance.supported_extensions()
        for ext in extensions:
            key = self._normalise(ext)
            self._adapters[key] = adapter_class

    def get_for_extension(self, extension: str) -> type:
        """Return the adapter class registered for *extension*."""
        key = self._normalise(extension)
        if key not in self._adapters:
            raise KeyError(f"No adapter registered for extension \x27{extension}\x27")
        return self._adapters[key]

    def all_adapters(self) -> dict[str, type]:
        """Return a copy of the full extension-to-adapter mapping."""
        return dict(self._adapters)

    def register_defaults(self) -> None:
        """Register all built-in format adapters shipped with SciEasy."""
        from scieasy.blocks.io.adapters.csv_adapter import CSVAdapter
        from scieasy.blocks.io.adapters.generic_adapter import GenericAdapter
        from scieasy.blocks.io.adapters.parquet_adapter import ParquetAdapter
        from scieasy.blocks.io.adapters.tiff_adapter import TIFFAdapter
        from scieasy.blocks.io.adapters.zarr_adapter import ZarrAdapter

        self.register(CSVAdapter)
        self.register(TIFFAdapter)
        self.register(ParquetAdapter)
        self.register(ZarrAdapter)
        self.register(GenericAdapter)

    def scan_entry_points(self) -> None:
        """Discover adapters from ``scieasy.adapters`` entry-points.

        External adapters whose extensions collide with
        :data:`BUILTIN_EXTENSIONS` are **skipped** with a warning so that
        core format handling cannot be silently overridden by third-party
        packages.
        """
        try:
            eps = importlib.metadata.entry_points()
        except Exception:
            logger.warning("Failed to read entry-points", exc_info=True)
            return

        adapter_eps: Any = (
            eps.select(group="scieasy.adapters") if hasattr(eps, "select") else eps.get("scieasy.adapters", [])
        )

        for ep in adapter_eps:
            try:
                cls = ep.load()
            except Exception:
                logger.warning(
                    "Failed to load adapter entry-point '%s'",
                    ep.name,
                    exc_info=True,
                )
                continue

            self._register_external(cls, ep.name)

    def _register_external(self, adapter_class: type, ep_name: str) -> None:
        """Register an external adapter, skipping built-in extensions."""
        instance = adapter_class()
        extensions = instance.supported_extensions()

        for ext in extensions:
            key = self._normalise(ext)
            if key in BUILTIN_EXTENSIONS:
                logger.warning(
                    "External adapter '%s' tried to override built-in extension '%s' -- skipped",
                    ep_name,
                    key,
                )
                continue
            self._adapters[key] = adapter_class
            logger.info(
                "Registered external adapter '%s' for '%s'",
                ep_name,
                key,
            )

    @staticmethod
    def _normalise(ext: str) -> str:
        """Normalise an extension to lower-case with a leading dot."""
        ext = ext.lower().strip()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext
