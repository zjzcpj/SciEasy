"""Tests for process block utilities — to_arrow()."""

from __future__ import annotations

from unittest.mock import MagicMock

import pyarrow as pa
import pytest

from scieasy.blocks.process.utils import to_arrow
from scieasy.core.types.dataframe import DataFrame


class TestToArrow:
    """to_arrow — extract Arrow Table from various input types."""

    def test_from_arrow_table_passthrough(self) -> None:
        table = pa.table({"a": [1, 2, 3]})
        result = to_arrow(table)
        assert result is table

    def test_from_dataframe_with_arrow_table(self) -> None:
        table = pa.table({"x": [10, 20]})
        df = DataFrame(columns=["x"], row_count=2)
        df._arrow_table = table  # type: ignore[attr-defined]
        result = to_arrow(df)
        assert result is table

    def test_from_viewproxy(self) -> None:
        from scieasy.core.proxy import ViewProxy

        table = pa.table({"col": [1]})
        proxy = MagicMock(spec=ViewProxy)
        proxy.to_memory.return_value = table
        result = to_arrow(proxy)
        assert result is table
        proxy.to_memory.assert_called_once()

    def test_unsupported_type_raises(self) -> None:
        with pytest.raises(TypeError, match="Cannot extract Arrow Table"):
            to_arrow("not a table")
