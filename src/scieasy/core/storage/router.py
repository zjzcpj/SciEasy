"""BackendRouter — DataObject type to StorageBackend automatic routing.

ADR-020 Addendum 5: _auto_flush needs to select the correct StorageBackend
based on the DataObject type.  BackendRouter provides a single entry point
for this mapping.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scieasy.core.storage.ref import StorageReference


class BackendRouter:
    """Route DataObject instances to the appropriate StorageBackend.

    Uses ``isinstance``-based type matching with ordered rules so that
    more-specific types (e.g. ``Image``) are matched by their base type's
    route (e.g. ``Array`` → ``ZarrBackend``).

    Default routes (checked in order):

    ============== ==================
    DataObject     StorageBackend
    ============== ==================
    CompositeData  CompositeStore
    Array          ZarrBackend
    DataFrame      ArrowBackend
    Text           FilesystemBackend
    Artifact       FilesystemBackend
    ============== ==================
    """

    def __init__(self) -> None:
        self._routes: list[tuple[type, type]] = self._default_routes()

    @staticmethod
    def _default_routes() -> list[tuple[type, type]]:
        """Return the default DataObject→Backend mapping."""
        from scieasy.core.storage.arrow_backend import ArrowBackend
        from scieasy.core.storage.composite_store import CompositeStore
        from scieasy.core.storage.filesystem import FilesystemBackend
        from scieasy.core.storage.zarr_backend import ZarrBackend
        from scieasy.core.types.array import Array
        from scieasy.core.types.artifact import Artifact
        from scieasy.core.types.composite import CompositeData
        from scieasy.core.types.dataframe import DataFrame
        from scieasy.core.types.text import Text

        return [
            (CompositeData, CompositeStore),
            (Array, ZarrBackend),
            (DataFrame, ArrowBackend),
            (Text, FilesystemBackend),
            (Artifact, FilesystemBackend),
        ]

    def get_backend(self, obj: Any) -> Any:
        """Return a StorageBackend instance for the given DataObject."""
        for data_type, backend_cls in self._routes:
            if isinstance(obj, data_type):
                return backend_cls()
        raise TypeError(f"No backend registered for {type(obj).__name__}")

    def get_backend_name(self, obj: Any) -> str:
        """Return the backend identifier string for the given DataObject."""
        from scieasy.core.storage.arrow_backend import ArrowBackend
        from scieasy.core.storage.composite_store import CompositeStore
        from scieasy.core.storage.filesystem import FilesystemBackend
        from scieasy.core.storage.zarr_backend import ZarrBackend

        _name_map = {
            ZarrBackend: "zarr",
            ArrowBackend: "arrow",
            FilesystemBackend: "filesystem",
            CompositeStore: "composite",
        }
        backend = self.get_backend(obj)
        return _name_map.get(type(backend), type(backend).__name__.lower())

    def register(self, data_type: type, backend_cls: type) -> None:
        """Register a custom type→backend mapping (prepended for priority)."""
        self._routes.insert(0, (data_type, backend_cls))

    def write(self, obj: Any, output_dir: str | Path) -> StorageReference:
        """Write a DataObject to *output_dir* using the appropriate backend.

        Constructs a StorageReference with a generated filename and delegates
        to the backend's ``write_from_memory`` method.
        """
        backend = self.get_backend(obj)
        backend_name = self.get_backend_name(obj)
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)

        # Determine file extension based on backend.
        ext_map = {"zarr": ".zarr", "arrow": ".parquet", "filesystem": "", "composite": ""}
        ext = ext_map.get(backend_name, "")
        target = str(path / f"data{ext}")

        ref = StorageReference(backend=backend_name, path=target)
        return backend.write(obj, ref)
