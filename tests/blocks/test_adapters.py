"""Tests for format adapters -- CSV, Parquet, Generic, TIFF, Zarr (direct coverage)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyarrow as pa
import pytest

from scieasy.blocks.io.adapters.csv_adapter import CSVAdapter
from scieasy.blocks.io.adapters.generic_adapter import GenericAdapter, _guess_mime
from scieasy.blocks.io.adapters.parquet_adapter import ParquetAdapter
from scieasy.blocks.io.adapters.zarr_adapter import ZarrAdapter
from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.dataframe import DataFrame

# ---------------------------------------------------------------------------
# CSV Adapter
# ---------------------------------------------------------------------------


class TestCSVAdapterDirect:
    """CSVAdapter — direct read/write coverage."""

    def test_read_csv(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("a,b\n1,2\n3,4\n")
        adapter = CSVAdapter()
        result = adapter.read(csv_file)
        assert isinstance(result, DataFrame)
        assert result.columns == ["a", "b"]
        assert result.row_count == 2

    def test_write_from_dataframe(self, tmp_path: Path) -> None:
        adapter = CSVAdapter()
        table = pa.table({"x": [1, 2], "y": [3, 4]})
        df = DataFrame(columns=["x", "y"], row_count=2)
        df._arrow_table = table  # type: ignore[attr-defined]
        out = adapter.write(df, tmp_path / "out.csv")
        assert out.exists()

    def test_write_from_arrow_table(self, tmp_path: Path) -> None:
        adapter = CSVAdapter()
        table = pa.table({"col": [10, 20]})
        out = adapter.write(table, tmp_path / "out.csv")
        assert out.exists()

    def test_write_from_dict(self, tmp_path: Path) -> None:
        adapter = CSVAdapter()
        out = adapter.write({"col": [1, 2, 3]}, tmp_path / "out.csv")
        assert out.exists()

    def test_write_invalid_type_raises(self, tmp_path: Path) -> None:
        adapter = CSVAdapter()
        with pytest.raises(TypeError, match="Cannot write"):
            adapter.write(12345, tmp_path / "out.csv")

    def test_supported_extensions(self) -> None:
        assert CSVAdapter().supported_extensions() == [".csv"]

    def test_create_reference(self, tmp_path: Path) -> None:
        adapter = CSVAdapter()
        ref = adapter.create_reference(tmp_path / "data.csv")
        assert isinstance(ref, StorageReference)
        assert ref.backend == "arrow"
        assert ref.format == "csv"
        # StorageReference normalizes paths to POSIX (ADR-017, #53)
        assert ref.path == str(tmp_path / "data.csv").replace("\\", "/")


# ---------------------------------------------------------------------------
# Parquet Adapter
# ---------------------------------------------------------------------------


class TestParquetAdapterDirect:
    """ParquetAdapter — direct read/write coverage."""

    def test_read_parquet(self, tmp_path: Path) -> None:
        pq_file = tmp_path / "test.parquet"
        table = pa.table({"a": [1, 2], "b": [3, 4]})
        import pyarrow.parquet as pq

        pq.write_table(table, str(pq_file))

        adapter = ParquetAdapter()
        result = adapter.read(pq_file)
        assert isinstance(result, DataFrame)
        assert result.columns == ["a", "b"]
        assert result.row_count == 2

    def test_write_from_dataframe(self, tmp_path: Path) -> None:
        adapter = ParquetAdapter()
        table = pa.table({"x": [1], "y": [2]})
        df = DataFrame(columns=["x", "y"], row_count=1)
        df._arrow_table = table  # type: ignore[attr-defined]
        out = adapter.write(df, tmp_path / "out.parquet")
        assert out.exists()

    def test_write_from_arrow_table(self, tmp_path: Path) -> None:
        adapter = ParquetAdapter()
        table = pa.table({"col": [10]})
        out = adapter.write(table, tmp_path / "out.parquet")
        assert out.exists()

    def test_write_from_dict(self, tmp_path: Path) -> None:
        adapter = ParquetAdapter()
        out = adapter.write({"col": [1, 2]}, tmp_path / "out.parquet")
        assert out.exists()

    def test_write_invalid_type_raises(self, tmp_path: Path) -> None:
        adapter = ParquetAdapter()
        with pytest.raises(TypeError, match="Cannot write"):
            adapter.write(12345, tmp_path / "out.parquet")

    def test_supported_extensions(self) -> None:
        assert ParquetAdapter().supported_extensions() == [".parquet", ".pq"]

    def test_create_reference(self, tmp_path: Path) -> None:
        adapter = ParquetAdapter()
        ref = adapter.create_reference(tmp_path / "data.parquet")
        assert isinstance(ref, StorageReference)
        assert ref.backend == "arrow"
        assert ref.format == "parquet"
        assert ref.path == str(tmp_path / "data.parquet").replace("\\", "/")


# ---------------------------------------------------------------------------
# Generic Adapter
# ---------------------------------------------------------------------------


class TestGenericAdapter:
    """GenericAdapter — fallback binary file adapter."""

    def test_read_creates_artifact(self, tmp_path: Path) -> None:
        f = tmp_path / "data.bin"
        f.write_bytes(b"\x00\x01\x02")
        adapter = GenericAdapter()
        result = adapter.read(f)
        assert isinstance(result, Artifact)
        assert result.file_path == f
        assert result.description == "data.bin"

    def test_read_guesses_mime_type(self, tmp_path: Path) -> None:
        f = tmp_path / "image.png"
        f.write_bytes(b"\x89PNG")
        result = GenericAdapter().read(f)
        assert result.mime_type == "image/png"

    def test_write_artifact_copies_file(self, tmp_path: Path) -> None:
        src = tmp_path / "source.bin"
        src.write_bytes(b"binary content")
        artifact = Artifact(file_path=src, mime_type="application/octet-stream")
        out = tmp_path / "dest.bin"
        GenericAdapter().write(artifact, out)
        assert out.read_bytes() == b"binary content"

    def test_write_bytes(self, tmp_path: Path) -> None:
        out = tmp_path / "out.dat"
        GenericAdapter().write(b"raw bytes", out)
        assert out.read_bytes() == b"raw bytes"

    def test_write_string(self, tmp_path: Path) -> None:
        out = tmp_path / "out.txt"
        GenericAdapter().write("hello text", out)
        assert out.read_text(encoding="utf-8") == "hello text"

    def test_write_unsupported_type_raises(self, tmp_path: Path) -> None:
        with pytest.raises(TypeError, match="Cannot write"):
            GenericAdapter().write(42, tmp_path / "out.bin")

    def test_supported_extensions(self) -> None:
        exts = GenericAdapter().supported_extensions()
        assert ".bin" in exts
        assert ".pdf" in exts

    def test_create_reference(self, tmp_path: Path) -> None:
        adapter = GenericAdapter()
        ref = adapter.create_reference(tmp_path / "file.pdf")
        assert isinstance(ref, StorageReference)
        assert ref.backend == "filesystem"
        assert ref.format == "pdf"
        assert ref.path == str(tmp_path / "file.pdf").replace("\\", "/")

    def test_create_reference_unknown_extension(self, tmp_path: Path) -> None:
        adapter = GenericAdapter()
        ref = adapter.create_reference(tmp_path / "file.xyz")
        assert ref.format == "xyz"


class TestGuessMime:
    """_guess_mime — MIME type inference from file extension."""

    @pytest.mark.parametrize(
        ("suffix", "expected"),
        [
            (".csv", "text/csv"),
            (".json", "application/json"),
            (".txt", "text/plain"),
            (".png", "image/png"),
            (".jpg", "image/jpeg"),
            (".jpeg", "image/jpeg"),
            (".tif", "image/tiff"),
            (".tiff", "image/tiff"),
            (".pdf", "application/pdf"),
            (".bin", "application/octet-stream"),
            (".dat", "application/octet-stream"),
        ],
    )
    def test_known_extensions(self, suffix: str, expected: str) -> None:
        assert _guess_mime(Path(f"file{suffix}")) == expected

    def test_unknown_extension(self) -> None:
        assert _guess_mime(Path("file.xyz")) == "application/octet-stream"


# ---------------------------------------------------------------------------
# Zarr Adapter
# ---------------------------------------------------------------------------


class TestZarrAdapter:
    """ZarrAdapter -- create_reference support."""

    def test_create_reference(self, tmp_path: Path) -> None:
        adapter = ZarrAdapter()
        ref = adapter.create_reference(tmp_path / "data.zarr")
        assert isinstance(ref, StorageReference)
        assert ref.backend == "zarr"
        assert ref.format == "zarr"
        assert ref.path == str(tmp_path / "data.zarr").replace("\\", "/")

    def test_supported_extensions(self) -> None:
        assert ZarrAdapter().supported_extensions() == [".zarr"]

    def test_read_raises_not_implemented(self, tmp_path: Path) -> None:
        with pytest.raises(NotImplementedError):
            ZarrAdapter().read(tmp_path / "data.zarr")

    def test_write_raises_not_implemented(self, tmp_path: Path) -> None:
        with pytest.raises(NotImplementedError):
            ZarrAdapter().write(object(), tmp_path / "data.zarr")


# ---------------------------------------------------------------------------
# TIFF Adapter
# ---------------------------------------------------------------------------


def _has_tifffile() -> bool:
    try:
        import tifffile  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _has_tifffile(), reason="tifffile not installed")
class TestTIFFAdapter:
    """TIFFAdapter — TIFF/OME-TIFF image file support."""

    def test_read_tiff(self, tmp_path: Path) -> None:
        import tifffile as tf

        from scieasy.blocks.io.adapters.tiff_adapter import TIFFAdapter
        from scieasy.core.types.array import Image

        arr = np.random.randint(0, 255, (32, 32), dtype=np.uint8)
        path = tmp_path / "test.tif"
        tf.imwrite(str(path), arr)

        adapter = TIFFAdapter()
        result = adapter.read(path)
        assert isinstance(result, Image)
        assert result.shape == (32, 32)

    def test_write_from_ndarray(self, tmp_path: Path) -> None:
        from scieasy.blocks.io.adapters.tiff_adapter import TIFFAdapter

        arr = np.zeros((16, 16), dtype=np.uint8)
        out = tmp_path / "out.tiff"
        result = TIFFAdapter().write(arr, out)
        assert result.exists()

    def test_write_from_image(self, tmp_path: Path) -> None:
        from scieasy.blocks.io.adapters.tiff_adapter import TIFFAdapter
        from scieasy.core.types.array import Image

        arr = np.zeros((8, 8), dtype=np.float32)
        img = Image(shape=arr.shape, ndim=arr.ndim, dtype=arr.dtype)
        img._data = arr  # type: ignore[attr-defined]
        out = tmp_path / "out.tif"
        result = TIFFAdapter().write(img, out)
        assert result.exists()

    def test_write_unsupported_type_raises(self, tmp_path: Path) -> None:
        from scieasy.blocks.io.adapters.tiff_adapter import TIFFAdapter

        with pytest.raises(TypeError, match="Cannot write"):
            TIFFAdapter().write("not an array", tmp_path / "out.tif")

    def test_supported_extensions(self) -> None:
        from scieasy.blocks.io.adapters.tiff_adapter import TIFFAdapter

        assert TIFFAdapter().supported_extensions() == [".tif", ".tiff"]

    def test_create_reference(self, tmp_path: Path) -> None:
        from scieasy.blocks.io.adapters.tiff_adapter import TIFFAdapter

        adapter = TIFFAdapter()
        ref = adapter.create_reference(tmp_path / "image.tif")
        assert isinstance(ref, StorageReference)
        assert ref.backend == "filesystem"
        assert ref.format == "tiff"
        assert ref.path == str(tmp_path / "image.tif").replace("\\", "/")
