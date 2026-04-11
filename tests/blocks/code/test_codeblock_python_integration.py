"""T-TRK-014: CodeBlock Python runner end-to-end integration.

Per ``docs/specs/phase11-implementation-standards.md`` §T-TRK-014, this
module drives ``CodeBlock(language="python")`` through two realistic
user pipelines and verifies that Collection auto-unpack/repack
(ADR-020-Add4) produces correctly shaped and typed results:

1. ``test_codeblock_python_skimage_workflow`` — loads the T-TRK-003
   segmentation test images from ``tests/fixtures/test_images.py``,
   runs a gaussian-filter + Otsu-threshold pipeline through a Python
   inline CodeBlock, and asserts the output is a length-2
   ``Collection`` of :class:`Array` instances.
2. ``test_codeblock_python_collection_unpack`` — wraps three
   :class:`DataFrame` items in a single Collection, normalises each
   frame inside the script, and asserts the output is a length-3
   ``Collection`` of processed DataFrames.

Both tests operate on data persisted through the real storage backends
(Zarr for ``Array``, Arrow for ``DataFrame``) — ADR-031 D2.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from scieasy.blocks.base.state import BlockState
from scieasy.blocks.code.code_block import CodeBlock
from scieasy.core.types.array import Array
from scieasy.core.types.base import DataObject
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from tests.fixtures.test_images import SEGMENTATION_IMAGES, TEST_IMAGES_DIR

# Per spec Q6: skip module if the T-TRK-003 test-image directory is absent.
if not TEST_IMAGES_DIR.exists():
    pytest.skip("test images unavailable", allow_module_level=True)


def _load_tiff_as_array(path: Path, storage_dir: Path) -> Array:
    """Load a TIFF via tifffile and persist to zarr (ADR-031 D2)."""
    import uuid

    from scieasy.core.storage.ref import StorageReference
    from scieasy.core.storage.zarr_backend import ZarrBackend

    tifffile = pytest.importorskip("tifffile")
    data = np.asarray(tifffile.imread(str(path)))
    zarr_path = str(storage_dir / f"{uuid.uuid4()}.zarr")
    ref = ZarrBackend().write(data, StorageReference(backend="zarr", path=zarr_path))
    return Array(axes=["y", "x"], shape=tuple(data.shape), dtype=str(data.dtype), storage_ref=ref)


def test_codeblock_python_skimage_workflow(tmp_path: Path) -> None:
    """Run a gaussian + threshold skimage pipeline through a CodeBlock.

    The block receives a multi-item ``Collection`` (auto-unpacked into
    a :class:`LazyList`), the script iterates, builds a processed
    ``Array`` per input, and the block repacks the returned list into
    a new ``Collection``.
    """
    pytest.importorskip("skimage")
    pytest.importorskip("zarr")

    stored: list[DataObject] = []
    for img_path in SEGMENTATION_IMAGES:
        arr = _load_tiff_as_array(img_path, tmp_path)
        stored.append(arr)
    assert len(stored) == 2, "T-TRK-003 should provide exactly two segmentation images"

    input_collection = Collection(stored, item_type=Array)

    # Inline script: iterate the LazyList, gaussian-filter, Otsu-threshold,
    # wrap each mask back into an Array, and return a list.
    script = (
        "import tempfile, uuid\n"
        "import numpy as np\n"
        "from skimage.filters import gaussian, threshold_otsu\n"
        "from scieasy.core.types.array import Array\n"
        "from scieasy.core.storage.zarr_backend import ZarrBackend\n"
        "from scieasy.core.storage.ref import StorageReference\n"
        "from pathlib import Path\n"
        "processed = []\n"
        "for item in data:\n"
        "    raw = np.asarray(item)\n"
        "    smoothed = gaussian(raw, sigma=1.0, preserve_range=True)\n"
        "    mask = smoothed > threshold_otsu(smoothed)\n"
        "    arr = mask.astype(np.uint8)\n"
        "    p = str(Path(tempfile.gettempdir()) / f'{uuid.uuid4()}.zarr')\n"
        "    ref = ZarrBackend().write(arr, StorageReference(backend='zarr', path=p))\n"
        "    out = Array(axes=['y', 'x'], shape=tuple(arr.shape), dtype=str(arr.dtype), storage_ref=ref)\n"
        "    processed.append(out)\n"
    )

    block = CodeBlock(config={"params": {"script": script}})
    block.transition(BlockState.READY)
    outputs = block.run({"data": input_collection}, block.config)

    assert "processed" in outputs, f"expected 'processed' key, got {list(outputs)}"
    result = outputs["processed"]
    assert isinstance(result, Collection), f"expected Collection, got {type(result).__name__}"
    assert len(result) == 2
    for item in result:
        assert isinstance(item, Array)
        assert item.axes == ["y", "x"]
        assert item.shape is not None and len(item.shape) == 2


def test_codeblock_python_collection_unpack(tmp_path: Path) -> None:
    """Feed a Collection of three DataFrames through a Python CodeBlock.

    Verifies that auto-unpack wraps the multi-item Collection in a
    LazyList, the script can iterate and produce three new DataFrames,
    and auto-repack emits a length-3 ``Collection[DataFrame]``.
    """
    pytest.importorskip("pyarrow")
    pa = pytest.importorskip("pyarrow")

    # Build three distinct DataFrames, persist each to its own Arrow file.
    from scieasy.core.storage.arrow_backend import ArrowBackend
    from scieasy.core.storage.ref import StorageReference

    source: list[DataObject] = []
    tables = [
        pa.table({"x": [1, 2, 3], "y": [10, 20, 30]}),
        pa.table({"x": [4, 5, 6], "y": [40, 50, 60]}),
        pa.table({"x": [7, 8, 9], "y": [70, 80, 90]}),
    ]
    for i, tbl in enumerate(tables):
        ref = ArrowBackend().write(tbl, StorageReference(backend="arrow", path=str(tmp_path / f"df_{i}.parquet")))
        df = DataFrame(columns=["x", "y"], row_count=tbl.num_rows, storage_ref=ref)
        source.append(df)

    input_collection = Collection(source, item_type=DataFrame)

    # Script: for each loaded table, add a 'sum' column, persist, and collect.
    script = (
        "import tempfile, uuid\n"
        "import pyarrow as pa\n"
        "import pyarrow.compute as pc\n"
        "from pathlib import Path\n"
        "from scieasy.core.types.dataframe import DataFrame\n"
        "from scieasy.core.storage.arrow_backend import ArrowBackend\n"
        "from scieasy.core.storage.ref import StorageReference\n"
        "processed = []\n"
        "for item in data:\n"
        "    tbl = item.to_memory()\n"
        "    s = pc.add(tbl.column('x'), tbl.column('y'))\n"
        "    new_tbl = tbl.append_column('sum', s)\n"
        "    p = str(Path(tempfile.gettempdir()) / f'{uuid.uuid4()}.parquet')\n"
        "    ref = ArrowBackend().write(new_tbl, StorageReference(backend='arrow', path=p))\n"
        "    out = DataFrame(columns=list(new_tbl.column_names), row_count=new_tbl.num_rows, storage_ref=ref)\n"
        "    processed.append(out)\n"
    )

    block = CodeBlock(config={"params": {"script": script}})
    block.transition(BlockState.READY)
    outputs = block.run({"data": input_collection}, block.config)

    assert "processed" in outputs
    result = outputs["processed"]
    assert isinstance(result, Collection)
    assert len(result) == 3
    for item in result:
        assert isinstance(item, DataFrame)
        assert item.columns is not None and "sum" in item.columns
        assert item.row_count == 3
