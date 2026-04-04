"""Extended tests for DataObject — storage_ref, to_memory, type attributes."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from scieasy.core.storage.ref import StorageReference
from scieasy.core.storage.zarr_backend import ZarrBackend
from scieasy.core.types.array import Array, Image
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.base import DataObject
from scieasy.core.types.dataframe import DataFrame
from scieasy.core.types.series import Series
from scieasy.core.types.text import Text


class TestMetadataValidation:
    """ADR-017: metadata must be JSON-serializable for subprocess transport."""

    def test_valid_json_primitives(self) -> None:
        obj = DataObject(metadata={"str": "hello", "int": 42, "float": 3.14, "bool": True, "none": None})
        assert obj.metadata["str"] == "hello"

    def test_valid_nested_structures(self) -> None:
        obj = DataObject(metadata={"list": [1, 2, 3], "nested": {"a": {"b": [1]}}})
        assert obj.metadata["list"] == [1, 2, 3]

    def test_empty_metadata_passes(self) -> None:
        obj = DataObject(metadata={})
        assert obj.metadata == {}

    def test_none_metadata_defaults_to_empty(self) -> None:
        obj = DataObject(metadata=None)
        assert obj.metadata == {}

    def test_no_metadata_arg(self) -> None:
        obj = DataObject()
        assert obj.metadata == {}

    def test_set_raises(self) -> None:
        with pytest.raises(TypeError, match="JSON-serializable"):
            DataObject(metadata={"bad": {1, 2, 3}})

    def test_lambda_raises(self) -> None:
        with pytest.raises(TypeError, match="JSON-serializable"):
            DataObject(metadata={"fn": lambda x: x})

    def test_custom_object_raises(self) -> None:
        class Custom:
            pass

        with pytest.raises(TypeError, match="JSON-serializable"):
            DataObject(metadata={"obj": Custom()})

    def test_bytes_raises(self) -> None:
        with pytest.raises(TypeError, match="JSON-serializable"):
            DataObject(metadata={"data": b"\x00\x01"})


class TestDataObjectStorageRef:
    """DataObject.storage_ref — getter and setter."""

    def test_default_none(self) -> None:
        obj = DataObject()
        assert obj.storage_ref is None

    def test_setter(self) -> None:
        obj = DataObject()
        ref = StorageReference(backend="zarr", path="/tmp/test.zarr")
        obj.storage_ref = ref
        assert obj.storage_ref is ref

    def test_clear_to_none(self) -> None:
        ref = StorageReference(backend="zarr", path="/tmp/test.zarr")
        obj = DataObject(storage_ref=ref)
        assert obj.storage_ref is ref
        obj.storage_ref = None
        assert obj.storage_ref is None


class TestDataObjectToMemory:
    """DataObject.to_memory — delegates to view().to_memory()."""

    def test_to_memory_delegates(self, tmp_path: Path) -> None:
        arr = np.array([1.0, 2.0, 3.0])
        backend = ZarrBackend()
        ref = StorageReference(backend="zarr", path=str(tmp_path / "data.zarr"))
        ref = backend.write(arr, ref)

        obj = DataObject(storage_ref=ref)
        result = obj.to_memory()
        np.testing.assert_array_equal(result, arr)

    def test_to_memory_without_ref_raises(self) -> None:
        obj = DataObject()
        with pytest.raises(ValueError, match="Cannot create ViewProxy"):
            obj.to_memory()


class TestTypeAttributes:
    """Type attribute storage on concrete DataObject subclasses."""

    def test_array_shape_dtype(self) -> None:
        arr = Array(shape=(10, 20), ndim=2, dtype="float32")
        assert arr.shape == (10, 20)
        assert arr.ndim == 2
        assert arr.dtype == "float32"

    def test_image_inherits_array(self) -> None:
        img = Image(shape=(256, 256), ndim=2, dtype="uint8")
        assert img.shape == (256, 256)
        assert isinstance(img, Array)

    def test_series_attributes(self) -> None:
        s = Series(index_name="wavelength", value_name="intensity", length=100)
        assert s.index_name == "wavelength"
        assert s.value_name == "intensity"
        assert s.length == 100

    def test_dataframe_columns(self) -> None:
        df = DataFrame(columns=["a", "b", "c"], row_count=50)
        assert df.columns == ["a", "b", "c"]
        assert df.row_count == 50

    def test_text_content(self) -> None:
        t = Text(content="hello world", format="plain")
        assert t.content == "hello world"
        assert t.format == "plain"

    def test_artifact_file_path_and_mime(self) -> None:
        a = Artifact(file_path=Path("/data/report.pdf"), mime_type="application/pdf")
        assert a.file_path == Path("/data/report.pdf")
        assert a.mime_type == "application/pdf"
