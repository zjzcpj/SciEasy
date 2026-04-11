"""Tests for DataObject persistence — get_in_memory_data() and save()."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import numpy as np
import pytest

from scieasy.core.types.array import Array
from scieasy.core.types.base import DataObject
from scieasy.core.types.text import Text


def _make_zarr_backed_array(data: np.ndarray, axes: list[str]) -> Array:
    """Create a storage-backed Array via ZarrBackend (ADR-031 D2)."""
    from scieasy.core.storage.ref import StorageReference
    from scieasy.core.storage.zarr_backend import ZarrBackend

    zarr_path = str(Path(tempfile.gettempdir()) / f"{uuid.uuid4()}.zarr")
    ref = ZarrBackend().write(data, StorageReference(backend="zarr", path=zarr_path))
    return Array(axes=axes, shape=tuple(data.shape), dtype=str(data.dtype), storage_ref=ref)


class TestArrayGetInMemoryData:
    """Array.get_in_memory_data — returns numpy array from storage backend."""

    def test_array_get_in_memory_data(self) -> None:
        data = np.ones((3, 3), dtype="float64")
        arr = _make_zarr_backed_array(data, ["y", "x"])
        result = arr.get_in_memory_data()
        assert isinstance(result, np.ndarray)
        assert result.shape == (3, 3)


class TestTextGetInMemoryData:
    """Text.get_in_memory_data — returns content string."""

    def test_text_get_in_memory_data(self) -> None:
        t = Text(content="hello world")
        result = t.get_in_memory_data()
        assert result == "hello world"


class TestBareDataObjectRaises:
    """DataObject.get_in_memory_data — raises ValueError without storage_ref."""

    def test_bare_dataobject_raises(self) -> None:
        obj = DataObject()
        with pytest.raises(ValueError, match="requires a storage_ref"):
            obj.get_in_memory_data()


class TestSaveArrayToZarr:
    """Array.save — idempotent for already-persisted arrays (ADR-031 D2)."""

    def test_save_array_already_backed_is_noop(self, tmp_path: Path) -> None:
        """A storage-backed Array returns its existing ref on save()."""
        data = np.arange(16, dtype="float32").reshape(4, 4)
        arr = _make_zarr_backed_array(data, ["y", "x"])

        original_ref = arr.storage_ref
        assert original_ref is not None
        assert original_ref.backend == "zarr"

        # save() to a different path is a no-op (returns existing ref).
        returned_ref = arr.save(str(tmp_path / "ignored.zarr"))
        assert returned_ref is original_ref


class TestSaveIdempotency:
    """DataObject.save — always a no-op for storage-backed objects."""

    def test_save_is_idempotent(self, tmp_path: Path) -> None:
        data = np.ones((2, 2), dtype="float64")
        arr = _make_zarr_backed_array(data, ["y", "x"])

        ref1 = arr.storage_ref
        # Repeated calls return the same StorageReference object.
        ref2 = arr.save("/different/path.zarr")

        assert ref1 is ref2  # exact same object returned


class TestSaveDataFrameToArrow:
    """DataFrame.save — idempotent for already-persisted DataFrames (ADR-031 D2)."""

    def test_save_dataframe_already_backed_is_noop(self, tmp_path: Path) -> None:
        """A storage-backed DataFrame returns its existing ref on save()."""
        import pyarrow as pa

        from scieasy.core.storage.arrow_backend import ArrowBackend
        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.types.dataframe import DataFrame

        table = pa.table({"a": [1, 2, 3], "b": [4, 5, 6]})
        src_path = str(tmp_path / "src.parquet")
        ref = ArrowBackend().write(table, StorageReference(backend="arrow", path=src_path))
        df = DataFrame(columns=["a", "b"], row_count=3, storage_ref=ref)

        assert df.storage_ref is not None
        assert df.storage_ref.backend == "arrow"

        # save() to a different path is a no-op (returns existing ref).
        returned_ref = df.save(str(tmp_path / "ignored.parquet"))
        assert returned_ref is df.storage_ref


class TestSaveTextToFilesystem:
    """Text.save — round-trip through FilesystemBackend."""

    def test_save_text_to_filesystem(self, tmp_path: Path) -> None:
        t = Text(content="hello world")

        target = str(tmp_path / "test.txt")
        ref = t.save(target)

        assert ref is not None
        assert ref.backend == "filesystem"
        assert ref.path == target
        assert t.storage_ref is not None

        loaded = Path(target).read_text(encoding="utf-8")
        assert loaded == "hello world"


class TestWriteFromMemoryZarr:
    """ZarrBackend.write_from_memory — round-trip test."""

    def test_write_from_memory(self, tmp_path: Path) -> None:
        import zarr

        from scieasy.core.storage.zarr_backend import ZarrBackend

        backend = ZarrBackend()
        data = np.arange(12, dtype="int32").reshape(3, 4)
        target = str(tmp_path / "wfm.zarr")

        ref = backend.write_from_memory(data, target)

        assert ref.backend == "zarr"
        assert ref.path == target
        loaded = np.asarray(zarr.open_array(target, mode="r"))
        np.testing.assert_array_equal(loaded, data)


class TestWriteFromMemoryArrow:
    """ArrowBackend.write_from_memory — round-trip test."""

    def test_write_from_memory(self, tmp_path: Path) -> None:
        import pyarrow.parquet as pq

        from scieasy.core.storage.arrow_backend import ArrowBackend

        backend = ArrowBackend()
        data = {"x": [10, 20], "y": [30, 40]}
        target = str(tmp_path / "wfm.parquet")

        ref = backend.write_from_memory(data, target)

        assert ref.backend == "arrow"
        assert ref.path == target
        loaded = pq.read_table(target)
        assert loaded.column_names == ["x", "y"]
        assert loaded.num_rows == 2


class TestWriteFromMemoryFilesystem:
    """FilesystemBackend.write_from_memory — round-trip test."""

    def test_write_from_memory(self, tmp_path: Path) -> None:
        from scieasy.core.storage.filesystem import FilesystemBackend

        backend = FilesystemBackend()
        target = str(tmp_path / "wfm.txt")

        ref = backend.write_from_memory("test content", target)

        assert ref.backend == "filesystem"
        assert ref.path == target
        loaded = Path(target).read_text(encoding="utf-8")
        assert loaded == "test content"
