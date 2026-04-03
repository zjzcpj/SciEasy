"""Tests for IOBlock — load CSV -> DataFrame, save DataFrame -> Parquet."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pytest

from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.dataframe import DataFrame


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    """Create a temporary CSV file."""
    path = tmp_path / "test.csv"
    path.write_text("name,value,score\nalice,10,0.5\nbob,20,0.8\ncarol,30,0.9\n")
    return path


@pytest.fixture
def parquet_file(tmp_path: Path) -> Path:
    """Create a temporary Parquet file."""
    path = tmp_path / "test.parquet"
    table = pa.table({"x": [1, 2, 3], "y": [4, 5, 6]})
    import pyarrow.parquet as pq

    pq.write_table(table, str(path))
    return path


class TestIOBlockInput:
    """IOBlock in input (read) mode."""

    def test_load_csv(self, csv_file: Path) -> None:
        block = IOBlock(config={"params": {"path": str(csv_file)}})
        block.transition(block.state.READY)
        result = block.run({}, block.config)
        assert "data" in result
        df = result["data"]
        assert isinstance(df, DataFrame)
        assert df.columns == ["name", "value", "score"]
        assert df.row_count == 3

    def test_load_parquet(self, parquet_file: Path) -> None:
        block = IOBlock(config={"params": {"path": str(parquet_file)}})
        block.transition(block.state.READY)
        result = block.run({}, block.config)
        df = result["data"]
        assert isinstance(df, DataFrame)
        assert df.columns == ["x", "y"]
        assert df.row_count == 3

    def test_missing_path_raises(self) -> None:
        block = IOBlock(config={"params": {}})
        block.transition(block.state.READY)
        with pytest.raises(ValueError, match="path"):
            block.run({}, block.config)


class TestIOBlockOutput:
    """IOBlock in output (write) mode."""

    def test_save_as_csv(self, tmp_path: Path) -> None:
        out_path = tmp_path / "out.csv"
        table = pa.table({"a": [1, 2], "b": [3, 4]})
        df = DataFrame(columns=["a", "b"], row_count=2)
        df._arrow_table = table  # type: ignore[attr-defined]

        block = IOBlock(config={"params": {"path": str(out_path)}})
        block.direction = "output"
        block.transition(block.state.READY)
        block.run({"data": df}, block.config)
        assert out_path.exists()

    def test_save_as_parquet(self, tmp_path: Path) -> None:
        out_path = tmp_path / "out.parquet"
        table = pa.table({"x": [10, 20]})
        df = DataFrame(columns=["x"], row_count=2)
        df._arrow_table = table  # type: ignore[attr-defined]

        block = IOBlock(config={"params": {"path": str(out_path)}})
        block.direction = "output"
        block.transition(block.state.READY)
        block.run({"data": df}, block.config)
        assert out_path.exists()
