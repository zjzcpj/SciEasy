"""Smoke tests for the Phase 10 skeleton files (PR #261).

These tests guard the contract documented in
``docs/specs/phase10-implementation-standards.md``:

1. Every skeleton module is importable at module-load time.
2. Every public name is exposed as documented.
3. Calling any placeholder method raises ``NotImplementedError`` with a
   message that cites the implementing ticket so future agents can find
   the right place to fill in.

When a follow-up ticket (T-003 / T-004 / T-010 / T-011) lands its
implementation, that ticket must REPLACE these smoke assertions with the
real per-feature tests listed in the standards doc. This file is
explicitly a temporary scaffold — the standards doc names the
replacement test files (e.g. ``tests/core/test_units.py`` for T-003).
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# T-003 / ADR-027 D6 + Addendum 1 §4 — PhysicalQuantity skeleton
# ---------------------------------------------------------------------------


def test_physical_quantity_module_importable() -> None:
    from scieasy.core.units import PhysicalQuantity

    assert PhysicalQuantity is not None


def test_physical_quantity_construction_raises_not_implemented() -> None:
    from scieasy.core.units import PhysicalQuantity

    with pytest.raises(NotImplementedError, match="T-003"):
        PhysicalQuantity(value=1.0, unit="m")


# ---------------------------------------------------------------------------
# T-004 / ADR-027 D5 — FrameworkMeta + scieasy.core.meta module
#
# T-004 has landed; the smoke tests that lived here have been replaced by
# the real per-feature suite in ``tests/core/test_framework_meta.py``.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# T-010 / ADR-027 D4 companion — scieasy.utils.constraints
# ---------------------------------------------------------------------------


def test_constraints_module_importable() -> None:
    from scieasy.utils.constraints import (
        ConstraintFn,
        has_axes,
        has_exact_axes,
        has_shape,
    )

    assert ConstraintFn is not None
    assert callable(has_axes)
    assert callable(has_exact_axes)
    assert callable(has_shape)


def test_constraint_factories_return_callables() -> None:
    """The skeleton's factory bodies do not raise; they return a
    placeholder callable that itself raises NotImplementedError when
    invoked. This matches the standards-doc contract for T-010."""
    from scieasy.utils.constraints import has_axes, has_exact_axes, has_shape

    has_yx = has_axes("y", "x")
    assert callable(has_yx)
    with pytest.raises(NotImplementedError, match="T-010"):
        has_yx([])

    has_exact_yx = has_exact_axes("y", "x")
    assert callable(has_exact_yx)
    with pytest.raises(NotImplementedError, match="T-010"):
        has_exact_yx([])

    has_2d = has_shape(2)
    assert callable(has_2d)
    with pytest.raises(NotImplementedError, match="T-010"):
        has_2d([])


def test_constraint_factory_callables_have_useful_repr_doc() -> None:
    """The placeholder factories assign a doc string to the returned
    callable so that future error messages have a useful breadcrumb.
    T-010 will preserve this contract in the real implementation."""
    from scieasy.utils.constraints import has_axes, has_exact_axes, has_shape

    assert "y" in has_axes("y", "x").__doc__  # type: ignore[operator]
    assert "y" in has_exact_axes("y", "x").__doc__  # type: ignore[operator]
    assert "2" in has_shape(2).__doc__  # type: ignore[operator]


# ---------------------------------------------------------------------------
# T-011 / ADR-027 D3 — scieasy.utils.axis_iter.iterate_over_axes
# ---------------------------------------------------------------------------


def test_axis_iter_module_importable() -> None:
    from scieasy.utils.axis_iter import SliceFn, iterate_over_axes

    assert SliceFn is not None
    assert callable(iterate_over_axes)


def test_iterate_over_axes_skeleton_raises_not_implemented() -> None:
    from scieasy.utils.axis_iter import iterate_over_axes

    with pytest.raises(NotImplementedError, match="T-011"):
        iterate_over_axes(
            source=None,  # type: ignore[arg-type]
            operates_on={"y", "x"},
            func=lambda data, coord: data,  # type: ignore[arg-type,return-value]
        )


# ---------------------------------------------------------------------------
# Cross-skeleton contract checks
# ---------------------------------------------------------------------------


def test_all_skeletons_co_importable() -> None:
    """The PR description claims all 5 skeletons import together
    cleanly. Guard that claim. T-004 has landed, so the
    ``scieasy.core.meta`` symbols (``FrameworkMeta``, ``ChannelInfo``,
    ``with_meta_changes``) are real implementations rather than
    placeholders, but the import-surface contract still applies."""
    from scieasy.core.meta import ChannelInfo, FrameworkMeta, with_meta_changes
    from scieasy.core.meta.framework import FrameworkMeta as FrameworkMetaDirect
    from scieasy.core.units import PhysicalQuantity
    from scieasy.utils.axis_iter import iterate_over_axes
    from scieasy.utils.constraints import has_axes, has_exact_axes, has_shape

    assert FrameworkMeta is FrameworkMetaDirect
    assert PhysicalQuantity is not None
    assert ChannelInfo is not None
    assert callable(with_meta_changes)
    assert callable(iterate_over_axes)
    assert callable(has_axes)
    assert callable(has_exact_axes)
    assert callable(has_shape)
