"""Tests for CompositeData slot access and nested composites (Phase 3.1)."""

from __future__ import annotations

import pytest

from scieasy.core.types.array import Array, Image
from scieasy.core.types.base import DataObject
from scieasy.core.types.composite import AnnData, CompositeData, SpatialData
from scieasy.core.types.dataframe import DataFrame


class TestCompositeDataSlotAccess:
    """Verify get, set, slot_types, and slot_names."""

    def test_set_and_get(self) -> None:
        comp = CompositeData()
        obj = DataObject(metadata={"test": True})
        comp.set("my_slot", obj)
        assert comp.get("my_slot") is obj

    def test_get_missing_raises(self) -> None:
        comp = CompositeData()
        with pytest.raises(KeyError, match="not populated"):
            comp.get("nonexistent")

    def test_slot_names_empty(self) -> None:
        comp = CompositeData()
        assert comp.slot_names == []

    def test_slot_names_populated(self) -> None:
        comp = CompositeData()
        comp.set("a", DataObject())
        comp.set("b", DataObject())
        assert sorted(comp.slot_names) == ["a", "b"]

    def test_slot_types_base_empty(self) -> None:
        comp = CompositeData()
        assert comp.slot_types() == {}

    def test_init_with_slots(self) -> None:
        obj_a = DataObject()
        obj_b = DataObject()
        comp = CompositeData(slots={"a": obj_a, "b": obj_b})
        assert comp.get("a") is obj_a
        assert comp.get("b") is obj_b


class TestAnnDataSlots:
    """Verify AnnData expected_slots and type validation."""

    def test_slot_types(self) -> None:
        ad = AnnData()
        types = ad.slot_types()
        assert "X" in types
        assert types["X"] is Array
        assert types["obs"] is DataFrame
        assert types["var"] is DataFrame

    def test_set_valid_slot(self) -> None:
        ad = AnnData()
        x = Array(shape=(100, 50), dtype="float64")
        obs = DataFrame(columns=["cell_type"], row_count=100)
        ad.set("X", x)
        ad.set("obs", obs)
        assert ad.get("X") is x
        assert ad.get("obs") is obs

    def test_set_invalid_type_raises(self) -> None:
        ad = AnnData()
        wrong = DataFrame(columns=["a"])  # Not an Array
        with pytest.raises(TypeError, match="expects Array"):
            ad.set("X", wrong)

    def test_set_subtype_accepted(self) -> None:
        """Image is a subtype of Array, so it should be accepted for X."""
        ad = AnnData()
        img = Image(shape=(100, 100))
        ad.set("X", img)
        assert ad.get("X") is img

    def test_dtype_info_slot_schema(self) -> None:
        ad = AnnData()
        sig = ad.dtype_info
        assert sig.slot_schema is not None
        assert "X" in sig.slot_schema
        assert sig.slot_schema["X"] == "Array"


class TestSpatialDataSlots:
    """Verify SpatialData expected_slots."""

    def test_slot_types(self) -> None:
        sd = SpatialData()
        types = sd.slot_types()
        assert "images" in types
        assert "points" in types
        assert "table" in types
        assert types["table"] is AnnData

    def test_set_anndata_in_table_slot(self) -> None:
        sd = SpatialData()
        ad = AnnData()
        sd.set("table", ad)
        assert sd.get("table") is ad


class TestNestedComposites:
    """Verify nested composites: SpatialData containing AnnData."""

    def test_nested_access(self) -> None:
        ad = AnnData()
        x = Array(shape=(100, 50), dtype="float64")
        obs = DataFrame(columns=["cell_type"], row_count=100)
        ad.set("X", x)
        ad.set("obs", obs)

        sd = SpatialData()
        images = Array(shape=(1024, 1024, 3))
        points = DataFrame(columns=["x", "y", "z"])
        sd.set("images", images)
        sd.set("points", points)
        sd.set("table", ad)

        # Accessing nested: SpatialData -> table -> X
        inner_ad = sd.get("table")
        assert isinstance(inner_ad, AnnData)
        inner_x = inner_ad.get("X")
        assert inner_x is x
        assert inner_x.shape == (100, 50)

    def test_nested_dtype_info(self) -> None:
        sd = SpatialData()
        sig = sd.dtype_info
        assert sig.type_chain == ["DataObject", "CompositeData", "SpatialData"]
        assert sig.slot_schema is not None
        assert sig.slot_schema["table"] == "AnnData"
