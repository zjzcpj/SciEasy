"""Collection — homogeneous ordered container of DataObjects for block-to-block transport.

ADR-020: Collection is NOT a DataObject subclass — it is a transport wrapper only.
Type identity determined by item_type (for port matching).
Engine never unpacks, iterates, or inspects Collection contents.
"""

from __future__ import annotations

from typing import Any

# TODO(ADR-020): Implement Collection class.
#
# Design constraints:
#   - NOT a DataObject subclass — transport wrapper only
#   - Homogeneous: all items must share the same base type
#   - item_type is immutable after construction
#   - length=0 is valid (empty Collection)
#   - Single item = Collection with length=1
#   - Type identity determined by item_type (for port matching)
#
# Fields:
#   _items: list[DataObject]
#   _item_type: type  — immutable after __init__
#
# Properties:
#   item_type -> type: read-only
#   length -> int: read-only (== len(_items))
#
# Protocols to implement:
#   __iter__: iterate over items
#   __len__: return length
#   __getitem__: index access
#   __class_getitem__: enable Collection[Image] syntax
#
# Methods:
#   storage_refs -> list[StorageReference]: extract refs from all items
#
# Invariants:
#   - All items same base type (enforced at construction)
#   - item_type immutable after init
#   - length=0 valid
#
# TODO(ADR-020-Add6): Empty Collection must specify item_type explicitly.
#   Collection(items=[], item_type=Image)  # valid
#   Collection(items=[])                    # raises ValueError
#
# TODO(ADR-020-Add6): Port validation checks Collection.item_type, not
#   Collection itself. Collection[DataFrame] rejected by accepted_types=[Image] port.


class Collection:
    """Homogeneous ordered collection of DataObjects for inter-block transport."""

    def __init__(self, items: list[Any], item_type: type | None = None) -> None:
        # TODO(ADR-020): Validate homogeneity — all items must be instances of item_type.
        # TODO(ADR-020-Add6): If items is empty, item_type must be explicitly provided.
        raise NotImplementedError

    @property
    def item_type(self) -> type:
        """Return the element type of this Collection (immutable)."""
        raise NotImplementedError

    @property
    def length(self) -> int:
        """Return the number of items in this Collection."""
        raise NotImplementedError

    def __iter__(self) -> Any:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __getitem__(self, index: int) -> Any:
        raise NotImplementedError

    def __class_getitem__(cls, item_type: type) -> Any:
        """Enable Collection[Image] syntax for type annotations."""
        # TODO(ADR-020): Return a parameterized alias or GenericAlias.
        raise NotImplementedError

    @property
    def storage_refs(self) -> list[Any]:
        """Extract StorageReference from each item."""
        # TODO(ADR-020): Return [item.storage_ref for item in self._items]
        raise NotImplementedError
