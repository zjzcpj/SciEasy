"""Tests for process block utilities — to_arrow()."""

from __future__ import annotations

import pyarrow as pa
import pytest

from scieasy.blocks.process.utils import to_arrow
from scieasy.core.types.dataframe import DataFrame


class TestToArrow:
    """to_arrow — extract Arrow Table from various input types (ADR-031 D2)."""

    def test_from_arrow_table_passthrough(self) -> None:
        table = pa.table({"a": [1, 2, 3]})
        result = to_arrow(table)
        assert result is table

    def test_from_storage_backed_dataframe(self, tmp_path: object) -> None:
        """DataFrame with storage_ref returns Arrow Table via get_in_memory_data."""
        from scieasy.core.storage.arrow_backend import ArrowBackend
        from scieasy.core.storage.ref import StorageReference

        table = pa.table({"x": [10, 20]})
        ref = StorageReference(backend="arrow", path=str(tmp_path) + "/test.parquet")
        ref = ArrowBackend().write(table, ref)
        df = DataFrame(columns=["x"], row_count=2, storage_ref=ref)
        result = to_arrow(df)
        assert result.column_names == ["x"]
        assert result.num_rows == 2

    def test_unsupported_type_raises(self) -> None:
        with pytest.raises(TypeError, match="Cannot extract Arrow Table"):
            to_arrow("not a table")
