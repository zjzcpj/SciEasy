"""Tests for ADR-031 Phase 3 (step 18): SaveData streaming export paths.

Verifies that:
- zarr-to-zarr copy works without full materialisation.
- arrow-to-parquet streaming writes produce correct output.
- arrow-to-csv streaming writes produce correct output.
- Non-streaming paths (fallbacks) still work correctly.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.csv as pcsv
import pyarrow.parquet as pq
import zarr

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.io.savers.save_data import (
    _save_array,
    _save_dataframe,
    _zarr_to_zarr_copy,
)
from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.array import Array
from scieasy.core.types.dataframe import DataFrame

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _zarr_backed_array(axes: list[str], data: np.ndarray) -> Array:
    """Return an Array backed by zarr storage."""
    tmpdir = tempfile.mkdtemp(prefix="scieasy_test_stream_")
    zarr_path = f"{tmpdir}/{uuid.uuid4()}.zarr"
    zarr.save(zarr_path, data)
    ref = StorageReference(
        backend="zarr",
        path=zarr_path,
        metadata={"shape": list(data.shape), "dtype": str(data.dtype)},
    )
    return Array(axes=axes, shape=data.shape, dtype=str(data.dtype), storage_ref=ref)


def _arrow_backed_dataframe(table: pa.Table) -> DataFrame:
    """Return a DataFrame backed by arrow/parquet storage."""
    tmpdir = tempfile.mkdtemp(prefix="scieasy_test_stream_")
    pq_path = f"{tmpdir}/{uuid.uuid4()}.parquet"
    pq.write_table(table, pq_path)
    ref = StorageReference(
        backend="arrow",
        path=pq_path,
        format="parquet",
        metadata={"columns": table.column_names, "num_rows": table.num_rows},
    )
    df = DataFrame(columns=table.column_names, row_count=table.num_rows, storage_ref=ref)
    return df


# ---------------------------------------------------------------------------
# zarr-to-zarr copy
# ---------------------------------------------------------------------------


class TestZarrToZarrCopy:
    """ADR-031 Phase 3: direct zarr-to-zarr copy."""

    def test_zarr_to_zarr_copy_preserves_data(self, tmp_path: Path) -> None:
        data = np.arange(100, dtype="float32").reshape(10, 10)
        src_path = str(tmp_path / "src.zarr")
        zarr.save(src_path, data)
        dst_path = str(tmp_path / "dst.zarr")
        _zarr_to_zarr_copy(src_path, dst_path)
        result = np.asarray(zarr.open_array(dst_path, mode="r"))
        np.testing.assert_array_equal(result, data)

    def test_zarr_to_zarr_copy_preserves_attrs(self, tmp_path: Path) -> None:
        data = np.arange(12, dtype="float64").reshape(3, 4)
        src_path = str(tmp_path / "src.zarr")
        z = zarr.open_array(src_path, mode="w", shape=data.shape, dtype=data.dtype)
        z[:] = data
        z.attrs["axes"] = ["z", "y"]
        dst_path = str(tmp_path / "dst.zarr")
        _zarr_to_zarr_copy(src_path, dst_path)
        dst = zarr.open_array(dst_path, mode="r")
        assert list(dst.attrs.get("axes", [])) == ["z", "y"]

    def test_zarr_to_zarr_copy_overwrites_existing(self, tmp_path: Path) -> None:
        """If dst already exists, it gets replaced."""
        data = np.arange(6, dtype="int32").reshape(2, 3)
        src_path = str(tmp_path / "src.zarr")
        zarr.save(src_path, data)
        dst_path = str(tmp_path / "dst.zarr")
        zarr.save(dst_path, np.zeros((10, 10), dtype="int32"))
        _zarr_to_zarr_copy(src_path, dst_path)
        result = np.asarray(zarr.open_array(dst_path, mode="r"))
        np.testing.assert_array_equal(result, data)


# ---------------------------------------------------------------------------
# _save_array streaming paths
# ---------------------------------------------------------------------------


class TestSaveArrayStreaming:
    """ADR-031 Phase 3: _save_array with zarr-to-zarr streaming."""

    def test_save_array_zarr_streaming(self, tmp_path: Path) -> None:
        """Zarr-backed Array saved to .zarr uses streaming copy."""
        data = np.arange(60, dtype="float32").reshape(3, 4, 5)
        arr = _zarr_backed_array(["z", "y", "x"], data)
        dst = tmp_path / "output.zarr"
        config = BlockConfig(params={"core_type": "Array", "path": str(dst)})
        _save_array(arr, config)
        result = np.asarray(zarr.open_array(str(dst), mode="r"))
        np.testing.assert_array_equal(result, data)

    def test_save_array_zarr_fallback_no_ref(self, tmp_path: Path) -> None:
        """Array without storage_ref falls back to materialise path."""
        data = np.arange(12, dtype="float32").reshape(3, 4)
        arr = Array(axes=["y", "x"], shape=data.shape, dtype=str(data.dtype))
        arr._data = data  # type: ignore[attr-defined]
        dst = tmp_path / "output.zarr"
        config = BlockConfig(params={"core_type": "Array", "path": str(dst)})
        _save_array(arr, config)
        result = np.asarray(zarr.open_array(str(dst), mode="r"))
        np.testing.assert_array_equal(result, data)

    def test_save_array_npy_still_works(self, tmp_path: Path) -> None:
        """Non-streaming formats still work correctly."""
        data = np.arange(12, dtype="float32").reshape(3, 4)
        arr = _zarr_backed_array(["y", "x"], data)
        dst = tmp_path / "output.npy"
        config = BlockConfig(params={"core_type": "Array", "path": str(dst)})
        _save_array(arr, config)
        result = np.load(str(dst))
        np.testing.assert_array_equal(result, data)


# ---------------------------------------------------------------------------
# _save_dataframe streaming paths
# ---------------------------------------------------------------------------


class TestSaveDataFrameStreaming:
    """ADR-031 Phase 3: _save_dataframe with arrow streaming."""

    def test_save_dataframe_parquet_streaming(self, tmp_path: Path) -> None:
        """Arrow-backed DataFrame saved to .parquet uses streaming."""
        table = pa.table({"a": [1, 2, 3, 4, 5], "b": [10.0, 20.0, 30.0, 40.0, 50.0]})
        df = _arrow_backed_dataframe(table)
        dst = tmp_path / "output.parquet"
        config = BlockConfig(params={"core_type": "DataFrame", "path": str(dst)})
        _save_dataframe(df, config)
        result = pq.read_table(str(dst))
        assert result.equals(table)

    def test_save_dataframe_csv_streaming(self, tmp_path: Path) -> None:
        """Arrow-backed DataFrame saved to .csv uses streaming."""
        table = pa.table({"x": [1, 2, 3], "y": ["a", "b", "c"]})
        df = _arrow_backed_dataframe(table)
        dst = tmp_path / "output.csv"
        config = BlockConfig(params={"core_type": "DataFrame", "path": str(dst)})
        _save_dataframe(df, config)
        result = pcsv.read_csv(str(dst))
        assert result.equals(table)

    def test_save_dataframe_tsv_streaming(self, tmp_path: Path) -> None:
        """Arrow-backed DataFrame saved to .tsv uses streaming."""
        table = pa.table({"col1": [10, 20], "col2": [30, 40]})
        df = _arrow_backed_dataframe(table)
        dst = tmp_path / "output.tsv"
        config = BlockConfig(params={"core_type": "DataFrame", "path": str(dst)})
        _save_dataframe(df, config)
        result = pcsv.read_csv(
            str(dst),
            parse_options=pcsv.ParseOptions(delimiter="\t"),
        )
        assert result.equals(table)

    def test_save_dataframe_json_non_streaming(self, tmp_path: Path) -> None:
        """JSON format does not support streaming, uses fallback."""
        table = pa.table({"a": [1, 2], "b": [3.0, 4.0]})
        df = _arrow_backed_dataframe(table)
        dst = tmp_path / "output.json"
        config = BlockConfig(params={"core_type": "DataFrame", "path": str(dst)})
        _save_dataframe(df, config)
        import json

        with open(str(dst), encoding="utf-8") as fh:
            records = json.load(fh)
        assert records == [{"a": 1, "b": 3.0}, {"a": 2, "b": 4.0}]

    def test_save_dataframe_parquet_non_arrow_fallback(self, tmp_path: Path) -> None:
        """DataFrame without arrow backend uses non-streaming parquet write."""
        table = pa.table({"x": [1, 2, 3]})
        df = DataFrame(columns=["x"], row_count=3)
        df._arrow_table = table  # type: ignore[attr-defined]
        dst = tmp_path / "output.parquet"
        config = BlockConfig(params={"core_type": "DataFrame", "path": str(dst)})
        _save_dataframe(df, config)
        result = pq.read_table(str(dst))
        assert result.equals(table)
