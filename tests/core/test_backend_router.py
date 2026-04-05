"""Tests for BackendRouter — type-to-backend MRO resolution."""

from __future__ import annotations

import pytest

from scieasy.core.storage.backend_router import BackendRouter, get_router
from scieasy.core.storage.zarr_backend import ZarrBackend
from scieasy.core.types.array import Array, Image


class TestResolveDirectType:
    """BackendRouter.resolve — direct type lookup."""

    def test_resolve_direct_type(self) -> None:
        router = get_router()
        name, backend = router.resolve(Array)
        assert name == "zarr"
        assert isinstance(backend, ZarrBackend)


class TestResolveSubclassViaMRO:
    """BackendRouter.resolve — subclass falls back to ancestor via MRO."""

    def test_resolve_subclass_via_mro(self) -> None:
        router = get_router()
        name, backend = router.resolve(Image)
        assert name == "zarr"
        assert isinstance(backend, ZarrBackend)


class TestResolveUnregisteredRaises:
    """BackendRouter.resolve — unregistered type raises KeyError."""

    def test_resolve_unregistered_raises(self) -> None:
        router = BackendRouter()
        with pytest.raises(KeyError, match="No storage backend registered"):
            router.resolve(int)


class TestDefaultRouterCoverage:
    """get_router() has all 6 core types registered."""

    def test_default_router_coverage(self) -> None:
        from scieasy.core.types.artifact import Artifact
        from scieasy.core.types.composite import CompositeData
        from scieasy.core.types.dataframe import DataFrame
        from scieasy.core.types.series import Series
        from scieasy.core.types.text import Text

        router = get_router()
        for data_type in [Array, Series, DataFrame, Text, Artifact, CompositeData]:
            name, backend = router.resolve(data_type)
            assert isinstance(name, str)
            assert backend is not None


class TestExtensionFor:
    """BackendRouter.extension_for — correct file extensions."""

    def test_extension_for_array(self) -> None:
        router = get_router()
        assert router.extension_for(Array) == ".zarr"

    def test_extension_for_dataframe(self) -> None:
        from scieasy.core.types.dataframe import DataFrame

        router = get_router()
        assert router.extension_for(DataFrame) == ".parquet"

    def test_extension_for_text(self) -> None:
        from scieasy.core.types.text import Text

        router = get_router()
        assert router.extension_for(Text) == ".txt"

    def test_extension_for_composite(self) -> None:
        from scieasy.core.types.composite import CompositeData

        router = get_router()
        assert router.extension_for(CompositeData) == ""


class TestBackendNameFor:
    """BackendRouter.backend_name_for — correct backend name strings."""

    def test_backend_name_for_array(self) -> None:
        router = get_router()
        assert router.backend_name_for(Array) == "zarr"

    def test_backend_name_for_dataframe(self) -> None:
        from scieasy.core.types.dataframe import DataFrame

        router = get_router()
        assert router.backend_name_for(DataFrame) == "arrow"

    def test_backend_name_for_text(self) -> None:
        from scieasy.core.types.text import Text

        router = get_router()
        assert router.backend_name_for(Text) == "filesystem"


class TestSingletonIdentity:
    """get_router() returns the same instance on repeated calls."""

    def test_singleton_identity(self) -> None:
        r1 = get_router()
        r2 = get_router()
        assert r1 is r2
