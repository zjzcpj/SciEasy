"""Tests for ViewProxy lazy loading (Phase 3.3)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import numpy as np
import pytest

from scieasy.core.proxy import ViewProxy
from scieasy.core.storage.ref import StorageReference
from scieasy.core.storage.zarr_backend import ZarrBackend
from scieasy.core.types.array import Array
from scieasy.core.types.base import TypeSignature


class Image(Array):
    """T-006 shim for the removed core ``Image`` class (T-008 migration)."""

    required_axes: ClassVar[frozenset[str]] = frozenset({"y", "x"})

    def __init__(
        self,
        *,
        shape: tuple[int, ...] | None = None,
        ndim: int | None = None,
        dtype: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(axes=["y", "x"], shape=shape, dtype=dtype, **kwargs)


class TestViewProxyLazyLoading:
    """Verify that no data is loaded until .slice() or .to_memory()."""

    @pytest.fixture()
    def zarr_ref(self, tmp_path: Path) -> StorageReference:
        """Write a test array and return its StorageReference."""
        backend = ZarrBackend()
        data = np.arange(100, dtype="float64").reshape(10, 10)
        ref = StorageReference(
            backend="zarr",
            path=str(tmp_path / "lazy.zarr"),
            metadata={"axes": ["y", "x"]},
        )
        return backend.write(data, ref)

    def test_shape_without_loading(self, zarr_ref: StorageReference) -> None:
        proxy = ViewProxy(
            storage_ref=zarr_ref,
            dtype_info=TypeSignature.from_type(Image),
        )
        assert proxy.shape == (10, 10)

    def test_axes_from_metadata(self, zarr_ref: StorageReference) -> None:
        proxy = ViewProxy(
            storage_ref=zarr_ref,
            dtype_info=TypeSignature.from_type(Image),
        )
        assert proxy.axes == ["y", "x"]

    def test_slice_partial_read(self, zarr_ref: StorageReference) -> None:
        proxy = ViewProxy(
            storage_ref=zarr_ref,
            dtype_info=TypeSignature.from_type(Image),
        )
        chunk = proxy.slice(slice(0, 3), slice(0, 5))
        assert chunk.shape == (3, 5)
        expected = np.arange(100).reshape(10, 10)[0:3, 0:5]
        np.testing.assert_array_equal(chunk, expected)

    def test_to_memory_full_load(self, zarr_ref: StorageReference) -> None:
        proxy = ViewProxy(
            storage_ref=zarr_ref,
            dtype_info=TypeSignature.from_type(Image),
        )
        full = proxy.to_memory()
        assert full.shape == (10, 10)
        expected = np.arange(100, dtype="float64").reshape(10, 10)
        np.testing.assert_array_equal(full, expected)

    def test_iter_chunks(self, zarr_ref: StorageReference) -> None:
        proxy = ViewProxy(
            storage_ref=zarr_ref,
            dtype_info=TypeSignature.from_type(Image),
        )
        chunks = list(proxy.iter_chunks(chunk_size=4))
        total_rows = sum(c.shape[0] for c in chunks)
        assert total_rows == 10

    def test_dtype_info_preserved(self, zarr_ref: StorageReference) -> None:
        sig = TypeSignature.from_type(Image)
        proxy = ViewProxy(storage_ref=zarr_ref, dtype_info=sig)
        assert proxy.dtype_info.type_chain == ["DataObject", "Array", "Image"]


class TestViewProxyFromDataObject:
    """Verify DataObject.view() integration with ViewProxy."""

    def test_image_view(self, tmp_path: Path) -> None:
        backend = ZarrBackend()
        data = np.zeros((64, 64), dtype="uint8")
        ref = StorageReference(
            backend="zarr",
            path=str(tmp_path / "img.zarr"),
            metadata={"axes": ["y", "x"]},
        )
        result_ref = backend.write(data, ref)

        img = Image(shape=(64, 64), dtype="uint8", storage_ref=result_ref)
        proxy = img.view()
        assert proxy.shape == (64, 64)
        assert proxy.axes == ["y", "x"]

        loaded = proxy.to_memory()
        np.testing.assert_array_equal(loaded, data)
