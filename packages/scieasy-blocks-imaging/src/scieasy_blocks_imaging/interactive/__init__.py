"""Interactive AppBlock helpers and exports for the imaging plugin."""

from __future__ import annotations

import csv
import json
import logging
import platform
import subprocess
import tempfile
from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pyarrow as pa

from scieasy.blocks.app.app_block import AppBlock, _PopenProcessAdapter
from scieasy.blocks.app.bridge import FileExchangeBridge
from scieasy.blocks.app.watcher import FileWatcher, ProcessExitedWithoutOutputError
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.state import BlockState
from scieasy.core.types.array import Array
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy_blocks_imaging.io.load_image import _default_axes_for_ndim, _load_tiff, _load_zarr
from scieasy_blocks_imaging.types import Image, Label, Mask

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from scieasy_blocks_imaging.interactive.fiji_block import FijiBlock
    from scieasy_blocks_imaging.interactive.napari_block import NapariBlock


def _resolve_exchange_dir(config: BlockConfig, *, prefix: str) -> Path:
    explicit_dir = config.get("exchange_dir")
    if explicit_dir:
        exchange_dir = Path(str(explicit_dir))
    else:
        project_dir = config.get("project_dir")
        block_id = config.get("block_id")
        if project_dir and block_id:
            exchange_dir = Path(str(project_dir)) / "data" / "exchange" / str(block_id)
        else:
            exchange_dir = Path(tempfile.mkdtemp(prefix=prefix))
    exchange_dir.mkdir(parents=True, exist_ok=True)
    (exchange_dir / "inputs").mkdir(exist_ok=True)
    (exchange_dir / "outputs").mkdir(exist_ok=True)
    return exchange_dir


def _input_images(inputs: Mapping[str, Collection | Image], port_name: str, block_name: str) -> list[Image]:
    raw = inputs.get(port_name)
    if raw is None:
        raise ValueError(f"{block_name}: missing required input port {port_name!r}")
    if isinstance(raw, Collection):
        images: list[Image] = []
        for index, item in enumerate(raw):
            if not isinstance(item, Image):
                raise ValueError(f"{block_name}: {port_name}[{index}] must be Image, got {type(item).__name__}")
            images.append(item)
        return images
    if isinstance(raw, Image):
        return [raw]
    raise ValueError(f"{block_name}: input {port_name!r} must be Image or Collection[Image], got {type(raw).__name__}")


