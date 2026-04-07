"""Array — N-dimensional array DataObject with named axes.

Implements ADR-027 D1 (instance-level axes with class-level schema) and
ADR-027 D4 (``sel`` / ``iter_over`` with Level 1 laziness).

ADR-027 D2: this module is core-only. The four legacy domain subclasses
(``Image``, ``MSImage``, ``SRSImage``, ``FluorImage``) have been removed
as of T-006 and now live in the ``scieasy-blocks-imaging`` plugin
package. Code that previously imported them should either switch to
``Array(axes=[...])`` directly or depend on the imaging plugin.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, ClassVar, Self

from scieasy.core.types.base import DataObject

if TYPE_CHECKING:
    pass


class Array(DataObject):
    """N-dimensional array, optionally chunked and backed by Zarr.

    ADR-027 D1: ``axes`` is an instance-level attribute passed via the
    constructor. Subclasses declare what axes they accept via three
    class-level ClassVars that form a small schema:

    - ``required_axes``: minimum set of axis names any instance must
      carry. Subclasses tighten this to enforce "must have ``y, x``" or
      "must have ``c``".
    - ``allowed_axes``: superset of axis names the class accepts.
      ``None`` means "no restriction"; a frozenset means "instance axes
      must be a subset of this set".
    - ``canonical_order``: preferred ordering of axes used by reorder
      operations and pretty-printing.

    The 6D axis alphabet for scientific imaging is::

        {"t", "z", "c", "lambda", "y", "x"}

    where ``t`` is time, ``z`` is depth, ``c`` is discrete channel,
    ``lambda`` is continuous spectral, ``y`` and ``x`` are the spatial
    axes. ``c`` (discrete channel) and ``lambda`` (continuous spectral)
    are distinct axes and may coexist in a single instance (ADR-027
    discussion #3).

    Plugin subclasses (e.g. ``FluorImage`` in ``scieasy-blocks-imaging``)
    tighten the schema::

        class FluorImage(Image):
            required_axes = frozenset({"y", "x", "c"})

    Attributes:
        axes: Per-instance axis labels, e.g. ``["t", "z", "c", "y", "x"]``.
        shape: Shape of the array (may be ``None`` for metadata-only).
        dtype: Element data type.
        chunk_shape: Chunk dimensions for lazy/chunked storage.
    """

    # Class-level schema (subclasses override). Defaults are maximally
    # permissive: no required axes, no allowed restriction, no canonical
    # order. Plugin subclasses (Image / FluorImage / ...) override.
    required_axes: ClassVar[frozenset[str]] = frozenset()
    allowed_axes: ClassVar[frozenset[str] | None] = None
    canonical_order: ClassVar[tuple[str, ...]] = ()

    def __init__(
        self,
        *,
        axes: list[str],
        shape: tuple[int, ...] | None = None,
        dtype: Any = None,
        chunk_shape: tuple[int, ...] | None = None,
        **kwargs: Any,
    ) -> None:
        """Construct an Array with explicit axes and shape.

        ``axes`` is required per ADR-027 D1. The other :class:`DataObject`
        slots (``framework``, ``meta``, ``user``, ``storage_ref``) are
        passed through ``**kwargs`` to
        :meth:`DataObject.__init__`.

        Raises:
            ValueError: if ``axes`` fails :meth:`_validate_axes` (missing
                required / disallowed / duplicate).
        """
        super().__init__(**kwargs)
        self.axes: list[str] = list(axes)
        self.shape: tuple[int, ...] | None = tuple(shape) if shape is not None else None
        self.dtype: Any = dtype
        self.chunk_shape: tuple[int, ...] | None = tuple(chunk_shape) if chunk_shape is not None else None
        self._validate_axes()

    def _validate_axes(self) -> None:
        """Validate the instance's axes against the class's schema.

        Raises:
            ValueError: if axes contain duplicates, are missing any
                required axis, or contain any axis not in
                ``allowed_axes`` (when the latter is non-None).
        """
        axes_set = set(self.axes)
        if len(axes_set) != len(self.axes):
            raise ValueError(f"Duplicate axes in {self.axes}")
        if not self.required_axes.issubset(axes_set):
            missing = sorted(self.required_axes - axes_set)
            raise ValueError(f"{type(self).__name__} requires axes {sorted(self.required_axes)}, missing: {missing}")
        if self.allowed_axes is not None and not axes_set.issubset(self.allowed_axes):
            extra = sorted(axes_set - self.allowed_axes)
            raise ValueError(f"{type(self).__name__} accepts only {sorted(self.allowed_axes)}, unexpected: {extra}")

    @property
    def ndim(self) -> int:
        """Return the number of dimensions (length of ``axes``)."""
        return len(self.axes)

    def __array__(self, dtype: Any = None, copy: Any = None) -> Any:
        """Support ``np.asarray(array_obj)`` via the NumPy array protocol.

        Materialises the full data from storage (or from a derived
        in-memory slice produced by :meth:`sel` / :meth:`iter_over`).
        """
        import numpy as np

        data = self.to_memory()
        arr = np.asarray(data)
        if dtype is not None:
            arr = arr.astype(dtype)
        if copy:
            arr = arr.copy()
        return arr

    # -- ADR-027 D4: sel and iter_over ------------------------------------

    def sel(self, **kwargs: int | slice) -> Array:
        """Select a sub-array along named axes (ADR-027 D4).

        Examples::

            img.sel(z=15, c=0)        # single z, single channel
            img.sel(z=slice(10, 20))  # z range

        Integer indices REMOVE the corresponding axis from the result.
        Slice objects KEEP the axis. Lists of indices and boolean masks
        are NOT supported in Phase 10.

        The result is always a plain :class:`Array` instance (not
        ``type(self)``). This deliberate choice sidesteps the problem
        that a reduced slice may no longer satisfy the source class's
        ``required_axes`` invariant (e.g. a ``FluorImage`` requiring
        ``{y, x, c}`` and a call to ``sel(c=0)`` produces axes
        ``[y, x]``). The returned :class:`Array` has
        ``required_axes = frozenset()``, so any axis subset is valid.

        Metadata inheritance follows ADR-027 D5:

        - ``framework``: derived (lineage hint ``derived_from = self.object_id``).
        - ``meta``: shared by reference (immutable Pydantic model).
        - ``user``: shallow copy.
        - ``axes``: reduced per the selection.

        Laziness (Level 1): for in-memory-backed instances, the materialised
        numpy view is sliced eagerly and stashed on the returned instance
        via the ``_data`` attribute. For storage-backed instances, the
        full data is materialised through :meth:`DataObject.to_memory`
        once and then sliced with numpy (Level 1 laziness per ADR-027 D4
        Question 4: "For other backends, falls back to
        ``self.view().to_memory()`` then numpy indexing"). The Zarr-aware
        partial-read path is deferred to a future T-006a per Question 4.

        Raises:
            ValueError: if any kwarg key is not in ``self.axes``, if any
                kwarg value is not ``int`` or ``slice``, or if the
                instance has no backing data (no ``_data`` and no
                ``storage_ref``).
        """
        # Validate kwargs refer to existing axes before doing anything.
        unknown = set(kwargs.keys()) - set(self.axes)
        if unknown:
            raise ValueError(f"sel() received unknown axes: {sorted(unknown)}")

        # Build numpy index tuple in axis order, tracking resulting axes
        # and shape simultaneously.
        indexer: list[Any] = []
        new_axes: list[str] = []
        new_shape_list: list[int] = []
        for i, axis_name in enumerate(self.axes):
            if axis_name in kwargs:
                idx = kwargs[axis_name]
                if isinstance(idx, bool) or not isinstance(idx, (int, slice)):
                    raise ValueError(
                        f"sel() index for axis {axis_name!r} must be int or slice, got {type(idx).__name__}"
                    )
                indexer.append(idx)
                if isinstance(idx, slice):
                    new_axes.append(axis_name)
                    if self.shape is not None:
                        start, stop, step = idx.indices(self.shape[i])
                        size = max(0, (stop - start + (step - (1 if step > 0 else -1))) // step)
                        new_shape_list.append(size)
                # Integer index drops the axis — no append to new_axes.
            else:
                indexer.append(slice(None))
                new_axes.append(axis_name)
                if self.shape is not None:
                    new_shape_list.append(self.shape[i])

        # Materialise and slice the underlying data. Supports both
        # in-memory (``_data`` attribute, e.g. from tiff_adapter or a
        # previous sel result) and storage-backed instances.
        if hasattr(self, "_data") and getattr(self, "_data", None) is not None:
            full_data = self._data  # type: ignore[attr-defined]
        elif self._storage_ref is not None:
            full_data = self.to_memory()
        else:
            raise ValueError(
                f"{type(self).__name__}.sel() requires backing data. "
                f"This instance has no in-memory data and no storage_ref."
            )
        sliced_data = full_data[tuple(indexer)]

        # Metadata propagation per ADR-027 D5.
        new_framework = self._framework.derive()

        # Compute the new shape. If we had a known shape, new_shape_list
        # was populated alongside indexer; otherwise fall back to the
        # sliced array's shape (may be None if sliced_data has no shape).
        if self.shape is not None:
            new_shape: tuple[int, ...] | None = tuple(new_shape_list) if new_shape_list else ()
        else:
            new_shape = tuple(getattr(sliced_data, "shape", ())) or None

        # Always construct a plain Array instance (not type(self)) so
        # that required_axes violations do not trip _validate_axes on
        # reduced slices. See docstring for the rationale.
        new_instance = Array(
            axes=new_axes,
            shape=new_shape,
            dtype=self.dtype,
            chunk_shape=None,  # derived slice drops the chunk hint
            framework=new_framework,
            meta=self._meta,
            user=dict(self._user),
            storage_ref=None,
        )
        # Stash the materialised data so to_memory / __array__ can reach
        # it without hitting storage again.
        new_instance._data = sliced_data  # type: ignore[attr-defined]
        return new_instance

    def iter_over(self, axis: str) -> Iterator[Array]:
        """Yield sub-arrays along one named axis (ADR-027 D4).

        Example::

            for z_slice in img.iter_over("z"):
                ...

        Memory: ``O(one slice per iteration step)`` — each yielded
        :class:`Array` has ``axis`` removed from its axes list, carries
        metadata propagated per :meth:`sel`'s rules, and holds its
        sliced data in an ``_data`` attribute.

        Raises:
            ValueError: if ``axis`` is not in :attr:`axes` or if
                :attr:`shape` is ``None`` (cannot determine iteration
                length).
        """
        if axis not in self.axes:
            raise ValueError(f"Axis {axis!r} not in {self.axes}")
        if self.shape is None:
            raise ValueError(f"{type(self).__name__}.iter_over() requires a known shape. This instance has shape=None.")
        axis_pos = self.axes.index(axis)
        axis_size = self.shape[axis_pos]
        for i in range(axis_size):
            yield self.sel(**{axis: i})

    # -- with_meta override (T-005's base only handles standard slots) ----

    def with_meta(self, **changes: Any) -> Self:
        """Return a new Array with the ``meta`` slot updated.

        Overrides :meth:`DataObject.with_meta` to propagate the
        Array-specific constructor arguments (``axes``, ``shape``,
        ``dtype``, ``chunk_shape``). The base implementation only
        propagates the four standard DataObject slots (``framework``,
        ``meta``, ``user``, ``storage_ref``); without this override the
        call would raise ``TypeError`` because ``Array.__init__``
        requires ``axes``.

        Raises:
            ValueError: if ``self.meta is None`` (no typed Meta to
                update). Only Array subclasses that declare a
                ``Meta`` ClassVar can use :meth:`with_meta`.
        """
        if self._meta is None:
            raise ValueError(
                f"{type(self).__name__}.with_meta() requires a typed `meta` slot. "
                f"This instance has meta=None. Subclass with a class-level `Meta` "
                f"Pydantic model and pass an instance via the constructor to use "
                f"with_meta()."
            )

        from scieasy.core.meta import with_meta_changes

        new_meta = with_meta_changes(self._meta, **changes)
        new_framework = self._framework.derive()

        return type(self)(
            axes=list(self.axes),
            shape=self.shape,
            dtype=self.dtype,
            chunk_shape=self.chunk_shape,
            framework=new_framework,
            meta=new_meta,
            user=dict(self._user),
            storage_ref=self._storage_ref,
        )

    # -- to_memory override that respects in-memory _data on slices -------

    def to_memory(self) -> Any:
        """Materialise the full data into an in-memory representation.

        If this instance was created via :meth:`sel` or
        :meth:`iter_over` and carries an in-memory ``_data`` attribute
        (with ``storage_ref=None``), return that directly. Otherwise
        delegate to :meth:`DataObject.to_memory`, which routes through
        the storage backend.
        """
        if self._storage_ref is None and hasattr(self, "_data") and getattr(self, "_data", None) is not None:
            return self._data  # type: ignore[attr-defined]
        return super().to_memory()
