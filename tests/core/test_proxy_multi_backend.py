"""Tests for ViewProxy with Arrow, Filesystem backends, and backend dispatch."""

from __future__ import annotations

import warnings

import numpy as np
import pyarrow as pa
import pytest

from scieasy.core.proxy import ViewProxy, _get_backend
from scieasy.core.storage.arrow_backend import ArrowBackend
from scieasy.core.storage.filesystem import FilesystemBackend
from scieasy.core.storage.ref import StorageReference
from scieasy.core.types.base import TypeSignature


class TestGetBackendDispatch:
    """_get_backend — resolves backend string to instance."""

    def test_unknown_backend_raises(self) -> None:
        ref = StorageReference(backend="nonexistent", path="/tmp/fake")
        with pytest.raises(ValueError, match="Unknown backend"):
            _get_backend(ref)

    def test_zarr_backend_resolves(self) -> None:
        from scieasy.core.storage.zarr_backend import ZarrBackend

        ref = StorageReference(backend="zarr", path="/tmp/fake")
        assert isinstance(_get_backend(ref), ZarrBackend)

    def test_arrow_backend_resolves(self) -> None:
        ref = StorageReference(backend="arrow", path="/tmp/fake")
        assert isinstance(_get_backend(ref), ArrowBackend)

    def test_filesystem_backend_resolves(self) -> None:
        ref = StorageReference(backend="filesystem", path="/tmp/fake")
        assert isinstance(_get_backend(ref), FilesystemBackend)

    def test_composite_backend_resolves(self) -> None:
        from scieasy.core.storage.composite_store import CompositeStore

        ref = StorageReference(backend="composite", path="/tmp/fake")
        assert isinstance(_get_backend(ref), CompositeStore)


class TestViewProxyArrow:
    """ViewProxy backed by ArrowBackend."""

    @pytest.fixture()
    def arrow_proxy(self, tmp_path: pytest.TempPathFactory) -> ViewProxy:
        table = pa.table({"x": [1, 2, 3], "y": [4, 5, 6]})
        path = str(tmp_path / "data.parquet")  # type: ignore[operator]
        backend = ArrowBackend()
        ref = StorageReference(backend="arrow", path=path, format="parquet")
        ref = backend.write(table, ref)
        sig = TypeSignature(type_chain=["DataObject", "DataFrame"])
        return ViewProxy(storage_ref=ref, dtype_info=sig)

    def test_to_memory_returns_table(self, arrow_proxy: ViewProxy) -> None:
        result = arrow_proxy.to_memory()
        assert isinstance(result, pa.Table)
        assert result.num_rows == 3

    def test_slice_columns(self, arrow_proxy: ViewProxy) -> None:
        result = arrow_proxy.slice(["x"])
        assert isinstance(result, pa.Table)
        assert result.column_names == ["x"]

    def test_iter_chunks(self, arrow_proxy: ViewProxy) -> None:
        chunks = list(arrow_proxy.iter_chunks(2))
        assert len(chunks) >= 1

    def test_shape_returns_none_for_arrow(self, arrow_proxy: ViewProxy) -> None:
        assert arrow_proxy.shape is None


class TestViewProxyFilesystem:
    """ViewProxy backed by FilesystemBackend."""

    @pytest.fixture()
    def text_proxy(self, tmp_path: pytest.TempPathFactory) -> ViewProxy:
        backend = FilesystemBackend()
        ref = StorageReference(backend="filesystem", path=str(tmp_path / "data.txt"), format="plain")  # type: ignore[operator]
        backend.write("Hello, world!", ref)
        sig = TypeSignature(type_chain=["DataObject", "Text"])
        return ViewProxy(storage_ref=ref, dtype_info=sig)

    @pytest.fixture()
    def binary_proxy(self, tmp_path: pytest.TempPathFactory) -> ViewProxy:
        backend = FilesystemBackend()
        ref = StorageReference(backend="filesystem", path=str(tmp_path / "data.bin"), format="binary")  # type: ignore[operator]
        backend.write(b"\x00\x01\x02\x03\x04\x05\x06\x07", ref)
        sig = TypeSignature(type_chain=["DataObject", "Artifact"])
        return ViewProxy(storage_ref=ref, dtype_info=sig)

    def test_to_memory_text(self, text_proxy: ViewProxy) -> None:
        result = text_proxy.to_memory()
        assert result == "Hello, world!"

    def test_to_memory_binary(self, binary_proxy: ViewProxy) -> None:
        result = binary_proxy.to_memory()
        assert result == b"\x00\x01\x02\x03\x04\x05\x06\x07"

    def test_slice_bytes(self, binary_proxy: ViewProxy) -> None:
        result = binary_proxy.slice(0, 4)
        assert result == b"\x00\x01\x02\x03"


class TestViewProxySizeWarning:
    """ViewProxy.to_memory — large data warning."""

    def test_large_data_emits_warning(self, tmp_path: pytest.TempPathFactory) -> None:
        """Zarr array with metadata reporting >2GB should trigger ResourceWarning."""
        arr = np.zeros((10, 10), dtype=np.float64)
        from scieasy.core.storage.zarr_backend import ZarrBackend

        backend = ZarrBackend()
        ref = StorageReference(backend="zarr", path=str(tmp_path / "big.zarr"))  # type: ignore[operator]
        ref = backend.write(arr, ref)

        # Manually set shape in metadata to simulate a huge array
        # The proxy estimates size as prod(shape) * 8
        huge_shape = (50000, 50000)  # 50000*50000*8 = 20 GB
        sig = TypeSignature(type_chain=["DataObject", "Array"])
        proxy = ViewProxy(storage_ref=ref, dtype_info=sig)
        # Inject a fake metadata cache to trigger the warning
        proxy._metadata_cache = {"shape": huge_shape}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            proxy.to_memory()
            resource_warnings = [x for x in w if issubclass(x.category, ResourceWarning)]
            assert len(resource_warnings) >= 1
            assert "GB" in str(resource_warnings[0].message)
