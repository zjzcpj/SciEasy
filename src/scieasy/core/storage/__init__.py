"""Storage backends — per-type persistence (Zarr, Arrow, filesystem)."""

from __future__ import annotations

from scieasy.core.storage.arrow_backend import ArrowBackend
from scieasy.core.storage.backend_router import BackendRouter, get_router
from scieasy.core.storage.base import StorageBackend
from scieasy.core.storage.composite_store import CompositeStore
from scieasy.core.storage.filesystem import FilesystemBackend
from scieasy.core.storage.ref import StorageReference
from scieasy.core.storage.zarr_backend import ZarrBackend

__all__ = [
    "ArrowBackend",
    "BackendRouter",
    "CompositeStore",
    "FilesystemBackend",
    "StorageBackend",
    "StorageReference",
    "ZarrBackend",
    "get_router",
]
