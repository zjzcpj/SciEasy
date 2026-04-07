"""Serialization helpers for typed DataObject reconstruction.

Implements ADR-027 Addendum 1 §1 (Decision D11': worker subprocess
returns typed ``DataObject`` instances, not ``ViewProxy``).

This module is a **stub** created in T-013. The full implementations
of :func:`_reconstruct_one` and :func:`_serialise_one` land in T-014
alongside the worker subprocess rewrite. T-013 needs the stub to exist
so that :mod:`scieasy.core.types.composite`'s
``_reconstruct_extra_kwargs`` / ``_serialise_extra_metadata`` hooks can
``from scieasy.core.types.serialization import _reconstruct_one,
_serialise_one`` *inside the classmethod body* for recursive slot
reconstruction. The inside-the-method import breaks what would
otherwise be a load-time cycle (``composite`` would import
``serialization``, and T-014's real ``serialization`` will import
every base class including ``composite``).

Per Open Question 1 of the Phase 10 implementation standards doc, this
module lives in ``scieasy.core.types.serialization`` rather than in
``scieasy.engine.runners.worker`` so the import direction is always
``core ← engine``, never the reverse. That keeps the importlinter
contract ``core must not depend on blocks/engine/api/ai/workflow``
clean.

T-014 will replace the bodies of :func:`_reconstruct_one` and
:func:`_serialise_one` with the real implementations described in
ADR-027 Addendum 1 §1. The signatures (single payload-item dict in,
single typed ``DataObject`` out; and the reverse) are locked by this
stub and by T-013's test ``test_serialization_module_imports``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scieasy.core.types.base import DataObject


def _reconstruct_one(payload_item: dict[str, Any]) -> DataObject:
    """Reconstruct one typed ``DataObject`` from a wire-format payload item.

    This is a T-013 stub. The full implementation lands in T-014 and
    will:

    1. Resolve the target class via ``TypeRegistry.resolve(type_chain)``.
    2. Rebuild the three metadata slots (``framework``, ``meta``, ``user``).
    3. Call ``cls._reconstruct_extra_kwargs(metadata)`` to pick up the
       base-class-specific constructor kwargs (e.g. ``axes``, ``shape``
       for ``Array``; ``slots`` for ``CompositeData``).
    4. Construct and return the typed instance with ``storage_ref`` set.

    Until then, any attempt to call this function raises
    :class:`NotImplementedError` with a pointer to T-014.

    Args:
        payload_item: The wire-format JSON dict produced by
            :func:`_serialise_one`. Shape:
            ``{"backend": ..., "path": ..., "format": ..., "metadata": {...}}``.

    Returns:
        A typed ``DataObject`` instance with ``storage_ref`` populated
        but its backing data **not** read yet (lazy per ADR-027 D4).

    Raises:
        NotImplementedError: always, until T-014 lands.
    """
    raise NotImplementedError(
        "scieasy.core.types.serialization._reconstruct_one is a T-013 stub. "
        "The full implementation lands in T-014. See ADR-027 Addendum 1 §1."
    )


def _serialise_one(obj: DataObject) -> dict[str, Any]:
    """Serialise one typed ``DataObject`` to a wire-format payload item.

    This is a T-013 stub. The full implementation lands in T-014 and
    will:

    1. Require ``obj.storage_ref is not None`` (caller's responsibility
       to run ``Block._auto_flush`` first).
    2. Dump ``obj.framework`` via ``model_dump(mode="json")``.
    3. Dump ``obj.meta`` via ``model_dump(mode="json")`` when non-None.
    4. Copy ``obj.user`` (shallow dict).
    5. Call ``type(obj)._serialise_extra_metadata(obj)`` to pick up the
       base-class-specific fields (e.g. ``axes``, ``shape`` for
       ``Array``; ``slots`` for ``CompositeData``).
    6. Assemble and return the wire-format dict.

    Until then, any attempt to call this function raises
    :class:`NotImplementedError` with a pointer to T-014.

    Args:
        obj: The typed ``DataObject`` to serialise. Must already have
            its backing data flushed to storage (``storage_ref`` set).

    Returns:
        A JSON-serialisable dict that :func:`_reconstruct_one` can
        round-trip back into a typed instance.

    Raises:
        NotImplementedError: always, until T-014 lands.
    """
    raise NotImplementedError(
        "scieasy.core.types.serialization._serialise_one is a T-013 stub. "
        "The full implementation lands in T-014. See ADR-027 Addendum 1 §1."
    )
