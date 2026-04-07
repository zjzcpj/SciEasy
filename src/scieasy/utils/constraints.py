# TODO(Phase 10 / T-010): Skeleton only. Implementation per
# docs/specs/phase10-implementation-standards.md
"""Port constraint factories — companion to ADR-027 D4 / D1.

Block authors compose ``InputPort.constraint`` callables from this
module to enforce per-axis or per-shape requirements at the port level
without needing to subclass ``Array``. Each factory returns a callable
suitable for the ``constraint=`` keyword on ``InputPort`` (per ADR-020
the callable receives a ``Collection`` and returns ``bool``).

Examples (post-implementation):

.. code-block:: python

    InputPort(name="image", accepted_types=[Image],
              constraint=has_axes("y", "x"))

    InputPort(name="image2d", accepted_types=[Image],
              constraint=has_exact_axes("y", "x"))

    InputPort(name="image", accepted_types=[Image],
              constraint=has_shape(2))   # ndim == 2

This module is a *skeleton*. Each factory currently returns a callable
that raises ``NotImplementedError`` when invoked, and the factory bodies
themselves do not validate their arguments yet. The full implementation
lands in T-010.

Source ADR section: ADR-027 D4 (companion utility — the ``has_*``
helpers complement the per-instance ``axes`` introduced by D1 and the
per-class ``required_axes`` introduced by D1).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# A constraint is a callable that takes a Collection (or any iterable of
# DataObject items per ADR-020) and returns True iff every item in the
# collection satisfies the constraint. The framework calls these inside
# ``Block.validate(...)`` before dispatching the block.
ConstraintFn = Callable[[Any], bool]


def has_axes(*required: str) -> ConstraintFn:
    """Constraint factory: items must include all of ``required`` axes.

    Returns a callable that returns True iff every item in the input
    collection has each of ``required`` somewhere in its ``axes`` list.
    Extra axes are allowed.
    """

    def _check(collection: Any) -> bool:
        # TODO(T-010): ADR-027 D4 companion — iterate the collection,
        # check ``required.issubset(set(item.axes))`` for each item,
        # short-circuit on first failure. Items lacking an ``axes``
        # attribute fail the constraint.
        raise NotImplementedError("T-010: ADR-027 D4 companion — has_axes() not yet implemented")

    _check.__doc__ = f"has_axes({', '.join(repr(a) for a in required)})"
    return _check


def has_exact_axes(*axes: str) -> ConstraintFn:
    """Constraint factory: items must have exactly ``axes`` (set equality).

    Returns a callable that returns True iff every item's ``axes`` set
    equals the supplied ``axes`` set. Order does not matter; the order
    of axes in an instance is governed by ``canonical_order`` on the
    item's class (ADR-027 D1), not by this constraint.
    """

    def _check(collection: Any) -> bool:
        # TODO(T-010): ADR-027 D4 companion — iterate the collection,
        # check ``set(item.axes) == set(axes)`` for each item.
        raise NotImplementedError("T-010: ADR-027 D4 companion — has_exact_axes() not yet implemented")

    _check.__doc__ = f"has_exact_axes({', '.join(repr(a) for a in axes)})"
    return _check


def has_shape(ndim: int) -> ConstraintFn:
    """Constraint factory: items must have exactly ``ndim`` axes.

    Returns a callable that returns True iff every item's ``len(axes)``
    equals ``ndim``. Useful for blocks that genuinely care about the
    rank but not the specific axis names (e.g. a generic 2D filter
    that does not assume ``(y, x)`` semantics).
    """

    def _check(collection: Any) -> bool:
        # TODO(T-010): ADR-027 D4 companion — iterate the collection,
        # check ``len(item.axes) == ndim`` for each item.
        raise NotImplementedError("T-010: ADR-027 D4 companion — has_shape() not yet implemented")

    _check.__doc__ = f"has_shape({ndim!r})"
    return _check


__all__ = [
    "ConstraintFn",
    "has_axes",
    "has_exact_axes",
    "has_shape",
]
