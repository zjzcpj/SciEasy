"""Tests for StorageReference — path normalization and cross-platform portability."""

from __future__ import annotations

from scieasy.core.storage.ref import StorageReference


class TestPathNormalization:
    """ADR-017 / #53: StorageReference.path always uses POSIX forward slashes."""

    def test_backslashes_normalized(self) -> None:
        ref = StorageReference(backend="zarr", path="C:\\Users\\test\\data.zarr")
        assert ref.path == "C:/Users/test/data.zarr"

    def test_posix_path_unchanged(self) -> None:
        ref = StorageReference(backend="zarr", path="/home/user/data.zarr")
        assert ref.path == "/home/user/data.zarr"

    def test_mixed_separators_normalized(self) -> None:
        ref = StorageReference(backend="arrow", path="data/parquet\\table.parquet")
        assert ref.path == "data/parquet/table.parquet"

    def test_windows_unc_path(self) -> None:
        ref = StorageReference(backend="filesystem", path="\\\\server\\share\\file.txt")
        assert ref.path == "//server/share/file.txt"

    def test_relative_path(self) -> None:
        ref = StorageReference(backend="zarr", path="data\\zarr\\img.zarr")
        assert ref.path == "data/zarr/img.zarr"

    def test_empty_path(self) -> None:
        ref = StorageReference(backend="zarr", path="")
        assert ref.path == ""

    def test_metadata_preserved(self) -> None:
        ref = StorageReference(
            backend="zarr",
            path="C:\\data\\arr.zarr",
            format="zarr",
            metadata={"shape": [10, 20]},
        )
        assert ref.path == "C:/data/arr.zarr"
        assert ref.format == "zarr"
        assert ref.metadata == {"shape": [10, 20]}
