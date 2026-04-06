"""DataFrame — columnar tabular data DataObject.

ADR-027 D2: this module is core-only. The legacy domain subclasses
(``PeakTable``, ``MetabPeakTable``) have been removed as of T-007 and
now belong in the ``scieasy-blocks-spectral`` plugin package. Code that
previously imported them should either switch to ``DataFrame(columns=..., ...)``
directly or depend on the spectral plugin.
"""

from __future__ import annotations

from typing import Any, Self

from scieasy.core.types.base import DataObject


class DataFrame(DataObject):
    """Columnar tabular data, backed by Arrow/Parquet for large datasets.

    Attributes:
        columns: Column names, if known.
        row_count: Number of rows, if known.
        schema: Column-level type schema, if known.
    """

    def __init__(
        self,
        *,
        columns: list[str] | None = None,
        row_count: int | None = None,
        schema: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Construct a DataFrame with optional column/schema information.

        Standard :class:`DataObject` slots (``framework``, ``meta``,
        ``user``, ``storage_ref``) are passed through ``**kwargs`` to
        :meth:`DataObject.__init__`.
        """
        super().__init__(**kwargs)
        self.columns = columns
        self.row_count = row_count
        self.schema = schema

    # -- with_meta override (T-005's base only handles standard slots) ----

    def with_meta(self, **changes: Any) -> Self:
        """Return a new DataFrame with the ``meta`` slot updated.

        Overrides :meth:`DataObject.with_meta` to propagate the
        DataFrame-specific constructor arguments (``columns``,
        ``row_count``, ``schema``). The base implementation only
        propagates the four standard DataObject slots (``framework``,
        ``meta``, ``user``, ``storage_ref``); without this override the
        call would lose the DataFrame-specific attributes on the
        returned instance.

        Raises:
            ValueError: if ``self.meta is None`` (no typed Meta to
                update). Only DataFrame subclasses that declare a
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
            columns=list(self.columns) if self.columns is not None else None,
            row_count=self.row_count,
            schema=dict(self.schema) if self.schema is not None else None,
            framework=new_framework,
            meta=new_meta,
            user=dict(self._user),
            storage_ref=self._storage_ref,
        )
