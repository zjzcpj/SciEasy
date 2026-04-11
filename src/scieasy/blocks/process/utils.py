"""Process block utilities — shared helpers for process builtins."""

from __future__ import annotations

from typing import Any

import pyarrow as pa

from scieasy.core.types.dataframe import DataFrame


def to_arrow(obj: Any) -> pa.Table:
    """Extract an Arrow Table from a DataFrame or raw Table.

    ADR-031 D2: ViewProxy is eliminated; DataFrames are always storage-backed.
    """
    if isinstance(obj, pa.Table):
        return obj
    if isinstance(obj, DataFrame):
        return obj.get_in_memory_data()
    raise TypeError(f"Cannot extract Arrow Table from {type(obj).__name__}")
