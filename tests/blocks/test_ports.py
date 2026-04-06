"""Tests for port type matching, constraint validation, and connection checking."""

from __future__ import annotations

from scieasy.blocks.base.ports import (
    InputPort,
    OutputPort,
    port_accepts_signature,
    port_accepts_type,
    validate_connection,
    validate_port_constraint,
)

# TODO(T-008): full Image → Array migration. T-006 removed the core
# Image class; this shim preserves the old import surface so the block
# port tests still collect and run until T-008 lands the real migration.
from scieasy.core.types.array import Array
from scieasy.core.types.array import Array as Image
from scieasy.core.types.base import DataObject, TypeSignature
from scieasy.core.types.composite import AnnData, CompositeData
from scieasy.core.types.dataframe import DataFrame, PeakTable
from scieasy.core.types.series import Series, Spectrum


class TestPortAcceptsType:
    """port_accepts_type — isinstance-based, inheritance-aware matching."""

    def test_exact_match(self) -> None:
        port = InputPort(name="in", accepted_types=[Array])
        assert port_accepts_type(port, Array)

    def test_subtype_accepted(self) -> None:
        port = InputPort(name="in", accepted_types=[Array])
        assert port_accepts_type(port, Image)

    def test_unrelated_rejected(self) -> None:
        port = InputPort(name="in", accepted_types=[Array])
        assert not port_accepts_type(port, DataFrame)

    def test_empty_accepts_anything(self) -> None:
        port = InputPort(name="in", accepted_types=[])
        assert port_accepts_type(port, DataFrame)
        assert port_accepts_type(port, Image)

    def test_multiple_accepted_types(self) -> None:
        port = InputPort(name="in", accepted_types=[Array, DataFrame])
        assert port_accepts_type(port, Image)
        assert port_accepts_type(port, PeakTable)
        assert not port_accepts_type(port, Series)

    def test_dataobject_accepts_all(self) -> None:
        port = InputPort(name="in", accepted_types=[DataObject])
        assert port_accepts_type(port, Image)
        assert port_accepts_type(port, DataFrame)
        assert port_accepts_type(port, Spectrum)


class TestPortAcceptsSignature:
    """port_accepts_signature — TypeSignature matching."""

    def test_exact_signature(self) -> None:
        port = InputPort(name="in", accepted_types=[Array])
        sig = TypeSignature.from_type(Array)
        assert port_accepts_signature(port, sig)

    def test_subtype_signature(self) -> None:
        port = InputPort(name="in", accepted_types=[Array])
        sig = TypeSignature.from_type(Image)
        assert port_accepts_signature(port, sig)

    def test_incompatible_signature(self) -> None:
        port = InputPort(name="in", accepted_types=[Array])
        sig = TypeSignature.from_type(DataFrame)
        assert not port_accepts_signature(port, sig)

    def test_empty_accepts_all_signatures(self) -> None:
        port = InputPort(name="in", accepted_types=[])
        sig = TypeSignature.from_type(DataFrame)
        assert port_accepts_signature(port, sig)

    def test_composite_slot_constraint(self) -> None:
        """CompositeData subtype's signature is accepted by CompositeData port."""
        port = InputPort(name="in", accepted_types=[CompositeData])
        sig = TypeSignature.from_type(AnnData)
        assert port_accepts_signature(port, sig)


class TestValidatePortConstraint:
    """validate_port_constraint — constraint function checking."""

    def test_no_constraint_passes(self) -> None:
        port = InputPort(name="in", accepted_types=[])
        ok, desc = validate_port_constraint(port, "anything")
        assert ok
        assert desc == ""

    def test_constraint_passes(self) -> None:
        port = InputPort(
            name="in",
            accepted_types=[],
            constraint=lambda v: v > 0,
            constraint_description="Must be positive",
        )
        ok, _desc = validate_port_constraint(port, 5)
        assert ok

    def test_constraint_fails(self) -> None:
        port = InputPort(
            name="in",
            accepted_types=[],
            constraint=lambda v: v > 0,
            constraint_description="Must be positive",
        )
        ok, desc = validate_port_constraint(port, -1)
        assert not ok
        assert "Must be positive" in desc

    def test_constraint_exception(self) -> None:
        port = InputPort(
            name="in",
            accepted_types=[],
            constraint=lambda v: v.nonexistent_attr,
        )
        ok, desc = validate_port_constraint(port, 42)
        assert not ok
        assert "AttributeError" in desc


