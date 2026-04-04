"""Tests for IOBlock -- lazy Collection construction via create_reference."""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pytest

from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
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


class TestIOBlockInputLazy:
    """IOBlock in input mode -- produces a lazy Collection of StorageReferences."""

    def test_load_single_csv_produces_collection(self, csv_file: Path) -> None:
        block = IOBlock(config={"params": {"path": str(csv_file)}})
        block.transition(block.state.READY)
        result = block.run({}, block.config)
        assert "data" in result
        coll = result["data"]
        assert isinstance(coll, Collection)
        assert coll.length == 1
        # The item should have a StorageReference, not eagerly loaded data.
        item = coll[0]
        assert isinstance(item, DataObject)
        assert item.storage_ref is not None
        assert isinstance(item.storage_ref, StorageReference)
        assert item.storage_ref.format == "csv"
        assert item.storage_ref.backend == "arrow"

    def test_load_single_parquet_produces_collection(self, parquet_file: Path) -> None:
        block = IOBlock(config={"params": {"path": str(parquet_file)}})
        block.transition(block.state.READY)
        result = block.run({}, block.config)
        coll = result["data"]
        assert isinstance(coll, Collection)
        assert coll.length == 1
        item = coll[0]
        assert item.storage_ref is not None
        assert item.storage_ref.format == "parquet"
        assert item.storage_ref.backend == "arrow"

    def test_load_directory_produces_collection(self, tmp_path: Path) -> None:
        """A directory with multiple CSV files should produce a multi-item Collection."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        for name in ("a.csv", "b.csv", "c.csv"):
            (data_dir / name).write_text("x,y\n1,2\n")

        block = IOBlock(config={"params": {"path": str(data_dir)}})
        block.transition(block.state.READY)
        result = block.run({}, block.config)
        coll = result["data"]
        assert isinstance(coll, Collection)
        assert coll.length == 3
        for item in coll:
            assert item.storage_ref is not None
            assert item.storage_ref.format == "csv"

    def test_load_directory_skips_unknown_extensions(self, tmp_path: Path) -> None:
        """Files with unregistered extensions should be silently skipped."""
        data_dir = tmp_path / "mixed"
        data_dir.mkdir()
        (data_dir / "good.csv").write_text("x\n1\n")
        (data_dir / "skip.xyz").write_text("junk")

        block = IOBlock(config={"params": {"path": str(data_dir)}})
        block.transition(block.state.READY)
        result = block.run({}, block.config)
        coll = result["data"]
        assert coll.length == 1

    def test_load_empty_directory_raises(self, tmp_path: Path) -> None:
        """An empty directory should raise ValueError."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        block = IOBlock(config={"params": {"path": str(empty_dir)}})
        block.transition(block.state.READY)
        with pytest.raises(ValueError, match="No recognised files"):
            block.run({}, block.config)

    def test_missing_path_raises(self) -> None:
        block = IOBlock(config={"params": {}})
        block.transition(block.state.READY)
        with pytest.raises(ValueError, match="path"):
            block.run({}, block.config)


class TestIOBlockOutput:
    """IOBlock in output (write) mode."""

    def test_save_single_dataobject_as_csv(self, tmp_path: Path) -> None:
        out_path = tmp_path / "out.csv"
        table = pa.table({"a": [1, 2], "b": [3, 4]})
        df = DataFrame(columns=["a", "b"], row_count=2)
        df._arrow_table = table  # type: ignore[attr-defined]

        block = IOBlock(config={"params": {"path": str(out_path)}})
        block.direction = "output"
        block.transition(block.state.READY)
        block.run({"data": df}, block.config)
        assert out_path.exists()

    def test_save_single_dataobject_as_parquet(self, tmp_path: Path) -> None:
        out_path = tmp_path / "out.parquet"
        table = pa.table({"x": [10, 20]})
        df = DataFrame(columns=["x"], row_count=2)
        df._arrow_table = table  # type: ignore[attr-defined]

        block = IOBlock(config={"params": {"path": str(out_path)}})
        block.direction = "output"
        block.transition(block.state.READY)
        block.run({"data": df}, block.config)
        assert out_path.exists()

    def test_output_missing_data_raises(self) -> None:
        block = IOBlock(config={"params": {"path": "/tmp/out.csv"}})
        block.direction = "output"
        block.transition(block.state.READY)
        with pytest.raises(ValueError, match="data"):
            block.run({}, block.config)
