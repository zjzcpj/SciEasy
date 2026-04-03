"""AdapterRegistry — maps file extensions to FormatAdapter classes."""

from __future__ import annotations

import importlib.metadata
from typing import Any


class AdapterRegistry:
    """Registry that maps file extensions to :class:`FormatAdapter` classes.

    Extensions are normalised to lower-case with a leading dot
    (e.g. ``".csv"``).

    Supports two discovery mechanisms:
    - Manual registration via :meth:`register`.
    - Entry-point scan via ``scieasy.adapters`` group.
    """

    def __init__(self) -> None:
        self._adapters: dict[str, type] = {}

    def register(self, adapter_class: type, extensions: list[str] | None = None) -> None:
        """Register *adapter_class* for the given *extensions*.

        If *extensions* is ``None``, calls ``adapter_class().supported_extensions()``
        to discover them automatically.
        """
        if extensions is None:
            instance = adapter_class()
            extensions = instance.supported_extensions()
        for ext in extensions:
            key = self._normalise(ext)
            self._adapters[key] = adapter_class

    def get_for_extension(self, extension: str) -> type:
        """Return the adapter class registered for *extension*.

        Raises :class:`KeyError` if no adapter is registered.
        """
        key = self._normalise(extension)
        if key not in self._adapters:
            raise KeyError(f"No adapter registered for extension '{extension}'")
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

        self.register(CSVAdapter)
        self.register(TIFFAdapter)
        self.register(ParquetAdapter)
        self.register(GenericAdapter)

    def scan_entry_points(self) -> None:
        """Discover adapters from ``scieasy.adapters`` entry-points."""
        try:
            eps = importlib.metadata.entry_points()
        except Exception:
            return

        adapter_eps = eps.select(group="scieasy.adapters") if hasattr(eps, "select") else eps.get("scieasy.adapters", [])

        for ep in adapter_eps:
            try:
                cls = ep.load()
                self.register(cls)
            except Exception:
                continue

    @staticmethod
    def _normalise(ext: str) -> str:
        """Normalise an extension to lower-case with a leading dot."""
        ext = ext.lower().strip()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext
