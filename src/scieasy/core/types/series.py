"""Series — 1D indexed data DataObject (time series, chromatograms, spectra).

ADR-027 D2: this module is core-only. The legacy domain subclasses
(``Spectrum``, ``RamanSpectrum``, ``MassSpectrum``) have been removed as
of T-007 and now belong in the ``scieasy-blocks-spectral`` plugin
package. Code that previously imported them should either switch to
``Series(index_name=..., value_name=...)`` directly or depend on the
spectral plugin.
"""

from __future__ import annotations

from typing import Any, Self

from scieasy.core.types.base import DataObject


class Series(DataObject):
    """One-dimensional indexed data (time series, chromatogram, spectrum).

    Attributes:
        index_name: Label for the index axis (e.g. ``"wavenumber"``,
            ``"mz"``, ``"time"``).
        value_name: Label for the value axis (e.g. ``"intensity"``).
        length: Number of data points, if known.
    """

    def __init__(
        self,
        *,
        index_name: str | None = None,
        value_name: str | None = None,
        length: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Construct a Series with optional axis labels and length.

        Standard :class:`DataObject` slots (``framework``, ``meta``,
        ``user``, ``storage_ref``) are passed through ``**kwargs`` to
        :meth:`DataObject.__init__`.
        """
        super().__init__(**kwargs)
        self.index_name = index_name
        self.value_name = value_name
        self.length = length

    # -- with_meta override (T-005's base only handles standard slots) ----

    def with_meta(self, **changes: Any) -> Self:
        """Return a new Series with the ``meta`` slot updated.

        Overrides :meth:`DataObject.with_meta` to propagate the
        Series-specific constructor arguments (``index_name``,
        ``value_name``, ``length``). The base implementation only
        propagates the four standard DataObject slots (``framework``,
        ``meta``, ``user``, ``storage_ref``); without this override the
        call would lose the Series-specific attributes on the returned
        instance.

        Raises:
            ValueError: if ``self.meta is None`` (no typed Meta to
                update). Only Series subclasses that declare a ``Meta``
                ClassVar can use :meth:`with_meta`.
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
            index_name=self.index_name,
            value_name=self.value_name,
            length=self.length,
            framework=new_framework,
            meta=new_meta,
            user=dict(self._user),
            storage_ref=self._storage_ref,
        )
