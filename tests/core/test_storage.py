"""Tests for storage backend round-trips (Phase 3.2)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyarrow as pa
import pytest

from scieasy.core.storage.arrow_backend import ArrowBackend
from scieasy.core.storage.composite_store import CompositeStore
from scieasy.core.storage.filesystem import FilesystemBackend
from scieasy.core.storage.ref import StorageReference
from scieasy.core.storage.zarr_backend import ZarrBackend


class TestZarrBackend:
    """Round-trip write/read for Zarr arrays."""

    def test_write_read_roundtrip(self, tmp_path: Path) -> None:
        backend = ZarrBackend()
        data = np.arange(100, dtype="float64").reshape(10, 10)
        ref = StorageReference(backend="zarr", path=str(tmp_path / "test.zarr"))

        result_ref = backend.write(data, ref)
        assert result_ref.metadata is not None
        assert result_ref.metadata["shape"] == [10, 10]

        loaded = backend.read(result_ref)
        np.testing.assert_array_equal(loaded, data)

    def test_slice(self, tmp_path: Path) -> None:
        backend = ZarrBackend()
        data = np.arange(100, dtype="float64").reshape(10, 10)
        ref = StorageReference(backend="zarr", path=str(tmp_path / "test.zarr"))
        result_ref = backend.write(data, ref)

        sliced = backend.slice(result_ref, slice(0, 3), slice(0, 5))
        assert sliced.shape == (3, 5)
        np.testing.assert_array_equal(sliced, data[0:3, 0:5])

    def test_iter_chunks(self, tmp_path: Path) -> None:
        backend = ZarrBackend()
        data = np.arange(100, dtype="float64").reshape(10, 10)
        ref = StorageReference(backend="zarr", path=str(tmp_path / "test.zarr"))
        result_ref = backend.write(data, ref)

        chunks = list(backend.iter_chunks(result_ref, chunk_size=3))
        assert len(chunks) == 4  # 3+3+3+1
        np.testing.assert_array_equal(chunks[0], data[0:3])
        np.testing.assert_array_equal(chunks[-1], data[9:10])

    def test_get_metadata(self, tmp_path: Path) -> None:
        backend = ZarrBackend()
        data = np.zeros((5, 8), dtype="int32")
        ref = StorageReference(backend="zarr", path=str(tmp_path / "meta.zarr"))
        result_ref = backend.write(data, ref)

        meta = backend.get_metadata(result_ref)
        assert meta["shape"] == [5, 8]
        assert meta["dtype"] == "int32"
        assert meta["ndim"] == 2


class TestArrowBackend:
    """Round-trip write/read for Parquet tables."""

    def test_write_read_roundtrip_from_dict(self, tmp_path: Path) -> None:
        backend = ArrowBackend()
        data = {"name": ["Alice", "Bob"], "score": [95.5, 87.0]}
        ref = StorageReference(backend="arrow", path=str(tmp_path / "test.parquet"))

        result_ref = backend.write(data, ref)
        assert result_ref.format == "parquet"
        assert result_ref.metadata is not None
        assert result_ref.metadata["num_rows"] == 2

        loaded = backend.read(result_ref)
        assert isinstance(loaded, pa.Table)
        assert loaded.num_rows == 2
        assert loaded.column_names == ["name", "score"]

    def test_write_read_roundtrip_from_table(self, tmp_path: Path) -> None:
        backend = ArrowBackend()
        table = pa.table({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        ref = StorageReference(backend="arrow", path=str(tmp_path / "table.parquet"))

        result_ref = backend.write(table, ref)
        loaded = backend.read(result_ref)
        assert loaded.equals(table)

    def test_slice_columns(self, tmp_path: Path) -> None:
        backend = ArrowBackend()
        data = {"x": [1, 2], "y": [3, 4], "z": [5, 6]}
        ref = StorageReference(backend="arrow", path=str(tmp_path / "slice.parquet"))
        result_ref = backend.write(data, ref)

        sliced = backend.slice(result_ref, ["x", "z"])
        assert sliced.column_names == ["x", "z"]
        assert sliced.num_rows == 2

    def test_iter_chunks(self, tmp_path: Path) -> None:
        backend = ArrowBackend()
        data = {"val": list(range(100))}
        ref = StorageReference(backend="arrow", path=str(tmp_path / "chunks.parquet"))
        result_ref = backend.write(data, ref)

        chunks = list(backend.iter_chunks(result_ref, chunk_size=30))
        total_rows = sum(c.num_rows for c in chunks)
        assert total_rows == 100

    def test_get_metadata(self, tmp_path: Path) -> None:
        backend = ArrowBackend()
        data = {"col_a": [1], "col_b": ["x"]}
        ref = StorageReference(backend="arrow", path=str(tmp_path / "meta.parquet"))
        result_ref = backend.write(data, ref)

        meta = backend.get_metadata(result_ref)
        assert meta["columns"] == ["col_a", "col_b"]
        assert meta["num_rows"] == 1

    def test_write_invalid_type_raises(self, tmp_path: Path) -> None:
        backend = ArrowBackend()
        ref = StorageReference(backend="arrow", path=str(tmp_path / "bad.parquet"))
        with pytest.raises(TypeError, match=r"dict or pa\.Table"):
            backend.write("not a table", ref)


class TestFilesystemBackend:
    """Round-trip write/read for text and binary files."""

    def test_text_roundtrip(self, tmp_path: Path) -> None:
        backend = FilesystemBackend()
        content = "Hello, SciEasy!\nLine 2."
        ref = StorageReference(
            backend="filesystem",
            path=str(tmp_path / "hello.txt"),
            format="plain",
        )
        result_ref = backend.write(content, ref)
        assert result_ref.metadata is not None
        assert result_ref.metadata["size"] > 0

        loaded = backend.read(result_ref)
        assert loaded == content

    def test_binary_roundtrip(self, tmp_path: Path) -> None:
        backend = FilesystemBackend()
        data = b"\x00\x01\x02\xff"
        ref = StorageReference(
            backend="filesystem",
            path=str(tmp_path / "blob.bin"),
            format="binary",
        )
        result_ref = backend.write(data, ref)
        loaded = backend.read(result_ref)
        assert loaded == data

    def test_slice_bytes(self, tmp_path: Path) -> None:
        backend = FilesystemBackend()
        data = b"0123456789"
        ref = StorageReference(
            backend="filesystem",
            path=str(tmp_path / "range.bin"),
            format="binary",
        )
        result_ref = backend.write(data, ref)
        chunk = backend.slice(result_ref, 2, 4)
        assert chunk == b"2345"

    def test_iter_chunks(self, tmp_path: Path) -> None:
        backend = FilesystemBackend()
        data = b"A" * 100
        ref = StorageReference(
            backend="filesystem",
            path=str(tmp_path / "chunked.bin"),
            format="binary",
        )
        result_ref = backend.write(data, ref)
        chunks = list(backend.iter_chunks(result_ref, chunk_size=30))
        assert len(chunks) == 4  # 30+30+30+10
        total = b"".join(chunks)
        assert total == data

    def test_get_metadata(self, tmp_path: Path) -> None:
        backend = FilesystemBackend()
        ref = StorageReference(
            backend="filesystem",
            path=str(tmp_path / "meta.txt"),
            format="plain",
        )
        backend.write("data", ref)
        meta = backend.get_metadata(ref)
        assert "size" in meta
        assert "name" in meta
        assert meta["name"] == "meta.txt"

    def test_write_invalid_type_raises(self, tmp_path: Path) -> None:
        backend = FilesystemBackend()
        ref = StorageReference(
            backend="filesystem",
            path=str(tmp_path / "bad.bin"),
        )
        with pytest.raises(TypeError, match="str or bytes"):
            backend.write(12345, ref)


class TestCompositeStore:
    """Round-trip write/read for composite (directory-of-slots) storage."""

    def test_roundtrip(self, tmp_path: Path) -> None:
        store = CompositeStore()
        composite_data = {
            "matrix": ("zarr", np.arange(20, dtype="float32").reshape(4, 5)),
            "metadata": ("arrow", {"name": ["a", "b", "c", "d"], "val": [1, 2, 3, 4]}),
            "notes": ("filesystem", "Experiment notes go here."),
        }
        ref = StorageReference(backend="composite", path=str(tmp_path / "composite"))

        result_ref = store.write(composite_data, ref)
        assert result_ref.metadata is not None
        assert sorted(result_ref.metadata["slot_names"]) == ["matrix", "metadata", "notes"]

        loaded = store.read(result_ref)
        assert "matrix" in loaded
        assert "metadata" in loaded
        assert "notes" in loaded
        np.testing.assert_array_equal(loaded["matrix"], composite_data["matrix"][1])
        assert loaded["notes"] == "Experiment notes go here."

    def test_slice_slots(self, tmp_path: Path) -> None:
        store = CompositeStore()
        composite_data = {
            "a": ("filesystem", "slot_a"),
            "b": ("filesystem", "slot_b"),
            "c": ("filesystem", "slot_c"),
        }
        ref = StorageReference(backend="composite", path=str(tmp_path / "comp"))
        result_ref = store.write(composite_data, ref)

        subset = store.slice(result_ref, "a", "c")
        assert sorted(subset.keys()) == ["a", "c"]

    def test_get_metadata(self, tmp_path: Path) -> None:
        store = CompositeStore()
        composite_data = {
            "x": ("zarr", np.zeros((3, 3))),
            "y": ("filesystem", "text data"),
        }
        ref = StorageReference(backend="composite", path=str(tmp_path / "meta_comp"))
        result_ref = store.write(composite_data, ref)

        meta = store.get_metadata(result_ref)
        assert sorted(meta["slot_names"]) == ["x", "y"]
        assert meta["slot_backends"]["x"] == "zarr"
        assert meta["slot_backends"]["y"] == "filesystem"

    def test_iter_chunks(self, tmp_path: Path) -> None:
        store = CompositeStore()
        composite_data = {
            "s1": ("filesystem", "data1"),
            "s2": ("filesystem", "data2"),
        }
        ref = StorageReference(backend="composite", path=str(tmp_path / "iter_comp"))
        result_ref = store.write(composite_data, ref)

        slots = list(store.iter_chunks(result_ref, chunk_size=1))
        assert len(slots) == 2
        slot_names = {s[0] for s in slots}
        assert slot_names == {"s1", "s2"}
