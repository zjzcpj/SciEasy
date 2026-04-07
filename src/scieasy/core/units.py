# TODO(Phase 10 / T-003): Skeleton only. Implementation per
# docs/specs/phase10-implementation-standards.md
"""PhysicalQuantity — value + unit dataclass for SciEasy metadata.

Implements ADR-027 D6 (PhysicalQuantity) and ADR-027 Addendum 1 §4
(PhysicalQuantity Pydantic v2 integration via
``__get_pydantic_core_schema__``).

The class supports the small set of physical units SciEasy actually needs
(length, time, frequency, wavenumber). Cross-kind conversions are
rejected; same-kind conversions are honoured. Pydantic v2 integration
makes ``pixel_size: PhysicalQuantity`` round-trip transparently as
``{"value": float, "unit": str}`` inside any ``BaseModel``.

This module is a *skeleton*. Method bodies raise ``NotImplementedError``;
the implementation lands in T-003.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# TODO(T-003): ADR-027 D6 — populate the unit tables. Each maps a unit
# string to its scale factor relative to the SI base unit of its kind.
#
# _LENGTH:  m, mm, um, nm, pm, A
# _TIME:    s, ms, us, ns, min, hr
# _FREQ:    Hz, kHz, MHz, GHz
# _WAVENUM: cm-1, m-1
_LENGTH: dict[str, float] = {}
_TIME: dict[str, float] = {}
_FREQ: dict[str, float] = {}
_WAVENUM: dict[str, float] = {}

# TODO(T-003): ADR-027 D6 — derived lookup tables.
# _KIND  maps each unit string to its kind name ("length"/"time"/...).
# _SCALE merges all unit -> scale-factor entries above.
_KIND: dict[str, str] = {}
_SCALE: dict[str, float] = {}


@dataclass(frozen=True)
class PhysicalQuantity:
    """A physical quantity: a numeric value paired with a unit string.

    See ADR-027 D6 for the unit alphabet and conversion rules.
    See ADR-027 Addendum 1 §4 for the Pydantic v2 integration contract.

    The dataclass is frozen so that ``Meta`` Pydantic models containing
    ``PhysicalQuantity`` fields remain immutable in spirit (and so that
    ``with_meta(...)`` semantics on ``DataObject`` remain meaningful).
    """

    value: float
    unit: str

    def __post_init__(self) -> None:
        # TODO(T-003): ADR-027 D6 — validate ``self.unit`` against
        # ``_SCALE``. Raise ``ValueError(f"Unknown unit: {self.unit!r}")``
        # for unknowns. Validation must run on every construction so that
        # malformed metadata fails loudly at object creation time, not at
        # the first conversion attempt.
        raise NotImplementedError("T-003: ADR-027 D6 — unit validation not yet implemented")

    def to(self, target_unit: str) -> PhysicalQuantity:
        """Convert this quantity to ``target_unit`` of the same kind."""
        # TODO(T-003): ADR-027 D6 — convert ``value`` to ``target_unit``.
        # Raise ``ValueError`` if ``_KIND[self.unit] != _KIND[target_unit]``.
        # Return a new ``PhysicalQuantity(scaled_value, target_unit)``.
        raise NotImplementedError("T-003: ADR-027 D6 — to() conversion not yet implemented")

    def __lt__(self, other: PhysicalQuantity) -> bool:
        # TODO(T-003): ADR-027 D6 — value comparison after normalising
        # both sides to their common kind's base unit. Raise ``TypeError``
        # for cross-kind comparisons.
        raise NotImplementedError("T-003: ADR-027 D6 — __lt__ not yet implemented")

    def __eq__(self, other: object) -> bool:
        # TODO(T-003): ADR-027 D6 — value equality after normalising to
        # the common base unit. Use a small epsilon (e.g. 1e-12) for
        # float comparison. Return ``NotImplemented`` for non-PQ inputs;
        # return ``False`` for incompatible kinds (do NOT raise — equality
        # is defined for any pair of objects).
        raise NotImplementedError("T-003: ADR-027 D6 — __eq__ not yet implemented")

    def __hash__(self) -> int:
        # TODO(T-003): ADR-027 D6 — frozen dataclass auto-generates
        # __hash__, but the implementation must be consistent with the
        # custom __eq__ above. Hash on (normalised_value_in_base_unit,
        # _KIND[self.unit]) so that ``Q(1.0, "m") == Q(1000.0, "mm")``
        # implies they hash equal.
        raise NotImplementedError("T-003: ADR-027 D6 — __hash__ not yet implemented")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any:
        """Pydantic v2 integration — ADR-027 Addendum 1 §4.

        Plugin authors writing ``pixel_size: PhysicalQuantity`` get JSON
        round-trip for free. The serialised JSON form is
        ``{"value": float, "unit": str}``. Validation accepts either an
        existing ``PhysicalQuantity`` instance or a dict with the two
        keys.
        """
        # TODO(T-003): ADR-027 Addendum 1 §4 — return a
        # ``pydantic_core.core_schema`` describing:
        #   - validator: dict-or-instance -> PhysicalQuantity
        #   - serializer: PhysicalQuantity -> {"value": ..., "unit": ...}
        # Use ``core_schema.no_info_plain_validator_function`` and
        # ``core_schema.plain_serializer_function_ser_schema`` per the
        # Addendum 1 §4 pseudocode.
        raise NotImplementedError("T-003: ADR-027 Addendum 1 §4 — Pydantic core schema not yet implemented")
