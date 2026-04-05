"""Tests for DataObject types, TypeSignature, and TypeRegistry (Phase 3.1)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from scieasy.core.types.array import Array, FluorImage, Image, MSImage, SRSImage
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.base import DataObject, TypeSignature
from scieasy.core.types.composite import AnnData, CompositeData, SpatialData
from scieasy.core.types.dataframe import DataFrame, MetabPeakTable, PeakTable
from scieasy.core.types.registry import TypeRegistry, TypeSpec
from scieasy.core.types.series import MassSpectrum, RamanSpectrum, Series, Spectrum
from scieasy.core.types.text import Text

# ---------------------------------------------------------------------------
# TypeSignature.from_type
# ---------------------------------------------------------------------------


class TestTypeSignatureFromType:
    """Verify auto-generation of TypeSignature from class MRO."""

    def test_data_object(self) -> None:
        sig = TypeSignature.from_type(DataObject)
        assert sig.type_chain == ["DataObject"]

    def test_array(self) -> None:
        sig = TypeSignature.from_type(Array)
        assert sig.type_chain == ["DataObject", "Array"]

    def test_image(self) -> None:
        sig = TypeSignature.from_type(Image)
        assert sig.type_chain == ["DataObject", "Array", "Image"]

    def test_ms_image(self) -> None:
        sig = TypeSignature.from_type(MSImage)
        assert sig.type_chain == ["DataObject", "Array", "MSImage"]

    def test_srs_image(self) -> None:
        sig = TypeSignature.from_type(SRSImage)
        assert sig.type_chain == ["DataObject", "Array", "Image", "SRSImage"]

    def test_fluor_image(self) -> None:
        sig = TypeSignature.from_type(FluorImage)
        assert sig.type_chain == ["DataObject", "Array", "Image", "FluorImage"]

    def test_series(self) -> None:
        sig = TypeSignature.from_type(Series)
        assert sig.type_chain == ["DataObject", "Series"]

    def test_spectrum(self) -> None:
        sig = TypeSignature.from_type(Spectrum)
        assert sig.type_chain == ["DataObject", "Series", "Spectrum"]

    def test_raman_spectrum(self) -> None:
        sig = TypeSignature.from_type(RamanSpectrum)
        assert sig.type_chain == ["DataObject", "Series", "Spectrum", "RamanSpectrum"]

    def test_mass_spectrum(self) -> None:
        sig = TypeSignature.from_type(MassSpectrum)
        assert sig.type_chain == ["DataObject", "Series", "Spectrum", "MassSpectrum"]

    def test_dataframe(self) -> None:
        sig = TypeSignature.from_type(DataFrame)
        assert sig.type_chain == ["DataObject", "DataFrame"]

    def test_peak_table(self) -> None:
        sig = TypeSignature.from_type(PeakTable)
        assert sig.type_chain == ["DataObject", "DataFrame", "PeakTable"]

    def test_metab_peak_table(self) -> None:
        sig = TypeSignature.from_type(MetabPeakTable)
        assert sig.type_chain == ["DataObject", "DataFrame", "PeakTable", "MetabPeakTable"]

    def test_text(self) -> None:
        sig = TypeSignature.from_type(Text)
        assert sig.type_chain == ["DataObject", "Text"]

    def test_artifact(self) -> None:
        sig = TypeSignature.from_type(Artifact)
        assert sig.type_chain == ["DataObject", "Artifact"]

    def test_composite(self) -> None:
        sig = TypeSignature.from_type(CompositeData)
        assert sig.type_chain == ["DataObject", "CompositeData"]

    def test_anndata(self) -> None:
        sig = TypeSignature.from_type(AnnData)
        assert sig.type_chain == ["DataObject", "CompositeData", "AnnData"]
        assert sig.slot_schema is not None
        assert "X" in sig.slot_schema

    def test_spatial_data(self) -> None:
        sig = TypeSignature.from_type(SpatialData)
        assert sig.type_chain == ["DataObject", "CompositeData", "SpatialData"]
        assert sig.slot_schema is not None
        assert "table" in sig.slot_schema


# ---------------------------------------------------------------------------
# TypeSignature.matches
# ---------------------------------------------------------------------------


class TestTypeSignatureMatches:
    """Verify inheritance-aware type matching."""

    def test_exact_match(self) -> None:
        sig_image = TypeSignature.from_type(Image)
        sig_image2 = TypeSignature.from_type(Image)
        assert sig_image.matches(sig_image2)

    def test_subtype_matches_parent(self) -> None:
        sig_image = TypeSignature.from_type(Image)
        sig_array = TypeSignature.from_type(Array)
        # Image matches a port accepting Array
        assert sig_image.matches(sig_array)

    def test_parent_does_not_match_subtype(self) -> None:
        sig_array = TypeSignature.from_type(Array)
        sig_image = TypeSignature.from_type(Image)
        # Array does NOT match a port requiring Image
        assert not sig_array.matches(sig_image)

    def test_unrelated_types_no_match(self) -> None:
        sig_image = TypeSignature.from_type(Image)
        sig_series = TypeSignature.from_type(Series)
        assert not sig_image.matches(sig_series)

    def test_deep_subtype_matches_root(self) -> None:
        sig_raman = TypeSignature.from_type(RamanSpectrum)
        sig_data = TypeSignature.from_type(DataObject)
        assert sig_raman.matches(sig_data)

    def test_matches_self(self) -> None:
        sig = TypeSignature.from_type(PeakTable)
        assert sig.matches(sig)


# ---------------------------------------------------------------------------
# DataObject.dtype_info property
# ---------------------------------------------------------------------------


class TestDataObjectDtypeInfo:
    """Verify dtype_info auto-generation on instances."""

    def test_array_dtype_info(self) -> None:
        arr = Array(shape=(10, 10), dtype="float64")
        assert arr.dtype_info.type_chain == ["DataObject", "Array"]

    def test_image_dtype_info(self) -> None:
        img = Image(shape=(1024, 1024), dtype="uint8")
        assert img.dtype_info.type_chain == ["DataObject", "Array", "Image"]

    def test_text_dtype_info(self) -> None:
        txt = Text(content="hello")
        assert txt.dtype_info.type_chain == ["DataObject", "Text"]

    def test_artifact_dtype_info(self) -> None:
        art = Artifact(mime_type="application/pdf")
        assert art.dtype_info.type_chain == ["DataObject", "Artifact"]


# ---------------------------------------------------------------------------
# DataObject metadata
# ---------------------------------------------------------------------------


class TestDataObjectMetadata:
    """Verify metadata handling."""

    def test_default_metadata_empty(self) -> None:
        obj = DataObject()
        assert obj.metadata == {}

    def test_custom_metadata(self) -> None:
        obj = DataObject(metadata={"source": "test", "units": "nm"})
        assert obj.metadata["source"] == "test"
        assert obj.metadata["units"] == "nm"


# ---------------------------------------------------------------------------
# DataObject.view raises without storage_ref
# ---------------------------------------------------------------------------


class TestDataObjectView:
    """Verify view() requires a storage reference."""

    def test_view_without_ref_raises(self) -> None:
        obj = DataObject()
        with pytest.raises(ValueError, match="storage reference"):
            obj.view()


# ---------------------------------------------------------------------------
# TypeRegistry
# ---------------------------------------------------------------------------


class TestTypeRegistry:
    """Verify TypeRegistry registration, lookup, and scanning."""

    def test_register_and_resolve(self) -> None:
        registry = TypeRegistry()
        spec = TypeSpec(name="Image", module_path="scieasy.core.types.array", class_name="Image")
        registry.register("Image", spec)
        resolved = registry.resolve("Image")
        assert resolved.name == "Image"

    def test_resolve_missing_raises(self) -> None:
        registry = TypeRegistry()
        with pytest.raises(KeyError, match="not registered"):
            registry.resolve("Nonexistent")

    def test_all_types(self) -> None:
        registry = TypeRegistry()
        spec = TypeSpec(name="A", module_path="m", class_name="A")
        registry.register("A", spec)
        all_t = registry.all_types()
        assert "A" in all_t
        # Returns a copy
        all_t["B"] = spec
        assert "B" not in registry.all_types()

    def test_scan_builtins(self) -> None:
        registry = TypeRegistry()
        registry.scan_builtins()
        all_t = registry.all_types()
        assert "Image" in all_t
        assert "Spectrum" in all_t
        assert "DataFrame" in all_t
        assert "AnnData" in all_t
        assert len(all_t) >= 18  # All 18 built-in types

    def test_load_class(self) -> None:
        registry = TypeRegistry()
        registry.scan_builtins()
        cls = registry.load_class("Image")
        assert cls is Image

    def test_is_instance(self) -> None:
        registry = TypeRegistry()
        registry.scan_builtins()
        img = Image(shape=(10, 10))
        assert registry.is_instance(img, "Image")
        assert registry.is_instance(img, "Array")
        assert registry.is_instance(img, "DataObject")
        assert not registry.is_instance(img, "Series")


# ---------------------------------------------------------------------------
# TypeSignature slot_schema comparison
# ---------------------------------------------------------------------------


class TestTypeSignatureSlotSchema:
    """Verify slot_schema comparison in TypeSignature.matches()."""

    def test_matching_slot_schema(self) -> None:
        sig_a = TypeSignature(
            type_chain=["DataObject", "CompositeData", "AnnData"],
            slot_schema={"X": "Array", "obs": "DataFrame", "var": "DataFrame", "uns": "Artifact"},
        )
        sig_b = TypeSignature(
            type_chain=["DataObject", "CompositeData"],
            slot_schema={"X": "Array", "obs": "DataFrame"},
        )
        assert sig_a.matches(sig_b)

    def test_mismatched_slot_type_rejects(self) -> None:
        sig_a = TypeSignature(
            type_chain=["DataObject", "CompositeData", "AnnData"],
            slot_schema={"X": "Array", "obs": "DataFrame", "var": "DataFrame", "uns": "Artifact"},
        )
        sig_b = TypeSignature(
            type_chain=["DataObject", "CompositeData"],
            slot_schema={"X": "DataFrame"},
        )
        assert not sig_a.matches(sig_b)

    def test_missing_slot_rejects(self) -> None:
        sig_a = TypeSignature(
            type_chain=["DataObject", "CompositeData"],
            slot_schema={"X": "Array"},
        )
        sig_b = TypeSignature(
            type_chain=["DataObject", "CompositeData"],
            slot_schema={"X": "Array", "Y": "DataFrame"},
        )
        assert not sig_a.matches(sig_b)

    def test_no_slot_schema_on_other_passes(self) -> None:
        sig_a = TypeSignature(
            type_chain=["DataObject", "CompositeData", "AnnData"],
            slot_schema={"X": "Array"},
        )
        sig_b = TypeSignature(type_chain=["DataObject", "CompositeData"])
        assert sig_a.matches(sig_b)

    def test_slot_schema_on_other_but_not_self_rejects(self) -> None:
        sig_a = TypeSignature(type_chain=["DataObject", "CompositeData"])
        sig_b = TypeSignature(
            type_chain=["DataObject", "CompositeData"],
            slot_schema={"X": "Array"},
        )
        assert not sig_a.matches(sig_b)


# ---------------------------------------------------------------------------
# Array.__array__() protocol
# ---------------------------------------------------------------------------


class TestArrayProtocol:
    """Verify Array.__array__() supports np.asarray()."""

    def test_array_protocol_with_storage(self, tmp_path: Path) -> None:
        """Array.__array__() materialises data via storage reference."""
        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.storage.zarr_backend import ZarrBackend

        backend = ZarrBackend()
        data = np.array([[1, 2], [3, 4]], dtype=np.float32)
        ref = StorageReference(backend="zarr", path=str(tmp_path / "test.zarr"))
        backend.write(data, ref)

        arr = Array(shape=(2, 2), dtype="float32", storage_ref=ref)

        result = np.asarray(arr)
        np.testing.assert_array_equal(result, data)

    def test_array_protocol_dtype_conversion(self, tmp_path: Path) -> None:
        """Array.__array__() respects dtype parameter."""
        from scieasy.core.storage.ref import StorageReference
        from scieasy.core.storage.zarr_backend import ZarrBackend

        backend = ZarrBackend()
        data = np.array([[1, 2], [3, 4]], dtype=np.float32)
        ref = StorageReference(backend="zarr", path=str(tmp_path / "test.zarr"))
        backend.write(data, ref)

        arr = Array(shape=(2, 2), dtype="float32", storage_ref=ref)

        result = np.asarray(arr, dtype=np.float64)
        assert result.dtype == np.float64
        np.testing.assert_array_equal(result, data.astype(np.float64))

    def test_array_protocol_without_storage_raises(self) -> None:
        """Array.__array__() raises when no storage reference is set."""
        arr = Array(shape=(2, 2), dtype="float32")
        with pytest.raises(ValueError, match="storage reference"):
            np.asarray(arr)
