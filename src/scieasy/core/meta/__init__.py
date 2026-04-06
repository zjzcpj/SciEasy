# TODO(Phase 10 / T-004): Skeleton only. Implementation per
# docs/specs/phase10-implementation-standards.md
"""scieasy.core.meta — stratified metadata primitives.

Public surface for ADR-027 D5's three-slot metadata model
(``framework`` / ``meta`` / ``user``).

This package re-exports:

- ``FrameworkMeta`` — immutable framework-managed metadata
  (see ``framework.py`` and ADR-027 D5).
- ``with_meta`` — immutable update helper for ``DataObject.meta``.
- ``ChannelInfo`` — small Pydantic model used by imaging plugin
  ``Meta`` classes; lives here so all plugins can compose it without
  importing from another plugin (per ADR-027 §"New files" — the
  ``scieasy.core.meta`` module is the public home for shared
  metadata primitives).

Implementation lands in T-004 (FrameworkMeta + ChannelInfo skeleton
fleshed out) and T-005 (DataObject side of with_meta plumbing).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scieasy.core.meta.framework import FrameworkMeta

if TYPE_CHECKING:
    from scieasy.core.types.base import DataObject


# TODO(T-004): ADR-027 D5 — define ChannelInfo as a small frozen
# pydantic.BaseModel with fields:
#
#   name:           str
#   excitation_nm:  float | None = None
#   emission_nm:    float | None = None
#   color:          str | None = None
#
# It is shared by every imaging-style plugin Meta that needs a
# ``channels: list[ChannelInfo]`` field. Living in core.meta keeps the
# core/plugin import direction clean (no plugin -> plugin imports).
class ChannelInfo:
    """Lightweight channel descriptor used by imaging plugin Meta classes.

    Skeleton placeholder. T-004 will replace this with a frozen
    ``pydantic.BaseModel`` per the field list in the TODO above.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # TODO(T-004): ADR-027 D5 — replace this entire class with a
        # frozen pydantic.BaseModel. The current placeholder exists only
        # so that ``from scieasy.core.meta import ChannelInfo`` does not
        # raise ImportError during the skeleton phase.
        raise NotImplementedError("T-004: ADR-027 D5 — ChannelInfo not yet implemented")


def with_meta(obj: DataObject, **changes: Any) -> DataObject:
    """Return a new DataObject with selected meta fields changed.

    See ADR-027 D5 for the propagation rule. Other slots
    (``framework``, ``user``, ``storage_ref``, geometry) are preserved.
    The ``meta`` slot is replaced with ``obj.meta.model_copy(update=changes)``,
    which honours the Pydantic frozen contract by producing a new model
    instance rather than mutating in place.

    This is a free function in addition to ``DataObject.with_meta(...)``
    method form so that callers who already hold a typed instance can
    use either style.
    """
    # TODO(T-004): ADR-027 D5 — implement with_meta() helper. The bulk
    # of the immutable-update logic lives on DataObject (added in T-005);
    # this helper is a thin wrapper that calls obj.with_meta(**changes).
    raise NotImplementedError("T-004: ADR-027 D5 — with_meta() helper not yet implemented")


__all__ = [
    "ChannelInfo",
    "FrameworkMeta",
    "with_meta",
]