class TestValidateConnection:
    """validate_connection — source port -> target port compatibility."""

    def test_compatible(self) -> None:
        src = OutputPort(name="out", accepted_types=[Image])
        tgt = InputPort(name="in", accepted_types=[Array])
        ok, _reason = validate_connection(src, tgt)
        assert ok

    def test_incompatible(self) -> None:
        src = OutputPort(name="out", accepted_types=[DataFrame])
        tgt = InputPort(name="in", accepted_types=[Array])
        ok, reason = validate_connection(src, tgt)
        assert not ok
        assert "DataFrame" in reason
        assert "Array" in reason

    def test_empty_source_always_compatible(self) -> None:
        src = OutputPort(name="out", accepted_types=[])
        tgt = InputPort(name="in", accepted_types=[Array])
        ok, _ = validate_connection(src, tgt)
        assert ok

    def test_empty_target_always_compatible(self) -> None:
        src = OutputPort(name="out", accepted_types=[DataFrame])
        tgt = InputPort(name="in", accepted_types=[])
        ok, _ = validate_connection(src, tgt)
        assert ok

    def test_subtype_in_multi_type_port(self) -> None:
        src = OutputPort(name="out", accepted_types=[PeakTable])
        tgt = InputPort(name="in", accepted_types=[Array, DataFrame])
        ok, _ = validate_connection(src, tgt)
        assert ok


class TestCollectionTransparency:
    """ADR-020: Collection-transparent type checking."""

    def test_collection_image_matches_image_port(self) -> None:
        """Collection[Image] should be accepted by a port accepting Image."""
        from scieasy.core.types.array import Array as Image  # T-008
        from scieasy.core.types.collection import Collection

        port = InputPort(name="in", accepted_types=[Image])
        img = Image(shape=(5, 5), ndim=2, dtype="uint8")
        c = Collection([img])
        # Collection-transparent: checks item_type
        assert port_accepts_type(port, c)

    def test_collection_dataframe_rejected_by_image_port(self) -> None:
        """ADR-020-Add6: Collection[DataFrame] should NOT match Image port."""
        from scieasy.core.types.collection import Collection
        from scieasy.core.types.dataframe import DataFrame

        port = InputPort(name="in", accepted_types=[Image])
        df = DataFrame(columns=["a"], row_count=1)
        c = Collection([df])
        assert not port_accepts_type(port, c)

    def test_collection_subtype_matches(self) -> None:
        """Collection[Image] (subtype of Array) should match Array port."""
        from scieasy.core.types.array import Array as Image  # T-008
        from scieasy.core.types.collection import Collection

        port = InputPort(name="in", accepted_types=[Array])
        img = Image(shape=(5, 5), ndim=2, dtype="uint8")
        c = Collection([img])
        assert port_accepts_type(port, c)

    def test_collection_type_object_does_not_match(self) -> None:
        """Issue #129: passing type(collection) instead of instance fails.

        This documents the old bug — Block.validate() was calling
        port_accepts_type(port, type(value)) which passes the Collection
        *class*, not a Collection *instance*. The isinstance check in
        port_accepts_type() correctly requires an instance.
        """
        from scieasy.core.types.collection import Collection

        port = InputPort(name="in", accepted_types=[Image])
        img = Image(shape=(5, 5), ndim=2, dtype="uint8")
        c = Collection([img])
        # type(c) is the Collection class, not a Collection instance
        # This should NOT match — Collection class is not a subclass of Image
        assert not port_accepts_type(port, type(c))
