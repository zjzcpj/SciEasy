"""Tests for BackendRouter — DataObject type to StorageBackend routing."""

from __future__ import annotations

import pytest

from scieasy.core.storage.arrow_backend import ArrowBackend
from scieasy.core.storage.composite_store import CompositeStore
from scieasy.core.storage.filesystem import FilesystemBackend
from scieasy.core.storage.router import BackendRouter
from scieasy.core.storage.zarr_backend import ZarrBackend
from scieasy.core.types.array import Array, Image
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.base import DataObject
from scieasy.core.types.composite import AnnData, CompositeData
from scieasy.core.types.dataframe import DataFrame, PeakTable
from scieasy.core.types.series import Series
from scieasy.core.types.text import Text


class TestDefaultRouting:
    """Default type→backend mapping via isinstance checks."""

    def test_array_routes_to_zarr(self) -> None:
        router = BackendRouter()
        arr = Array(shape=(10,), ndim=1, dtype="float32")
        assert isinstance(router.get_backend(arr), ZarrBackend)

    def test_image_routes_to_zarr(self) -> None:
        router = BackendRouter()
        img = Image(shape=(256, 256), ndim=2, dtype="uint8")
        assert isinstance(router.get_backend(img), ZarrBackend)

    def test_dataframe_routes_to_arrow(self) -> None:
        router = BackendRouter()
        df = DataFrame(columns=["a", "b"], row_count=10)
        assert isinstance(router.get_backend(df), ArrowBackend)

    def test_peaktable_routes_to_arrow(self) -> None:
        router = BackendRouter()
        pt = PeakTable(columns=["mz", "rt", "intensity"], row_count=100)
        assert isinstance(router.get_backend(pt), ArrowBackend)

    def test_text_routes_to_filesystem(self) -> None:
        router = BackendRouter()
        txt = Text(content="hello", format="plain")
        assert isinstance(router.get_backend(txt), FilesystemBackend)

    def test_artifact_routes_to_filesystem(self) -> None:
        router = BackendRouter()
        art = Artifact(file_path="/data/report.pdf", mime_type="application/pdf")
        assert isinstance(router.get_backend(art), FilesystemBackend)

    def test_composite_routes_to_composite_store(self) -> None:
        router = BackendRouter()
        cd = CompositeData(slots={"x": Array(shape=(5,), ndim=1, dtype="float32")})
        assert isinstance(router.get_backend(cd), CompositeStore)

    def test_anndata_routes_to_composite_store(self) -> None:
        router = BackendRouter()
        ad = AnnData(
            slots={
                "X": Array(shape=(10, 20), ndim=2, dtype="float32"),
                "obs": DataFrame(columns=["cell_id"], row_count=10),
                "var": DataFrame(columns=["gene_id"], row_count=20),
            }
        )
        assert isinstance(router.get_backend(ad), CompositeStore)


class TestBackendName:
    """get_backend_name returns string identifiers."""

    def test_zarr_name(self) -> None:
        router = BackendRouter()
        arr = Array(shape=(10,), ndim=1, dtype="float32")
        assert router.get_backend_name(arr) == "zarr"

    def test_arrow_name(self) -> None:
        router = BackendRouter()
        df = DataFrame(columns=["a"], row_count=1)
        assert router.get_backend_name(df) == "arrow"

    def test_filesystem_name(self) -> None:
        router = BackendRouter()
        txt = Text(content="hi", format="plain")
        assert router.get_backend_name(txt) == "filesystem"

    def test_composite_name(self) -> None:
        router = BackendRouter()
        cd = CompositeData(slots={"x": Array(shape=(1,), ndim=1, dtype="float32")})
        assert router.get_backend_name(cd) == "composite"


class TestCustomRegistration:
    """Custom type→backend registration."""

    def test_register_overrides_default(self) -> None:
        router = BackendRouter()
        # Register Series → ZarrBackend (Series normally has no route via Array)
        router.register(Series, ZarrBackend)
        s = Series(index_name="wl", value_name="int", length=100)
        assert isinstance(router.get_backend(s), ZarrBackend)


class TestUnknownType:
    """Error on unregistered types."""

    def test_base_dataobject_raises(self) -> None:
        router = BackendRouter()
        obj = DataObject()
        with pytest.raises(TypeError, match="No backend registered"):
            router.get_backend(obj)

    def test_series_unregistered_raises(self) -> None:
        router = BackendRouter()
        s = Series(index_name="wl", value_name="int", length=100)
        with pytest.raises(TypeError, match="No backend registered"):
            router.get_backend(s)
