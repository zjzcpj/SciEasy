"""LoadImage IO block — TIFF/Zarr loader for the imaging plugin.

T-IMG-002 implementation (Sprint C impl phase, narrow pilot scope).
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-002.

Scope for this implementation: ``.tif``/``.tiff`` via ``tifffile`` and
``.zarr`` via ``zarr``. Broader format support (PNG/JPG/NPY/CZI/ND2/LIF)
remains deferred per the Sprint C pilot dispatch prompt and is tracked
as out-of-scope on issue #354.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import numpy as np

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import OutputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.meta.framework import FrameworkMeta
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy_blocks_imaging.types import Image

_TIFF_EXTS = frozenset({".tif", ".tiff"})
_ZARR_EXTS = frozenset({".zarr"})
_SUPPORTED_EXTS = _TIFF_EXTS | _ZARR_EXTS

# Mapping from tifffile single-letter axis codes to the SciEasy axis
# alphabet declared on :class:`Image`. ``S`` (samples) is treated as a
# discrete channel, matching the OME convention.
_TIFF_AXIS_MAP: dict[str, str] = {
    "T": "t",
    "Z": "z",
    "C": "c",
    "S": "c",
    "Y": "y",
    "X": "x",
}


def _default_axes_for_ndim(ndim: int) -> list[str]:
    """Return a reasonable default axis labelling for an N-D array.

    Used when the backend does not carry an axis annotation of its own
    (raw numpy round-trip, axis-less Zarr group, etc.). The defaults
    follow the common microscopy convention of spatial axes last.
    """
    if ndim == 2:
        return ["y", "x"]
    if ndim == 3:
        return ["c", "y", "x"]
    if ndim == 4:
        return ["t", "c", "y", "x"]
    if ndim == 5:
        return ["t", "z", "c", "y", "x"]
    if ndim == 6:
        return ["t", "z", "c", "lambda", "y", "x"]
    raise ValueError(f"LoadImage: cannot infer default axes for ndim={ndim}")


def _normalise_tiff_axes(tiff_axes: str, ndim: int) -> list[str]:
    """Translate tifffile's axis string into the SciEasy alphabet.

    Falls back to :func:`_default_axes_for_ndim` if the tiff axis string
    is empty or contains only characters outside the known mapping.
    """
    mapped = [_TIFF_AXIS_MAP[ch] for ch in tiff_axes if ch in _TIFF_AXIS_MAP]
    if len(mapped) == ndim and mapped:
        return mapped
    return _default_axes_for_ndim(ndim)


def _load_tiff(path: Path, axes_override: list[str] | None) -> Image:
    """Load a TIFF file eagerly into an :class:`Image`."""
    import tifffile

    with tifffile.TiffFile(str(path)) as tf:
        data: np.ndarray = tf.asarray()
        series_axes = tf.series[0].axes if tf.series else ""
    axes = axes_override if axes_override is not None else _normalise_tiff_axes(series_axes, data.ndim)
    if len(axes) != data.ndim:
        raise ValueError(f"LoadImage: axes override {axes!r} does not match array ndim={data.ndim} for {path}")
    img = Image(
        axes=axes,
        shape=tuple(data.shape),
        dtype=data.dtype,
        framework=FrameworkMeta(source=str(path)),
        meta=Image.Meta(source_file=str(path)),
    )
    img._data = data  # type: ignore[attr-defined]
    return img


def _load_zarr(path: Path, axes_override: list[str] | None) -> Image:
    """Load a ``.zarr`` store eagerly into an :class:`Image`.

    Supports both a top-level array store and a group containing a
    single array named ``"data"``. Axis metadata is read from the group
    attribute ``"axes"`` when present.
    """
    import zarr

    node = zarr.open(str(path), mode="r")
    attrs_axes: list[str] | None = None
    if isinstance(node, zarr.Array):
        arr_node: zarr.Array = node
    else:
        # group
        raw_attrs = dict(node.attrs)
        raw_axes = raw_attrs.get("axes")
        if isinstance(raw_axes, list):
            attrs_axes = [str(x) for x in raw_axes]
        if "data" not in node:
            raise ValueError(
                f"LoadImage: zarr group at {path} has no 'data' array (found keys: {sorted(node.array_keys())})"
            )
        data_node = node["data"]
        if not isinstance(data_node, zarr.Array):
            raise ValueError(f"LoadImage: zarr group at {path} 'data' entry is not an array")
        arr_node = data_node
    data = np.asarray(arr_node[...])
    if axes_override is not None:
        axes = axes_override
    elif attrs_axes is not None:
        axes = attrs_axes
    else:
        axes = _default_axes_for_ndim(data.ndim)
    if len(axes) != data.ndim:
        raise ValueError(f"LoadImage: axes {axes!r} do not match array ndim={data.ndim} for {path}")
    img = Image(
        axes=axes,
        shape=tuple(data.shape),
        dtype=data.dtype,
        framework=FrameworkMeta(source=str(path)),
        meta=Image.Meta(source_file=str(path)),
    )
    img._data = data  # type: ignore[attr-defined]
    return img


class LoadImage(IOBlock):
    """TIFF/Zarr image loader (pilot scope).

    Returns a single-item :class:`Collection` of :class:`Image`. Per
    ADR-028 Addendum 1 §D6' this block is STATIC: fixed ``output_ports``,
    no ``dynamic_ports``. The output type is always :class:`Image`.
    """

    direction: ClassVar[str] = "input"
    type_name: ClassVar[str] = "imaging.load_image"
    name: ClassVar[str] = "Load Image"
    description: ClassVar[str] = "Load a TIFF or Zarr image into an Image data object."
    category: ClassVar[str] = "io"

    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="images", accepted_types=[Image], is_collection=True),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {
                "type": ["string", "array"],
                "items": {"type": "string"},
                "ui_priority": 0,
                "ui_widget": "file_browser",
            },
            "axes": {"type": "string", "ui_priority": 1},
        },
        "required": ["path"],
    }

    def load(self, config: BlockConfig) -> DataObject | Collection:
        """Load the configured file(s) into a ``Collection[Image]``.

        Args:
            config: BlockConfig with ``path`` (str or list[str]) and optional
                ``axes`` (axis string override, e.g. ``"cyx"``). When
                ``path`` is a list, each file is loaded and all images are
                packed into a single :class:`Collection`.

        Returns:
            A :class:`Collection` of :class:`Image`. Length-1 for a single
            path, length-N for a list of N paths.

        Raises:
            FileNotFoundError: If any path does not exist.
            ValueError: If any extension is not in {.tif, .tiff, .zarr},
                or if ``path`` is neither a string nor a list of strings.
        """
        raw_path = config.get("path")

        axes_cfg = config.get("axes")
        axes_override: list[str] | None
        if axes_cfg is None:
            axes_override = None
        elif isinstance(axes_cfg, str):
            axes_override = [ch for ch in axes_cfg]
        else:
            raise ValueError(f"LoadImage: config['axes'] must be a string or omitted, got {type(axes_cfg).__name__}")

        if isinstance(raw_path, list):
            # Multi-path: load each file and return a combined Collection.
            images: list[DataObject] = []
            for single_raw in raw_path:
                if not isinstance(single_raw, str) or not single_raw:
                    raise ValueError("LoadImage: each entry in path list must be a non-empty string")
                images.append(self._load_single(Path(single_raw), axes_override))
            return Collection(items=images, item_type=Image)

        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError("LoadImage: config['path'] must be a non-empty string or list of strings")
        image = self._load_single(Path(raw_path), axes_override)
        return Collection(items=[image], item_type=Image)

    def _load_single(self, path: Path, axes_override: list[str] | None) -> Image:
        """Load a single image file into an :class:`Image`.

        Args:
            path: Absolute or relative path to a TIFF or Zarr file.
            axes_override: Optional per-axis label override list.

        Returns:
            A loaded :class:`Image`.

        Raises:
            FileNotFoundError: If the path does not exist.
            ValueError: If the extension is not supported.
        """
        if not path.exists():
            raise FileNotFoundError(f"LoadImage: no file at {path}")
        ext = path.suffix.lower()
        if ext not in _SUPPORTED_EXTS:
            raise ValueError(
                f"LoadImage: unsupported image format {ext!r}; supported extensions are {sorted(_SUPPORTED_EXTS)}"
            )
        return _load_tiff(path, axes_override) if ext in _TIFF_EXTS else _load_zarr(path, axes_override)

    def save(
        self,
        obj: DataObject | Collection,
        config: BlockConfig,
    ) -> None:  # pragma: no cover - input block
        """LoadImage is an input block; ``save`` is unreachable via dispatch.

        The method is required only to satisfy the :class:`IOBlock` ABC;
        runtime dispatch in :meth:`IOBlock.run` routes on ``direction``
        and never invokes :meth:`save` on an ``input`` block.
        """
        raise NotImplementedError("LoadImage is an input block; use load()")
