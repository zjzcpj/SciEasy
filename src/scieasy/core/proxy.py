"""ViewProxy — lazy-loading accessor injected into block run() inputs."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.base import TypeSignature


class ViewProxy:
    """Lazy accessor that wraps a :class:`StorageReference` and defers I/O.

    Blocks receive ``ViewProxy`` instances as inputs so that data is only
    materialised when explicitly requested.

    Attributes:
        storage_ref: The underlying storage reference.
        dtype_info: The type signature of the wrapped data object.
    """

    def __init__(
        self,
        storage_ref: StorageReference,
        dtype_info: TypeSignature,
    ) -> None:
        self._storage_ref = storage_ref
        self._dtype_info = dtype_info

    # -- properties ----------------------------------------------------------

    @property
    def shape(self) -> tuple[int, ...] | None:
        """Return the shape of the underlying data, if applicable."""
        raise NotImplementedError

    @property
    def axes(self) -> list[str] | None:
        """Return the axis labels of the underlying data, if applicable."""
        raise NotImplementedError

    # -- data access ---------------------------------------------------------

    def slice(self, *args: Any) -> Any:
        """Return a sub-selection of the data without full materialisation."""
        raise NotImplementedError

    def to_memory(self) -> Any:
        """Materialise the full data into memory."""
        raise NotImplementedError

    def iter_chunks(self, chunk_size: int) -> Iterator[Any]:
        """Yield successive chunks of the data."""
        raise NotImplementedError
