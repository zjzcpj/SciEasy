"""CompositeData type — named collection of heterogeneous DataObject slots."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.core.types.array import Array
from scieasy.core.types.base import DataObject
from scieasy.core.types.dataframe import DataFrame


class CompositeData(DataObject):
    """A named collection of heterogeneous :class:`DataObject` slots.

    Subclasses declare :attr:`expected_slots` as a class variable mapping
    slot names to their expected types.

    Attributes:
        expected_slots: Class-level mapping of slot name to expected type.
    """

    expected_slots: ClassVar[dict[str, type]] = {}

    def __init__(
        self,
        *,
        slots: dict[str, DataObject] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._slots: dict[str, DataObject] = slots or {}

    def get(self, slot_name: str) -> DataObject:
        """Retrieve the :class:`DataObject` stored in *slot_name*."""
        raise NotImplementedError

    def set(self, slot_name: str, data: DataObject) -> None:
        """Store *data* in *slot_name*."""
        raise NotImplementedError

    def slot_types(self) -> dict[str, type]:
        """Return the expected slot-type mapping declared on this class."""
        raise NotImplementedError

    @property
    def slot_names(self) -> list[str]:
        """Return the names of all currently populated slots."""
        raise NotImplementedError


class AnnData(CompositeData):
    """AnnData-like composite: X (array), obs/var (dataframes), uns (artifact)."""

    expected_slots: ClassVar[dict[str, type]] = {
        "X": Array,
        "obs": DataFrame,
        "var": DataFrame,
        # Artifact is imported lazily to avoid a heavier import at class-definition
        # time; the string key is sufficient for Phase 1.
        "uns": DataObject,
    }


class SpatialData(CompositeData):
    """SpatialData-like composite: images, points, shapes, and an AnnData table."""

    expected_slots: ClassVar[dict[str, type]] = {
        "images": Array,
        "points": DataFrame,
        "shapes": DataFrame,
        "table": AnnData,
    }
