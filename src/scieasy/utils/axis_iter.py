# TODO(Phase 10 / T-011): Skeleton only. Implementation per
# docs/specs/phase10-implementation-standards.md
"""scieasy.utils.axis_iter — single-Array extra-axis iteration utility.

Implements ADR-027 D3 (``iterate_over_axes``). The function iterates a
caller-supplied ``func`` over all axes in a source ``Array`` that are
*not* in ``operates_on``, applying ``func`` to each slice and stacking
the results back into a new instance of the source's concrete class.

This is the common case for 5D / 6D imaging blocks: "I know how to
process ``(y, x)``, please loop over everything else (``t``, ``z``,
``c``, ...)". The sister utility ``scieasy.utils.broadcast.broadcast_apply``
covers the cross-modal case (low-dim source projected onto a high-dim
target along named axes).

Memory: O(one input slice + one output slice). Serial by design — block
internal parallelism is the block author's choice (ADR-027 D8).

Metadata propagation follows ADR-027 D5:

- ``framework`` is regenerated with ``derived_from=source.framework.object_id``
- ``meta`` is shared by reference (Pydantic models are frozen)
- ``user`` is shallow-copied
- ``axes`` is reduced to the ``operates_on`` axes only

This module is a *skeleton*. The function body raises
``NotImplementedError``; the implementation lands in T-011.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np

    from scieasy.core.types.array import Array


# Type alias for the user-supplied per-slice function. It receives the
# slice data (a numpy array containing only the operates_on dimensions)
# and a coordinate dict mapping each extra-axis name to its current
# integer index. It must return a numpy array whose shape is consistent
# across all slices (otherwise BroadcastError is raised at stack time).
SliceFn = Callable[["np.ndarray", dict[str, int]], "np.ndarray"]


def iterate_over_axes(
    source: Array,
    operates_on: set[str],
    func: SliceFn,
) -> Array:
    """Iterate ``func`` over every axis in ``source`` not in ``operates_on``.

    For each combination of the non-``operates_on`` axes, call::

        func(slice_data, slice_coord)

    where ``slice_data`` is a numpy array containing only the
    ``operates_on`` dimensions, and ``slice_coord`` is a dict mapping
    extra-axis name to current integer index.

    Results are stacked back into a new instance of ``source.__class__``,
    preserving ``axes``, ``shape``, and ``meta`` per ADR-027 D5
    propagation rules. The output ``framework`` slot has
    ``derived_from=source.framework.object_id`` and a fresh
    ``object_id`` / ``created_at``.

    Raises:
        scieasy.core.exceptions.BroadcastError: if ``operates_on`` is
            not a subset of ``source.axes``, or if slice outputs have
            inconsistent shapes that cannot be stacked back into a
            single array.
    """
    # TODO(T-011): ADR-027 D3 — implement iterate_over_axes:
    #
    #   1. Validate ``operates_on.issubset(set(source.axes))``; raise
    #      BroadcastError otherwise.
    #   2. Compute ``extra_axes = [a for a in source.axes if a not in operates_on]``
    #      and their lengths from ``source.shape``.
    #   3. Read the source payload via ``source.to_memory()`` (Phase 10
    #      Level 1 laziness — full materialise is acceptable for now;
    #      ``source.iter_over(...)`` chains may be used in T-011 if the
    #      Array.iter_over implementation from T-006 is also merged).
    #   4. For each combination of extra-axis indices, build a slice
    #      object that selects exactly those indices and the full range
    #      of operates_on axes; call ``func(slice_data, slice_coord)``;
    #      collect the results.
    #   5. Stack results into an output ndarray of the same overall
    #      shape (extra-axis dims unchanged + operates_on output dims),
    #      respecting whatever shape ``func`` returns. Raise
    #      BroadcastError if shapes are inconsistent.
    #   6. Construct the output instance with metadata propagation per
    #      ADR-027 D5: same class as source, framework derived,
    #      meta shared, user shallow-copied, axes preserved.
    #
    # Note for the implementer: this function MUST be serial. No
    # threads, no asyncio, no multiprocessing. Block-internal
    # parallelism is the block author's choice per ADR-027 D8 / D13.
    raise NotImplementedError("T-011: ADR-027 D3 — iterate_over_axes() not yet implemented")


__all__ = ["SliceFn", "iterate_over_axes"]


# Suppress unused-import lint by re-exporting Any in __annotations__
# (the SliceFn alias above already pulls in Callable; Any is reserved
# for any future type annotations the implementer adds in T-011).
_: Any = None
