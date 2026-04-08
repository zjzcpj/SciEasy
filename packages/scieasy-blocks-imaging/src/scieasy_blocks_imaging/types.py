"""Imaging plugin type classes (T-IMG-001).

Defines the four canonical imaging type classes per ADR-027 D1/D2/D5
and ADR-028 §D5:

- :class:`Image` — general-purpose 2D-to-6D microscopy image
- :class:`Mask` — binary mask (dtype=bool)
- :class:`Label` — composite label image (raster + optional polygons)
- :class:`Transform` — affine transform matrix (row/col axes)

Skeleton status: class declarations + ClassVars + Meta models are
fully populated. The ``Mask`` dtype validator and ``Label`` slot
validator raise ``NotImplementedError`` referencing T-IMG-001 until
the impl agent fills them in.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict

from scieasy.core.types.array import Array
from scieasy.core.types.composite import CompositeData


class Image(Array):
    """General-purpose microscopy image, 2D to 6D.

    The 6D axis alphabet for scientific imaging is::

        {"t", "z", "c", "lambda", "y", "x"}

    where ``t`` is time, ``z`` is depth, ``c`` is discrete channel,
    ``lambda`` is continuous spectral, ``y`` and ``x`` are the spatial
    axes. ``c`` and ``lambda`` are distinct axes and may coexist.

    Replaces OptEasy's per-modality subclasses (``FluorImage``,
    ``BrightfieldImage``, ``HyperspectralImage``) with a single class.
    Different modalities are distinguished by axis configuration and
    the :class:`Meta` fields, not by subclassing.
    """

    required_axes: ClassVar[frozenset[str]] = frozenset({"y", "x"})
    allowed_axes: ClassVar[frozenset[str] | None] = frozenset({"t", "z", "c", "lambda", "y", "x"})
    canonical_order: ClassVar[tuple[str, ...]] = ("t", "z", "c", "lambda", "y", "x")

    class Meta(BaseModel):
        """Per-instance imaging metadata.

        ADR-027 Addendum 1 §3: frozen, no PrivateAttr,
        JSON-round-trippable through Pydantic v2.

        Note (skeleton): ``pixel_size`` / ``z_spacing`` /
        ``time_interval`` are typed as ``Any | None`` until the impl
        agent retightens them to ``PhysicalQuantity | None`` and adds
        the corresponding import from ``scieasy.core.units``. Same
        applies to ``channels`` (target type ``list[ChannelInfo]``).
        """

        model_config = ConfigDict(frozen=True)
        pixel_size: Any | None = None
        z_spacing: Any | None = None
        time_interval: Any | None = None
        channels: list[Any] | None = None
        wavelengths_nm: list[float] | None = None
        objective: str | None = None
        acquisition_date: datetime | None = None
        source_file: str | None = None
        instrument: str | None = None


class Mask(Image):
    """Binary mask image. Enforces ``dtype=bool`` at construction.

    Per imaging spec Q-IMG-6: a Mask is an :class:`Image` whose dtype
    is constrained to boolean. The validator runs in ``__init__`` so
    illegal masks fail fast.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._validate_mask_dtype()

    def _validate_mask_dtype(self) -> None:
        """Enforce ``dtype == bool``.

        Raises:
            ValueError: If ``self.dtype`` is set and is not bool.
        """
        raise NotImplementedError(
            "T-IMG-001 Mask._validate_mask_dtype — impl pending (skeleton @ feat/issue-344/sprint-c-imaging-skeleton)"
        )


class Label(CompositeData):
    """Label image with raster and/or polygon representation.

    Per master plan Q-Image-1 = B: a composite with two slots:

    - ``raster``: integer-dtype :class:`Array`
    - ``polygons``: optional vector representation (target type
      ``DataFrame``; skeleton uses ``Array`` until the imaging
      plugin's DataFrame import path is finalised by impl agent)

    At least one slot must be non-None (Q-IMG-7). Validation runs in
    ``__init__``.
    """

    expected_slots: ClassVar[dict[str, type]] = {
        "raster": Array,
        "polygons": Array,
    }

    class Meta(BaseModel):
        """Per-instance label-image metadata."""

        model_config = ConfigDict(frozen=True)
        source_file: str | None = None
        n_objects: int | None = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._validate_label_slots()

    def _validate_label_slots(self) -> None:
        """Enforce at least one of ``raster`` / ``polygons`` is set.

        Raises:
            ValueError: If neither slot is populated.
        """
        raise NotImplementedError(
            "T-IMG-001 Label._validate_label_slots — impl pending (skeleton @ feat/issue-344/sprint-c-imaging-skeleton)"
        )


class Transform(Array):
    """Affine transform matrix.

    Per master plan Q-Image-2 = C: an :class:`Array` subclass with
    ``axes=["row","col"]`` and shape ``(2,3)`` for 2D affine or
    ``(3,3)`` for 3D affine.
    """

    required_axes: ClassVar[frozenset[str]] = frozenset({"row", "col"})
    allowed_axes: ClassVar[frozenset[str] | None] = frozenset({"row", "col"})
    canonical_order: ClassVar[tuple[str, ...]] = ("row", "col")

    class Meta(BaseModel):
        """Per-instance transform metadata.

        Attributes:
            transform_type: One of ``"affine"``, ``"rigid"``, ``"similarity"``.
            reference_shape: Shape of the reference image this
                transform was computed against, if known.
        """

        model_config = ConfigDict(frozen=True)
        transform_type: str = "affine"
        reference_shape: tuple[int, ...] | None = None


__all__ = ["Image", "Label", "Mask", "Transform"]
