"""Architecture enforcement: type system invariants.

Validates structural properties of the ``scieasy.core.types`` hierarchy:

* Every public class in the type modules inherits from ``DataObject``.
* No class inherits from more than one base-type family simultaneously.
* ``Array`` subclasses declare ``axes``.
* ``CompositeData`` subclasses declare ``expected_slots``.
"""

from __future__ import annotations

import pytest

# TODO(T-008): T-006 removed Image/MSImage/SRSImage/FluorImage from core
# per ADR-027 D2; T-007 additionally removed Spectrum/RamanSpectrum/
# MassSpectrum/PeakTable/MetabPeakTable/AnnData/SpatialData. Alias all
# deleted domain subtypes to their remaining core base classes here so
# this architecture test module still collects; the per-subclass
# invariants here will be rewritten in T-008 to cover only the seven
# remaining base types.
from scieasy.core.types.array import Array
from scieasy.core.types.array import Array as FluorImage
from scieasy.core.types.array import Array as Image
from scieasy.core.types.array import Array as MSImage
from scieasy.core.types.array import Array as SRSImage
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.base import DataObject, TypeSignature
from scieasy.core.types.composite import CompositeData
from scieasy.core.types.composite import CompositeData as AnnData
from scieasy.core.types.composite import CompositeData as SpatialData
from scieasy.core.types.dataframe import DataFrame
from scieasy.core.types.dataframe import DataFrame as MetabPeakTable
from scieasy.core.types.dataframe import DataFrame as PeakTable
from scieasy.core.types.series import Series
from scieasy.core.types.series import Series as MassSpectrum
from scieasy.core.types.series import Series as RamanSpectrum
from scieasy.core.types.series import Series as Spectrum
from scieasy.core.types.text import Text

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Every concrete or intermediate type class defined in the type modules.
# We intentionally exclude TypeSignature (a dataclass, not a DataObject).
ALL_TYPE_CLASSES: list[type] = [
    Array,
    Image,
    MSImage,
    SRSImage,
    FluorImage,
    Series,
    Spectrum,
    RamanSpectrum,
    MassSpectrum,
    DataFrame,
    PeakTable,
    MetabPeakTable,
    Text,
    Artifact,
    CompositeData,
    AnnData,
    SpatialData,
]

# The "base-type families" — direct children of DataObject.  No class should
# inherit from more than one of these.
BASE_TYPE_FAMILIES: list[type] = [
    Array,
    Series,
    DataFrame,
    Text,
    Artifact,
    CompositeData,
]

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cls",
    ALL_TYPE_CLASSES,
    ids=[c.__name__ for c in ALL_TYPE_CLASSES],
)
def test_type_inherits_from_dataobject(cls: type) -> None:
    """Every public type class inherits from DataObject."""
    assert issubclass(cls, DataObject), f"{cls.__name__} does not inherit from DataObject"


def test_no_multi_base_type_inheritance() -> None:
    """No class inherits from more than one base-type family."""
    for cls in ALL_TYPE_CLASSES:
        inherited_families = [family for family in BASE_TYPE_FAMILIES if issubclass(cls, family)]
        # A class may match itself and its parent (e.g. Image -> Array),
        # but the families should all be in a single chain.  We check that
        # the set of matched families forms a single inheritance line: every
        # pair must have an ancestor-descendant relationship.
        for i, fam_a in enumerate(inherited_families):
            for fam_b in inherited_families[i + 1 :]:
                assert issubclass(fam_a, fam_b) or issubclass(fam_b, fam_a), (
                    f"{cls.__name__} inherits from unrelated base families {fam_a.__name__} and {fam_b.__name__}"
                )


# All Array subclasses (direct and indirect) in the codebase.
ARRAY_SUBCLASSES: list[type] = [
    Image,
    MSImage,
    SRSImage,
    FluorImage,
]


@pytest.mark.parametrize(
    "cls",
    ARRAY_SUBCLASSES,
    ids=[c.__name__ for c in ARRAY_SUBCLASSES],
)
def test_array_subtypes_declare_axes(cls: type) -> None:
    """Every concrete Array subclass declares non-None ``axes``."""
    assert issubclass(cls, Array)
    axes = cls.axes
    assert axes is not None, f"{cls.__name__} is an Array subclass but axes is None"
    assert isinstance(axes, list), f"{cls.__name__}.axes should be a list, got {type(axes).__name__}"
    assert len(axes) > 0, f"{cls.__name__}.axes is an empty list"


# All CompositeData subclasses in the codebase.
COMPOSITE_SUBCLASSES: list[type] = [
    AnnData,
    SpatialData,
]


@pytest.mark.parametrize(
    "cls",
    COMPOSITE_SUBCLASSES,
    ids=[c.__name__ for c in COMPOSITE_SUBCLASSES],
)
def test_composite_subtypes_declare_expected_slots(cls: type) -> None:
    """Every CompositeData subclass declares non-empty ``expected_slots``."""
    assert issubclass(cls, CompositeData)
    slots = cls.expected_slots
    assert slots is not None, f"{cls.__name__}.expected_slots is None"
    assert isinstance(slots, dict), f"{cls.__name__}.expected_slots should be a dict, got {type(slots).__name__}"
    assert len(slots) > 0, f"{cls.__name__}.expected_slots is empty"


def test_composite_slot_values_are_dataobject_types() -> None:
    """Every type referenced in ``expected_slots`` is a DataObject subclass."""
    for cls in COMPOSITE_SUBCLASSES:
        for slot_name, slot_type in cls.expected_slots.items():
            assert issubclass(slot_type, DataObject), (
                f"{cls.__name__}.expected_slots['{slot_name}'] = {slot_type.__name__} "
                f"which is not a DataObject subclass"
            )


def test_type_signature_is_not_a_dataobject() -> None:
    """TypeSignature is a metadata descriptor, not a DataObject."""
    assert not issubclass(TypeSignature, DataObject)
