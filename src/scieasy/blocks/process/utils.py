"""Process block utilities — shared helpers for process builtins."""

from __future__ import annotations

from typing import Any

import pyarrow as pa

from scieasy.core.types.dataframe import DataFrame


def to_arrow(obj: Any) -> pa.Table:
    """Extract an Arrow Table from a DataFrame, ViewProxy, or raw Table."""
    from scieasy.core.proxy import ViewProxy

    if isinstance(obj, ViewProxy):
        obj = obj.to_memory()
    if isinstance(obj, pa.Table):
        return obj
    if isinstance(obj, DataFrame) and hasattr(obj, "_arrow_table"):
        return obj._arrow_table  # type: ignore[attr-defined]
    if isinstance(obj, DataFrame) and obj.storage_ref is not None:
        return obj.to_memory()
    raise TypeError(f"Cannot extract Arrow Table from {type(obj).__name__}")
