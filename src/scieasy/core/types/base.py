"""DataObject ABC, TypeSignature, and metadata containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from scieasy.core.storage.ref import StorageReference

if TYPE_CHECKING:
    from scieasy.core.proxy import ViewProxy


@dataclass
class TypeSignature:
    """Describes the semantic type of a DataObject via a chain of type names.

    Attributes:
        type_chain: Ordered list of type names from most general to most specific,
            e.g. ``["DataObject", "Array", "Image"]``.
        slot_schema: Optional mapping of slot names to type names (for composites).
    """

    type_chain: list[str]
    slot_schema: dict[str, str] | None = field(default=None)

    def matches(self, other: TypeSignature) -> bool:
        """Return ``True`` if *other* is compatible with this signature.

        Compatibility means that *other*'s type chain is a prefix of or equal
        to this signature's type chain (i.e. this type is a subtype of other).
        For composite types, slot schemas must also be compatible.
        """
        if len(other.type_chain) > len(self.type_chain):
            return False
        if self.type_chain[: len(other.type_chain)] != other.type_chain:
            return False
        # Slot schema comparison for composites
        if other.slot_schema is not None:
            if self.slot_schema is None:
                return False
            for slot_name, expected_type in other.slot_schema.items():
                if slot_name not in self.slot_schema:
                    return False
                if self.slot_schema[slot_name] != expected_type:
                    return False
        return True

    @classmethod
    def from_type(cls, data_type: type) -> TypeSignature:
        """Build a :class:`TypeSignature` from a Python class's MRO.

        This walks the MRO up to (but not including) ``object`` and records
        the class names, filtered to only include ``DataObject`` and its
        subclasses.
        """
        chain: list[str] = []
        for klass in reversed(data_type.__mro__):
            if klass is object:
                continue
            # Only include DataObject and its subclasses in the chain.
            if klass.__name__ == "DataObject" or (isinstance(klass, type) and issubclass(klass, DataObject)):
                chain.append(klass.__name__)

        slot_schema: dict[str, str] | None = None
        if hasattr(data_type, "expected_slots") and data_type.expected_slots:
            slot_schema = {name: t.__name__ for name, t in data_type.expected_slots.items()}

        return cls(type_chain=chain, slot_schema=slot_schema)


class DataObject:
    """Base class for all first-class data objects in SciEasy.

    Subclasses represent concrete scientific data kinds (arrays, series,
    dataframes, text, artifacts, composites).

    ADR-017: ``metadata`` must be JSON-serializable for subprocess transport.
    Non-serializable values (numpy arrays, custom objects, lambdas) raise
    ``TypeError`` at construction time.
    """

    def __init__(
        self,
        metadata: dict[str, Any] | None = None,
        storage_ref: StorageReference | None = None,
    ) -> None:
        self._metadata: dict[str, Any] = metadata or {}
        self._validate_metadata(self._metadata)
        self._storage_ref: StorageReference | None = storage_ref

    @staticmethod
    def _validate_metadata(metadata: dict[str, Any]) -> None:
        """Validate that *metadata* is JSON-serializable (ADR-017)."""
        import json

        try:
            json.dumps(metadata)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"DataObject metadata must be JSON-serializable: {exc}") from exc

    # -- properties ----------------------------------------------------------

    @property
    def metadata(self) -> dict[str, Any]:
        """Return the metadata dict."""
        return self._metadata

    @property
    def dtype_info(self) -> TypeSignature:
        """Return the :class:`TypeSignature` describing this object's type."""
        return TypeSignature.from_type(type(self))

    @property
    def storage_ref(self) -> StorageReference | None:
        """Return the :class:`StorageReference` if the object is persisted."""
        return self._storage_ref

    @storage_ref.setter
    def storage_ref(self, ref: StorageReference | None) -> None:
        """Set the storage reference."""
        self._storage_ref = ref

    # -- data access ---------------------------------------------------------

    def view(self) -> ViewProxy:
        """Return a lazy :class:`ViewProxy` for this object's data."""
        from scieasy.core.proxy import ViewProxy

        if self._storage_ref is None:
            raise ValueError("Cannot create ViewProxy without a storage reference.")
        return ViewProxy(storage_ref=self._storage_ref, dtype_info=self.dtype_info)

    def to_memory(self) -> Any:
        """Materialise the full data into an in-memory representation."""
        return self.view().to_memory()

    def save(self, path: str | Path) -> None:
        """Persist the data object to *path*."""
        raise NotImplementedError
