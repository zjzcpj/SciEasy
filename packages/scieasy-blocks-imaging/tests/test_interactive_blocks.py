"""Tests for interactive imaging AppBlocks using fake external tools."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scieasy_blocks_imaging.interactive.cell_profiler_block import CellProfilerBlock
from scieasy_blocks_imaging.interactive.fiji_block import FijiBlock
from scieasy_blocks_imaging.interactive.napari_block import NapariBlock
from scieasy_blocks_imaging.interactive.qupath_block import QuPathBlock
from scieasy_blocks_imaging.types import Image

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.state import BlockState
from scieasy.core.types.collection import Collection


def _make_image(arr: np.ndarray, axes: list[str] | None = None) -> Image:
    image = Image(axes=axes or ["y", "x"], shape=arr.shape, dtype=arr.dtype)
    image._data = arr  # type: ignore[attr-defined]
    return image


def _make_running(block: object) -> object:
    block.transition(BlockState.READY)  # type: ignore[attr-defined]
    block.transition(BlockState.RUNNING)  # type: ignore[attr-defined]
    return block


def _write_fake_tool(tmp_path: Path, body: str) -> Path:
    script = tmp_path / "fake_tool.py"
    script.write_text(body, encoding="utf-8")
    return script


def test_fiji_block_routes_image_outputs(tmp_path: Path) -> None:
    script = _write_fake_tool(
        tmp_path,
        """
from pathlib import Path
import shutil
import sys

exchange = Path(sys.argv[-1])
source = next((exchange / "inputs").glob("*.tif"))
target = exchange / "outputs" / "image_reviewed.tif"
target.parent.mkdir(exist_ok=True)
shutil.copyfile(source, target)
""".strip(),
    )
    block = _make_running(FijiBlock())
    image = _make_image(np.arange(16, dtype=np.uint8).reshape(4, 4))

    result = block.run(
        {"image": Collection(items=[image], item_type=Image)},
        BlockConfig(params={"app_command": [sys.executable, str(script)], "watch_timeout": 5}),
    )

    assert "image" in result
    assert result["image"].length == 1
    assert result["image"][0].shape == image.shape


def test_napari_block_routes_image_outputs(tmp_path: Path) -> None:
    script = _write_fake_tool(
        tmp_path,
        """
from pathlib import Path
import shutil
import sys

exchange = Path(sys.argv[-1])
source = next((exchange / "inputs").glob("*.tif"))
target = exchange / "outputs" / "image_layer.tif"
target.parent.mkdir(exist_ok=True)
shutil.copyfile(source, target)
""".strip(),
    )
    block = _make_running(NapariBlock())
    image = _make_image(np.arange(25, dtype=np.uint8).reshape(5, 5))

    result = block.run(
        {"image": Collection(items=[image], item_type=Image)},
        BlockConfig(params={"app_command": [sys.executable, str(script)], "watch_timeout": 5}),
    )

    assert "image" in result
    assert result["image"].length == 1
    assert result["image"][0].shape == image.shape


def test_cell_profiler_block_routes_measurements_and_label(tmp_path: Path) -> None:
    script = _write_fake_tool(
        tmp_path,
        """
from pathlib import Path
import shutil
import sys

exchange = Path(sys.argv[-1])
source = next((exchange / "inputs").glob("*.tif"))
output_dir = exchange / "outputs"
output_dir.mkdir(exist_ok=True)
shutil.copyfile(source, output_dir / "label_output.tif")
(output_dir / "measurements.csv").write_text("object_id,area\\n1,42\\n", encoding="utf-8")
""".strip(),
    )
    pipeline = tmp_path / "pipeline.cppipe"
    pipeline.write_text("fake pipeline", encoding="utf-8")
    block = _make_running(CellProfilerBlock())
    image = _make_image(np.arange(16, dtype=np.uint8).reshape(4, 4))

    result = block.run(
        {"image": Collection(items=[image], item_type=Image)},
        BlockConfig(
            params={
                "app_command": [sys.executable, str(script)],
                "pipeline_path": str(pipeline),
                "watch_timeout": 5,
            }
        ),
    )

    assert "label" in result
    assert "measurements" in result
    assert result["label"].length == 1
    assert result["measurements"][0].row_count == 1


def test_qupath_block_routes_measurements(tmp_path: Path) -> None:
    script = _write_fake_tool(
        tmp_path,
        """
from pathlib import Path
import sys

exchange = Path(sys.argv[-1])
output_dir = exchange / "outputs"
output_dir.mkdir(exist_ok=True)
(output_dir / "measurements.csv").write_text("cell_id,intensity\\n1,3.14\\n", encoding="utf-8")
""".strip(),
    )
    tool_script = tmp_path / "analysis.groovy"
    tool_script.write_text("// fake script", encoding="utf-8")
    block = _make_running(QuPathBlock())
    image = _make_image(np.arange(9, dtype=np.uint8).reshape(3, 3))

    result = block.run(
        {"image": Collection(items=[image], item_type=Image)},
        BlockConfig(
            params={
                "app_command": [sys.executable, str(script)],
                "script_path": str(tool_script),
                "watch_timeout": 5,
            }
        ),
    )

    assert "measurements" in result
    assert result["measurements"][0].row_count == 1
