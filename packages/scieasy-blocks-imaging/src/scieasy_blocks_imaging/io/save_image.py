"""SaveImage IO block — TIFF/Zarr writer for the imaging plugin.

T-IMG-003 implementation (Sprint C impl phase, narrow pilot scope).
See ``docs/specs/phase11-imaging-block-spec.md`` §9 T-IMG-003.

Scope for this implementation: write a single :class:`Image` (or a
length-1 :class:`Collection`) to ``.tif``/``.tiff`` via ``tifffile`` or
``.zarr`` via ``zarr``. Format is auto-detected from the output path
suffix but may be overridden via ``config['format']``. Broader format
support remains deferred per the Sprint C pilot dispatch prompt.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import numpy as np

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy_blocks_imaging.types import Image

_TIFF_FORMAT = "tiff"
_ZARR_FORMAT = "zarr"
_SUPPORTED_FORMATS = frozenset({_TIFF_FORMAT, _ZARR_FORMAT})

_EXT_TO_FORMAT: dict[str, str] = {
    ".tif": _TIFF_FORMAT,
    ".tiff": _TIFF_FORMAT,
    ".zarr": _ZARR_FORMAT,
}


def _materialise(image: Image) -> np.ndarray:
    """Return the underlying ``numpy`` array backing *image*.

    Lazy / storage-backed images are materialised through
    :meth:`DataObject.to_memory`. Eager images populated via the
    skeleton convention (``image._data``) are returned directly.
    """
    data_attr = getattr(image, "_data", None)
    if data_attr is not None:
        return np.asarray(data_attr)
    return np.asarray(image.to_memory())


def _unwrap_image(obj: DataObject | Collection) -> Image:
    """Extract a single :class:`Image` from either a bare instance or
    a length-1 :class:`Collection`."""
    if isinstance(obj, Image):
        return obj
    if isinstance(obj, Collection):
        if len(obj) == 0:
            raise ValueError("SaveImage: received an empty Collection")
        if len(obj) != 1:
            raise ValueError(f"SaveImage (pilot scope) only supports length-1 Collections; received length {len(obj)}")
        item = obj[0]
        if not isinstance(item, Image):
            raise ValueError(f"SaveImage: collection item is {type(item).__name__}, expected Image")
        return item
    raise ValueError(f"SaveImage: expected Image or Collection[Image], got {type(obj).__name__}")


def _resolve_format(path: Path, explicit: str | None) -> str:
    """Resolve the output format from an explicit config value or the
    path suffix. Raises :class:`ValueError` on unknown values."""
    if explicit is not None:
        fmt = explicit.lower()
        if fmt == "tif":
            fmt = _TIFF_FORMAT
        if fmt not in _SUPPORTED_FORMATS:
            raise ValueError(
                f"SaveImage: unsupported format {explicit!r}; supported formats are {sorted(_SUPPORTED_FORMATS)}"
            )
        return fmt
    ext = path.suffix.lower()
    if ext not in _EXT_TO_FORMAT:
        raise ValueError(
            f"SaveImage: cannot infer format from extension {ext!r}; "
            f"pass config['format'] explicitly (one of {sorted(_SUPPORTED_FORMATS)})"
        )
    return _EXT_TO_FORMAT[ext]


def _write_tiff(image: Image, path: Path) -> None:
    import tifffile

    data = _materialise(image)
    axes_str = "".join(image.axes).upper()
    tifffile.imwrite(str(path), data, metadata={"axes": axes_str})


def _write_zarr(image: Image, path: Path) -> None:
    import zarr

    data = _materialise(image)
    # Remove any previous store contents so repeated writes are
    # deterministic; zarr 3 refuses to overwrite an existing group by
    # default.
    if path.exists():
        import shutil

        shutil.rmtree(path)
    root = zarr.open_group(str(path), mode="w")
    arr = root.create_array(
        name="data",
        shape=data.shape,
        dtype=data.dtype,
    )
    arr[...] = data
    root.attrs["axes"] = list(image.axes)


class SaveImage(IOBlock):
    """TIFF/Zarr image writer (pilot scope).

    Accepts a single :class:`Image` or a length-1
    :class:`Collection[Image]` and writes it to the configured path.
    """

    direction: ClassVar[str] = "output"
    type_name: ClassVar[str] = "imaging.save_image"
    name: ClassVar[str] = "Save Image"
    description: ClassVar[str] = "Save an Image to a TIFF or Zarr store."
    category: ClassVar[str] = "io"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="images", accepted_types=[Image], is_collection=True),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "ui_priority": 0},
            "format": {
                "type": "string",
                "enum": ["tiff", "zarr"],
                "ui_priority": 1,
            },
        },
        "required": ["path"],
    }

    def load(self, config: BlockConfig) -> DataObject | Collection:  # pragma: no cover - output block
        """Direction is ``output``; ``load`` is unreachable via dispatch."""
        raise NotImplementedError("SaveImage is an output block; use save()")

    def save(self, obj: DataObject | Collection, config: BlockConfig) -> None:
        """Write *obj* to the configured path.

        Args:
            obj: An :class:`Image` or a length-1 :class:`Collection`.
            config: BlockConfig with ``path`` and optional ``format``.

        Raises:
            ValueError: If the collection is empty, longer than 1 item,
                or the format cannot be resolved.
        """
        raw_path = config.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError("SaveImage: config['path'] must be a non-empty string")
        path = Path(raw_path)

        fmt_cfg = config.get("format")
        if fmt_cfg is not None and not isinstance(fmt_cfg, str):
            raise ValueError(f"SaveImage: config['format'] must be a string or omitted, got {type(fmt_cfg).__name__}")
        fmt = _resolve_format(path, fmt_cfg)

        image = _unwrap_image(obj)
        path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == _TIFF_FORMAT:
            _write_tiff(image, path)
        else:
            _write_zarr(image, path)
