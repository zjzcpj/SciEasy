"""Tests for ProcessBlock — merge two DataFrames, split operations."""

from __future__ import annotations

import pyarrow as pa
import pytest

from scieasy.blocks.base.state import BlockState
from scieasy.blocks.process.builtins.merge import MergeBlock
from scieasy.blocks.process.builtins.split import SplitBlock
from scieasy.core.types.collection import Collection
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

        merged_col = result["merged"]
        assert isinstance(merged_col, Collection)
        merged = merged_col[0]
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

        out_col = result["out"]
        assert isinstance(out_col, Collection)
        assert out_col[0].row_count == 3

    def test_ratio_mode(self) -> None:
        data = _make_df({"val": list(range(10))})
        block = SplitBlock(config={"params": {"mode": "ratio", "ratio": 0.7}})
        block.transition(BlockState.READY)
        result = block.run({"data": data}, block.config)

        assert result["out"][0].row_count == 7
        assert result["remainder"][0].row_count == 3

    def test_filter_mode(self) -> None:
        data = _make_df({"name": ["alice", "bob", "alice"], "score": [10, 20, 30]})
        block = SplitBlock(config={"params": {"mode": "filter", "column": "name", "value": "alice"}})
        block.transition(BlockState.READY)
        result = block.run({"data": data}, block.config)

        out_col = result["out"]
        assert out_col[0].row_count == 2

    def test_unknown_mode_raises(self) -> None:
        data = _make_df({"x": [1]})
        block = SplitBlock(config={"params": {"mode": "unknown"}})
        block.transition(BlockState.READY)
        with pytest.raises(ValueError, match="Unknown split mode"):
            block.run({"data": data}, block.config)


class TestMergeBlockCollection:
    """ADR-020: MergeBlock with Collection-wrapped inputs."""

    def test_concat_collection_inputs(self) -> None:
        """MergeBlock should unpack Collection inputs and pack output."""
        from scieasy.core.types.collection import Collection

        left = _make_df({"a": [1, 2], "b": [3, 4]})
        right = _make_df({"a": [5, 6], "b": [7, 8]})

        left_col = Collection([left], item_type=DataFrame)
        right_col = Collection([right], item_type=DataFrame)

        block = MergeBlock(config={"params": {"how": "concat"}})
        block.transition(BlockState.READY)
        result = block.run({"left": left_col, "right": right_col}, block.config)

        merged_col = result["merged"]
        assert isinstance(merged_col, Collection)
        assert merged_col[0].row_count == 4

    def test_mixed_raw_and_collection(self) -> None:
        """MergeBlock should handle mix of raw and Collection inputs."""
        from scieasy.core.types.collection import Collection

        left = _make_df({"x": [1]})
        right_col = Collection([_make_df({"x": [2]})], item_type=DataFrame)

        block = MergeBlock(config={"params": {"how": "concat"}})
        block.transition(BlockState.READY)
        result = block.run({"left": left, "right": right_col}, block.config)

        assert result["merged"][0].row_count == 2


class TestSplitBlockCollection:
    """ADR-020: SplitBlock with Collection-wrapped inputs."""

    def test_head_collection_input(self) -> None:
        from scieasy.core.types.collection import Collection

        data = _make_df({"val": list(range(10))})
        data_col = Collection([data], item_type=DataFrame)

        block = SplitBlock(config={"params": {"mode": "head", "n": 3}})
        block.transition(BlockState.READY)
        result = block.run({"data": data_col}, block.config)

        out_col = result["out"]
        assert isinstance(out_col, Collection)
        assert out_col[0].row_count == 3

    def test_ratio_collection_input(self) -> None:
        from scieasy.core.types.collection import Collection

        data = _make_df({"val": list(range(10))})
        data_col = Collection([data], item_type=DataFrame)

        block = SplitBlock(config={"params": {"mode": "ratio", "ratio": 0.5}})
        block.transition(BlockState.READY)
        result = block.run({"data": data_col}, block.config)

        assert result["out"][0].row_count == 5
        assert result["remainder"][0].row_count == 5
