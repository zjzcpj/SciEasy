"""T-IMG-002 tests — LoadImage TIFF/Zarr round-trip and error handling.

Scope matches the pilot implementation in
``scieasy_blocks_imaging.io.load_image``: ``.tif``/``.tiff`` and
``.zarr`` only. Broader format coverage is deferred.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import numpy as np
import pytest
from scieasy_blocks_imaging.io.load_image import LoadImage
from scieasy_blocks_imaging.io.save_image import SaveImage
from scieasy_blocks_imaging.types import Image

from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.collection import Collection


def _make_image(arr: np.ndarray, axes: list[str]) -> Image:
    img = Image(axes=axes, shape=arr.shape, dtype=arr.dtype)
    img._data = arr
    return img


def test_t_img_002_module_importable() -> None:
    """The T-IMG-002 module imports cleanly."""
    importlib.import_module("scieasy_blocks_imaging.io.load_image")


def test_t_img_002_class_has_required_classvars() -> None:
    """LoadImage declares the mandatory IOBlock ClassVars."""
    assert LoadImage.type_name == "imaging.load_image"
    assert LoadImage.name == "Load Image"
    assert LoadImage.category == "io"
    assert LoadImage.direction == "input"
    assert "path" in LoadImage.config_schema["properties"]
    assert LoadImage.config_schema["required"] == ["path"]
    assert len(LoadImage.output_ports) == 1
    assert LoadImage.output_ports[0].name == "images"


def test_load_single_tif_round_trip(tmp_path: Path) -> None:
    """Write a 2-D TIFF via SaveImage, reload via LoadImage, verify equality."""
    arr = np.arange(20, dtype=np.uint16).reshape(4, 5)
    img = _make_image(arr, ["y", "x"])
    col = Collection(items=[img], item_type=Image)

    out_path = tmp_path / "single.tif"
    SaveImage().save(col, BlockConfig(params={"path": str(out_path)}))

    loaded = LoadImage().load(BlockConfig(params={"path": str(out_path)}))
    assert isinstance(loaded, Collection)
    assert len(loaded) == 1
    img_out = loaded[0]
    assert isinstance(img_out, Image)
    assert img_out.axes == ["y", "x"]
    assert img_out.shape == (4, 5)
    assert np.array_equal(img_out._data, arr)
    assert img_out.meta is not None
    assert img_out.meta.source_file == str(out_path)


def test_load_3d_tif_preserves_axes_via_tiff_metadata(tmp_path: Path) -> None:
    """A 3-D C/Y/X TIFF written with axis metadata round-trips axes."""
    arr = np.arange(2 * 3 * 4, dtype=np.uint8).reshape(2, 3, 4)
    img = _make_image(arr, ["c", "y", "x"])
    col = Collection(items=[img], item_type=Image)

    out_path = tmp_path / "stack.tif"
    SaveImage().save(col, BlockConfig(params={"path": str(out_path)}))

    loaded = LoadImage().load(BlockConfig(params={"path": str(out_path)}))
    img_out = loaded[0]
    assert img_out.axes == ["c", "y", "x"]
    assert np.array_equal(img_out._data, arr)


def test_load_zarr_round_trip_preserves_axes(tmp_path: Path) -> None:
    """Zarr round-trip preserves data and axis labels."""
    arr = np.random.default_rng(seed=42).integers(0, 255, size=(3, 5, 7)).astype(np.uint8)
    img = _make_image(arr, ["c", "y", "x"])
    col = Collection(items=[img], item_type=Image)

    out_path = tmp_path / "vol.zarr"
    SaveImage().save(col, BlockConfig(params={"path": str(out_path)}))

    loaded = LoadImage().load(BlockConfig(params={"path": str(out_path)}))
    img_out = loaded[0]
    assert img_out.axes == ["c", "y", "x"]
    assert img_out.shape == (3, 5, 7)
    assert np.array_equal(img_out._data, arr)


def test_load_unsupported_extension_raises(tmp_path: Path) -> None:
    """An unsupported file extension raises ValueError."""
    bogus = tmp_path / "image.xyz"
    bogus.write_bytes(b"not an image")
    with pytest.raises(ValueError, match="unsupported image format"):
        LoadImage().load(BlockConfig(params={"path": str(bogus)}))


def test_load_nonexistent_path_raises(tmp_path: Path) -> None:
    """A missing path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        LoadImage().load(BlockConfig(params={"path": str(tmp_path / "does_not_exist.tif")}))


def test_load_axes_override_applied(tmp_path: Path) -> None:
    """An explicit axes override is honoured and replaces auto-detection."""
    arr = np.zeros((2, 3), dtype=np.uint8)
    img = _make_image(arr, ["y", "x"])
    col = Collection(items=[img], item_type=Image)
    out_path = tmp_path / "override.tif"
    SaveImage().save(col, BlockConfig(params={"path": str(out_path)}))

    loaded = LoadImage().load(BlockConfig(params={"path": str(out_path), "axes": "yx"}))
    assert loaded[0].axes == ["y", "x"]


def test_load_axes_override_wrong_length_raises(tmp_path: Path) -> None:
    """An override whose length does not match ndim raises ValueError."""
    arr = np.zeros((2, 3), dtype=np.uint8)
    img = _make_image(arr, ["y", "x"])
    col = Collection(items=[img], item_type=Image)
    out_path = tmp_path / "wrong.tif"
    SaveImage().save(col, BlockConfig(params={"path": str(out_path)}))

    with pytest.raises(ValueError, match="ndim"):
        LoadImage().load(BlockConfig(params={"path": str(out_path), "axes": "cyx"}))
