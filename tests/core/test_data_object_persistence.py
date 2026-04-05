"""Tests for DataObject persistence — get_in_memory_data() and save()."""

from __future__ import annotations

import numpy as np
import pytest

from scieasy.core.types.array import Array
from scieasy.core.types.base import DataObject
from scieasy.core.types.text import Text


class TestArrayGetInMemoryData:
    """Array.get_in_memory_data — returns numpy array from _data."""

    def test_array_get_in_memory_data(self) -> None:
        arr = Array(shape=(3, 3), ndim=2, dtype="float64")
        arr._data = np.ones((3, 3))
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
    """DataObject.get_in_memory_data — raises ValueError without data."""

    def test_bare_dataobject_raises(self) -> None:
        obj = DataObject()
        with pytest.raises(ValueError, match="has no in-memory data"):
            obj.get_in_memory_data()


class TestSaveArrayToZarr:
    """Array.save — creates zarr store and sets storage_ref."""

    def test_save_array_to_zarr(self, tmp_path: object) -> None:
        import zarr

        arr = Array(shape=(4, 4), ndim=2, dtype="float32")
        arr._data = np.arange(16, dtype="float32").reshape(4, 4)

        target = str(tmp_path) + "/test.zarr"  # type: ignore[operator]
        ref = arr.save(target)

        assert ref is not None
        assert ref.backend == "zarr"
        assert ref.path == target
        assert arr.storage_ref is not None
        assert arr.storage_ref.backend == "zarr"

        # Verify data was actually written
        z = zarr.open_array(target, mode="r")
        loaded = np.asarray(z)
        np.testing.assert_array_equal(loaded, arr._data)
