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
# T-003 / ADR-027 D6 + Addendum 1 §4 — PhysicalQuantity
#
# The PhysicalQuantity skeleton smoke tests that previously lived here
# were removed when T-003 landed its real implementation. See
# ``tests/core/test_units.py`` for the replacement test suite.
# ``test_all_skeletons_co_importable`` below still imports
# ``PhysicalQuantity`` so the cross-skeleton check remains meaningful.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# T-004 / ADR-027 D5 — FrameworkMeta + scieasy.core.meta module
# ---------------------------------------------------------------------------


def test_framework_meta_module_importable() -> None:
    from scieasy.core.meta.framework import FrameworkMeta

    assert FrameworkMeta is not None


def test_framework_meta_can_be_instantiated_in_skeleton_phase() -> None:
    """The skeleton uses placeholder defaults so that ``FrameworkMeta()``
    is instantiable. T-004 will replace these with the real
    uuid4-based ``object_id`` and frozen config."""
    from scieasy.core.meta.framework import FrameworkMeta

    instance = FrameworkMeta()
    assert hasattr(instance, "created_at")
    assert hasattr(instance, "object_id")
    assert hasattr(instance, "source")
    assert hasattr(instance, "lineage_id")
    assert hasattr(instance, "derived_from")


def test_framework_meta_derive_raises_not_implemented() -> None:
    from scieasy.core.meta.framework import FrameworkMeta

    with pytest.raises(NotImplementedError, match="T-004"):
        FrameworkMeta().derive()


def test_core_meta_package_re_exports() -> None:
    from scieasy.core.meta import ChannelInfo, FrameworkMeta, with_meta

    assert FrameworkMeta is not None
    assert ChannelInfo is not None
    assert callable(with_meta)


def test_channel_info_skeleton_raises_not_implemented() -> None:
    from scieasy.core.meta import ChannelInfo

    with pytest.raises(NotImplementedError, match="T-004"):
        ChannelInfo(name="DAPI")


def test_with_meta_helper_skeleton_raises_not_implemented() -> None:
    from scieasy.core.meta import with_meta

    class _Stub:
        pass

    with pytest.raises(NotImplementedError, match="T-004"):
        with_meta(_Stub(), pixel_size=1.0)  # type: ignore[arg-type]


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
    cleanly. Guard that claim."""
    from scieasy.core.meta import ChannelInfo, FrameworkMeta, with_meta
    from scieasy.core.meta.framework import FrameworkMeta as FrameworkMetaDirect
    from scieasy.core.units import PhysicalQuantity
    from scieasy.utils.axis_iter import iterate_over_axes
    from scieasy.utils.constraints import has_axes, has_exact_axes, has_shape

    assert FrameworkMeta is FrameworkMetaDirect
    assert PhysicalQuantity is not None
    assert ChannelInfo is not None
    assert callable(with_meta)
    assert callable(iterate_over_axes)
    assert callable(has_axes)
    assert callable(has_exact_axes)
    assert callable(has_shape)