def _prepare_image_exchange(
    images: list[Image], exchange_dir: Path, *, tool_name: str, config: BlockConfig
) -> list[Path]:
    import tifffile

    input_dir = exchange_dir / "inputs"
    paths: list[Path] = []
    for index, image in enumerate(images):
        path = input_dir / f"image_{index:04d}.tif"
        tifffile.imwrite(str(path), _image_data(image), metadata={"axes": "".join(image.axes).upper()})
        paths.append(path)

    manifest = {
        "tool": tool_name,
        "input_files": [str(path) for path in paths],
        "output_dir": str(exchange_dir / "outputs"),
        "config": dict(config.params),
    }
    (exchange_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return paths


def _resolve_command(
    config: BlockConfig,
    *,
    app_command: str,
    override_key: str | None = None,
    extra_args: list[str] | None = None,
) -> str | list[str]:
    """Resolve the executable command from config or ClassVar default.

    Priority order:
    1. MRO-injected ``app_command`` config field (from AppBlock base)
    2. Legacy block-specific override key (e.g. ``fiji_path``) for backward compat
    3. ClassVar ``app_command`` default on the block class
    """
    # 1. Check the MRO-injected app_command config field
    raw_command = config.get("app_command")
    if raw_command is not None:
        if isinstance(raw_command, list):
            return [str(part) for part in raw_command]
        if isinstance(raw_command, str):
            return raw_command
        raise ValueError(f"Interactive app command must be str or list[str], got {type(raw_command).__name__}")

    # 2. Legacy: check block-specific override key (for backward compat with
    #    old configs that may still have fiji_path / napari_path)
    if override_key:
        override = config.get(override_key)
        if override:
            return [str(override), *(extra_args or [])]

    # 3. Fall back to ClassVar default
    return [app_command, *(extra_args or [])]


def _open_file_manager(path: Path) -> None:
    """Best-effort: open the OS file manager at *path*."""
    try:
        system = platform.system()
        if system == "Windows":
            import os

            os.startfile(str(path))  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass  # best-effort, never block the workflow


def _run_external_app(
    block: AppBlock,
    *,
    command: str | list[str],
    exchange_dir: Path,
    patterns: list[str],
    config: BlockConfig,
    launch_args: list[str] | None = None,
) -> list[Path]:
    """Launch an external application and wait for output files.

    Parameters
    ----------
    launch_args:
        When provided, these strings are appended to the validated command
        instead of the default ``str(exchange_dir)`` suffix.  Pass the staged
        TIFF file paths here for applications (e.g. Fiji native opener) that
        expect individual file paths rather than the exchange directory root
        (see issue #420).
    """
    bridge = FileExchangeBridge()
    timeout = int(config.get("watch_timeout", getattr(block, "watch_timeout", 300)))
    stability_period = float(config.get("stability_period", 0.5))
    done_marker = config.get("done_marker")

    if block.state == BlockState.RUNNING:
        block.transition(BlockState.PAUSED)

    # ADR-030 D3: use user-selected output_dir if configured.
    custom_output_dir = config.get("output_dir")
    output_dir = Path(str(custom_output_dir)) if custom_output_dir else exchange_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Waiting for external application output. Save files to: %s", output_dir)

    proc = bridge.launch(command, exchange_dir, argv_override=launch_args)
    watcher = FileWatcher(
        directory=output_dir,
        patterns=patterns,
        timeout=timeout,
        process_handle=_PopenProcessAdapter(proc),
        stability_period=stability_period,
        done_marker=str(done_marker) if done_marker is not None else None,
    )
    watcher.start()
    try:
        output_files = watcher.wait_for_output()
    except ProcessExitedWithoutOutputError:
        if block.state == BlockState.PAUSED:
            block.transition(BlockState.CANCELLED)
        return []
    except Exception:
        if block.state == BlockState.PAUSED:
            block.transition(BlockState.ERROR)
        raise
    finally:
        watcher.stop()
        with suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=5)

    if block.state == BlockState.PAUSED:
        block.transition(BlockState.RUNNING)
    if block.state == BlockState.RUNNING:
        block.transition(BlockState.DONE)
    return output_files


def _collect_outputs(
    output_files: list[Path], *, template_image: Image | None, allowed_ports: set[str]
) -> dict[str, Collection]:
    grouped: dict[str, list[Any]] = {}
    axes_hint = list(template_image.axes) if template_image is not None else None

    for path in output_files:
        port = _guess_output_port(path, allowed_ports)
        grouped.setdefault(port, []).append(_load_output(path, port=port, axes_hint=axes_hint))

    collections: dict[str, Collection] = {}
    for port_name, items in grouped.items():
        collections[port_name] = Collection(items=cast(list[Any], items), item_type=type(items[0]))
    return collections


def _guess_output_port(path: Path, allowed_ports: set[str]) -> str:
    suffix = path.suffix.lower()
    stem = path.stem.lower()
    if suffix == ".csv" and "measurements" in allowed_ports:
        return "measurements"
    if any(token in stem for token in ("mask", "segmentation_mask")) and "mask" in allowed_ports:
        return "mask"
    if any(token in stem for token in ("label", "labels", "annotation")) and "label" in allowed_ports:
        return "label"
    if suffix in {".geojson", ".roi", ".zip", ".qpdata"} and "label" in allowed_ports:
        return "label"
    if "image" in allowed_ports:
        return "image"
    if "label" in allowed_ports:
        return "label"
    if "measurements" in allowed_ports:
        return "measurements"
    raise ValueError(f"Could not route output file {path.name!r} to a known port")


def _load_output(path: Path, *, port: str, axes_hint: list[str] | None) -> Image | Mask | Label | DataFrame:
    if port == "measurements":
        return _dataframe_from_csv(path)
    if port == "label" and path.suffix.lower() in {".geojson", ".roi", ".zip", ".qpdata"}:
        return _annotation_label(path)

    image = _load_image_like(path, axes_hint=axes_hint)
    if port == "image":
        return image
    if port == "mask":
        return _mask_from_image(image)
    return _label_from_image(image)


