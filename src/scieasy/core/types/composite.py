"""CompositeData type — named collection of heterogeneous DataObject slots."""

from __future__ import annotations

from typing import Any, ClassVar

from scieasy.core.types.array import Array
from scieasy.core.types.artifact import Artifact
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
        self._slots: dict[str, DataObject] = {}
        if slots:
            for name, obj in slots.items():
                self.set(name, obj)

    def get(self, slot_name: str) -> DataObject:
        """Retrieve the :class:`DataObject` stored in *slot_name*."""
        if slot_name not in self._slots:
            raise KeyError(f"Slot '{slot_name}' is not populated.")
        return self._slots[slot_name]

    def set(self, slot_name: str, data: DataObject) -> None:
        """Store *data* in *slot_name*, validating against expected_slots if defined."""
        expected = self.slot_types()
        if expected and slot_name in expected:
            expected_type = expected[slot_name]
            if not isinstance(data, expected_type):
                raise TypeError(f"Slot '{slot_name}' expects {expected_type.__name__}, got {type(data).__name__}.")
        self._slots[slot_name] = data

    def slot_types(self) -> dict[str, type]:
        """Return the expected slot-type mapping declared on this class."""
        return dict(self.expected_slots)

    @property
    def slot_names(self) -> list[str]:
        """Return the names of all currently populated slots."""
        return list(self._slots.keys())

    def get_in_memory_data(self) -> Any:
        """Return dict of slot data for composite persistence.

        Each slot value is packaged as ``(backend_name, raw_data)`` for
        :class:`CompositeStore.write`.
        """
        from scieasy.core.storage.backend_router import get_router

        if not self._slots:
            return super().get_in_memory_data()

        router = get_router()
        result: dict[str, tuple[str, Any]] = {}
        for slot_name, slot_obj in self._slots.items():
            backend_name = router.backend_name_for(type(slot_obj))
            slot_data = slot_obj.get_in_memory_data()
            result[slot_name] = (backend_name, slot_data)
        return result


class AnnData(CompositeData):
    """AnnData-like composite: X (array), obs/var (dataframes), uns (artifact)."""

    expected_slots: ClassVar[dict[str, type]] = {
        "X": Array,
        "obs": DataFrame,
        "var": DataFrame,
        "uns": Artifact,
    }


class SpatialData(CompositeData):
    """SpatialData-like composite: images, points, shapes, and an AnnData table."""

    expected_slots: ClassVar[dict[str, type]] = {
        "images": Array,
        "points": DataFrame,
        "shapes": DataFrame,
        "table": AnnData,
    }
