"""Tests for ProcessBlock — merge two DataFrames, split operations."""

from __future__ import annotations

import pyarrow as pa
import pytest

from scieasy.blocks.base.state import BlockState
from scieasy.blocks.process.builtins.merge import MergeBlock
from scieasy.blocks.process.builtins.split import SplitBlock
from scieasy.core.types.dataframe import DataFrame


def _make_df(data: dict) -> DataFrame:
    """Helper: create a DataFrame with an Arrow table attached."""
    table = pa.table(data)
    df = DataFrame(columns=table.column_names, row_count=table.num_rows)
    df._arrow_table = table  # type: ignore[attr-defined]
    return df


class TestMergeBlock:
    """MergeBlock — concatenation of two DataFrames."""

    def test_concat_two_tables(self) -> None:
        left = _make_df({"a": [1, 2], "b": [3, 4]})
        right = _make_df({"a": [5, 6], "b": [7, 8]})

        block = MergeBlock(config={"params": {"how": "concat"}})
        block.transition(BlockState.READY)
        result = block.run({"left": left, "right": right}, block.config)

        merged = result["merged"]
        assert isinstance(merged, DataFrame)
        assert merged.row_count == 4
        assert merged.columns == ["a", "b"]
        assert block.state == BlockState.DONE

    def test_state_transitions(self) -> None:
        left = _make_df({"x": [1]})
        right = _make_df({"x": [2]})

        block = MergeBlock()
        block.transition(BlockState.READY)
        assert block.state == BlockState.READY

        block.run({"left": left, "right": right}, block.config)
        assert block.state == BlockState.DONE


class TestSplitBlock:
    """SplitBlock — head, ratio, filter modes."""

    def test_head_mode(self) -> None:
        data = _make_df({"val": list(range(10))})
        block = SplitBlock(config={"params": {"mode": "head", "n": 3}})
        block.transition(BlockState.READY)
        result = block.run({"data": data}, block.config)

        out = result["out"]
        assert isinstance(out, DataFrame)
        assert out.row_count == 3

    def test_ratio_mode(self) -> None:
        data = _make_df({"val": list(range(10))})
        block = SplitBlock(config={"params": {"mode": "ratio", "ratio": 0.7}})
        block.transition(BlockState.READY)
        result = block.run({"data": data}, block.config)

        assert result["out"].row_count == 7
        assert result["remainder"].row_count == 3

    def test_filter_mode(self) -> None:
        data = _make_df({"name": ["alice", "bob", "alice"], "score": [10, 20, 30]})
        block = SplitBlock(config={"params": {"mode": "filter", "column": "name", "value": "alice"}})
        block.transition(BlockState.READY)
        result = block.run({"data": data}, block.config)

        out = result["out"]
        assert out.row_count == 2

    def test_unknown_mode_raises(self) -> None:
        data = _make_df({"x": [1]})
        block = SplitBlock(config={"params": {"mode": "unknown"}})
        block.transition(BlockState.READY)
        with pytest.raises(ValueError, match="Unknown split mode"):
            block.run({"data": data}, block.config)