def _load_image_like(path: Path, *, axes_hint: list[str] | None) -> Image:
    suffix = path.suffix.lower()
    if suffix in {".tif", ".tiff"}:
        return _load_tiff(path, axes_hint)
    if suffix == ".zarr":
        return _load_zarr(path, axes_hint)
    if suffix == ".npy":
        data = np.load(path)
        axes = axes_hint or _default_axes_for_ndim(data.ndim)
        return _image_from_array(np.asarray(data), axes=axes, source_file=str(path))
    if suffix == ".png":
        import imageio.v2 as imageio

        data = np.asarray(imageio.imread(path))
        if data.ndim == 2:
            return _image_from_array(data, axes=["y", "x"], source_file=str(path))
        if data.ndim == 3 and data.shape[2] in {3, 4}:
            return _image_from_array(np.moveaxis(data[..., :3], -1, 0), axes=["c", "y", "x"], source_file=str(path))
    raise ValueError(f"Unsupported interactive output format {suffix!r} for {path}")


def _image_from_array(data: np.ndarray, *, axes: list[str], source_file: str) -> Image:
    image = Image(axes=axes, shape=tuple(data.shape), dtype=data.dtype, meta=Image.Meta(source_file=source_file))
    image._data = data  # type: ignore[attr-defined]
    return image


def _mask_from_image(image: Image) -> Mask:
    data = _image_data(image).astype(bool, copy=False)
    mask = Mask(
        axes=list(image.axes),
        shape=tuple(data.shape),
        dtype=bool,
        framework=image.framework.derive(),
        meta=image.meta,
        user=dict(image.user),
    )
    mask._data = data  # type: ignore[attr-defined]
    return mask


def _label_from_image(image: Image) -> Label:
    data = np.asarray(_image_data(image), dtype=np.int32)
    raster = Array(
        axes=list(image.axes),
        shape=tuple(data.shape),
        dtype=data.dtype,
        framework=image.framework.derive(),
        user=dict(image.user),
    )
    raster._data = data  # type: ignore[attr-defined]
    source_file = image.meta.source_file if isinstance(image.meta, Image.Meta) else None
    return Label(
        slots={"raster": raster},
        framework=image.framework.derive(),
        meta=Label.Meta(source_file=source_file, n_objects=int(np.max(data)) if data.size else 0),
        user=dict(image.user),
    )


def _annotation_label(path: Path) -> Label:
    if path.suffix.lower() == ".geojson":
        payload = json.loads(path.read_text(encoding="utf-8"))
        features = payload.get("features", []) if isinstance(payload, dict) else []
        rows = [
            {
                "source_path": str(path),
                "geometry_type": feature.get("geometry", {}).get("type"),
                "properties": json.dumps(feature.get("properties", {}), sort_keys=True),
            }
            for feature in features
            if isinstance(feature, dict)
        ]
        if not rows:
            rows = [{"source_path": str(path), "geometry_type": None, "properties": "{}"}]
    else:
        rows = [{"source_path": str(path), "format": path.suffix.lower().lstrip(".")}]

    polygons = _dataframe_from_rows(rows)
    return Label(slots={"polygons": polygons}, meta=Label.Meta(source_file=str(path), n_objects=len(rows)))


def _dataframe_from_csv(path: Path) -> DataFrame:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if reader.fieldnames is None:
            raise ValueError(f"Interactive measurements file {path} has no header row")
        if rows:
            table = pa.table({name: [row.get(name) for row in rows] for name in reader.fieldnames})
        else:
            table = pa.table({name: pa.array([]) for name in reader.fieldnames})
    dataframe = DataFrame(columns=list(table.column_names), row_count=table.num_rows)
    dataframe._arrow_table = table  # type: ignore[attr-defined]
    return dataframe


def _dataframe_from_rows(rows: list[dict[str, Any]]) -> DataFrame:
    column_names = list(rows[0].keys()) if rows else ["source_path"]
    table = pa.table({name: pa.array([row.get(name) for row in rows]) for name in column_names})
    dataframe = DataFrame(columns=list(table.column_names), row_count=table.num_rows)
    dataframe._arrow_table = table  # type: ignore[attr-defined]
    return dataframe


def _image_data(image: Image) -> np.ndarray:
    if image.storage_ref is None and hasattr(image, "_data") and getattr(image, "_data", None) is not None:
        return np.asarray(image._data)  # type: ignore[attr-defined]
    return np.asarray(image.to_memory())


__all__ = ["FijiBlock", "NapariBlock"]


def __getattr__(name: str) -> Any:
    if name == "FijiBlock":
        from scieasy_blocks_imaging.interactive.fiji_block import FijiBlock

        return FijiBlock
    if name == "NapariBlock":
        from scieasy_blocks_imaging.interactive.napari_block import NapariBlock

        return NapariBlock
    raise AttributeError(name)
