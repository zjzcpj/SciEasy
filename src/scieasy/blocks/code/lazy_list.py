"""LazyList — memory-safe wrapper for Collection items in CodeBlock.

ADR-020-Add4: When CodeBlock auto-unpacks a Collection with length > 1,
it wraps the Collection in a LazyList instead of materializing all items.
"""

from __future__ import annotations

from typing import Any

# TODO(ADR-020-Add4): Implement LazyList class.
#
# Design:
#   - Wraps a Collection instance
#   - Looks like a Python list to user scripts
#   - Iteration loads 1 item at a time via ViewProxy (memory-safe)
#   - Indexing loads only the requested item
#   - len() returns length without loading data (no-op)
#   - Full materialization requires explicit .to_list() call
#
# Usage in CodeBlock auto-unpack:
#   Collection length=1 → single native object (numpy array, pandas DataFrame)
#   Collection length>1 → LazyList (this class)
#
# Memory guarantee:
#   for x in lazy_list:  # loads 1 item at a time, O(1) memory
#       process(x)
#
#   lazy_list[5]  # loads only item 5
#
#   all_items = lazy_list.to_list()  # explicit full materialization (user's choice)


class LazyList:
    """Memory-safe list-like wrapper for Collection items."""

    def __init__(self, collection: Any) -> None:
        # TODO(ADR-020-Add4): Store Collection reference, do NOT load items.
        raise NotImplementedError

    def __iter__(self) -> Any:
        # TODO(ADR-020-Add4): Yield items one at a time via ViewProxy.
        # Each item loaded on demand, previous item eligible for GC.
        raise NotImplementedError

    def __getitem__(self, index: int) -> Any:
        # TODO(ADR-020-Add4): Load only the requested item.
        raise NotImplementedError

    def __len__(self) -> int:
        # TODO(ADR-020-Add4): Return Collection length without loading data.
        raise NotImplementedError

    def to_list(self) -> list[Any]:
        """Explicitly materialize all items into memory."""
        # TODO(ADR-020-Add4): Load all items. Warn if total size > threshold.
        raise NotImplementedError
