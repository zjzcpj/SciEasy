"""Sprint C imaging continuation B — skeleton stub tests (T-IMG-021..037).

Each test asserts the skeleton class exists and inherits from the
expected base. Behavioural tests are deferred to the impl agent and
marked via ``pytest.skip``.
"""

from __future__ import annotations

import numpy as np
import pytest

from scieasy.blocks.app.app_block import AppBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.array import Array


# ── T-IMG-021 ──────────────────────────────────────────────────────────
def test_t_img_021_connected_components_class() -> None:
    from scieasy_blocks_imaging.segmentation.connected_components import (
        ConnectedComponents,
    )

    assert issubclass(ConnectedComponents, ProcessBlock)
    assert ConnectedComponents.type_name == "imaging.connected_components"


def test_t_img_021_4_conn_label() -> None:
    from scieasy_blocks_imaging.segmentation.connected_components import (
        ConnectedComponents,
    )
    from scieasy_blocks_imaging.types import Mask

    arr = np.zeros((5, 5), dtype=bool)
    arr[1, 1] = True
    arr[2, 2] = True

    mask = Mask(axes=["y", "x"], shape=arr.shape, dtype=bool)
    mask._data = arr  # type: ignore[attr-defined]
    label = ConnectedComponents().process_item(mask, BlockConfig(params={"connectivity": 1}))

    assert label.meta is not None
    assert label.meta.n_objects == 2


def test_t_img_021_8_conn_label() -> None:
    from scieasy_blocks_imaging.segmentation.connected_components import (
        ConnectedComponents,
    )
    from scieasy_blocks_imaging.types import Mask

    arr = np.zeros((5, 5), dtype=bool)
    arr[1, 1] = True
    arr[2, 2] = True

    mask = Mask(axes=["y", "x"], shape=arr.shape, dtype=bool)
    mask._data = arr  # type: ignore[attr-defined]
    label = ConnectedComponents().process_item(mask, BlockConfig(params={"connectivity": 2}))

    assert label.meta is not None
    assert label.meta.n_objects == 1


def test_t_img_021_invalid_connectivity_raises() -> None:
    from scieasy_blocks_imaging.segmentation.connected_components import (
        ConnectedComponents,
    )
    from scieasy_blocks_imaging.types import Mask

    arr = np.ones((4, 4), dtype=bool)
    mask = Mask(axes=["y", "x"], shape=arr.shape, dtype=bool)
    mask._data = arr  # type: ignore[attr-defined]

    with pytest.raises(ValueError, match="connectivity"):
        ConnectedComponents().process_item(mask, BlockConfig(params={"connectivity": 3}))


# ── T-IMG-022 ──────────────────────────────────────────────────────────
def test_t_img_022_cleanup_classes() -> None:
    from scieasy_blocks_imaging.segmentation.cleanup import (
        ExpandLabels,
        FillHoles,
        RemoveBorderObjects,
        RemoveSmallObjects,
        ShrinkLabels,
    )

    for cls in (
        RemoveSmallObjects,
        RemoveBorderObjects,
        FillHoles,
        ExpandLabels,
        ShrinkLabels,
    ):
        assert issubclass(cls, ProcessBlock), cls


def test_t_img_022_remove_small_objects_min_size() -> None:
    pytest.importorskip("skimage")
    from scieasy_blocks_imaging.segmentation.cleanup import RemoveSmallObjects
    from scieasy_blocks_imaging.types import Mask

    arr = np.zeros((8, 8), dtype=bool)
    arr[1, 1] = True
    arr[3:7, 3:7] = True
    mask = Mask(axes=["y", "x"], shape=arr.shape, dtype=bool)
    mask._data = arr  # type: ignore[attr-defined]

    result = RemoveSmallObjects().process_item(mask, BlockConfig(params={"min_size": 4}))

    assert np.count_nonzero(np.asarray(result._data)) == 16


def test_t_img_022_fill_holes_basic() -> None:
    pytest.importorskip("scipy")
    from scieasy_blocks_imaging.segmentation.cleanup import FillHoles
    from scieasy_blocks_imaging.types import Mask

    arr = np.ones((7, 7), dtype=bool)
    arr[3, 3] = False
    mask = Mask(axes=["y", "x"], shape=arr.shape, dtype=bool)
    mask._data = arr  # type: ignore[attr-defined]

    result = FillHoles().process_item(mask, BlockConfig(params={}))

    assert bool(np.asarray(result._data)[3, 3]) is True


def test_t_img_022_expand_shrink_labels() -> None:
    pytest.importorskip("skimage")
    from scieasy_blocks_imaging.segmentation.cleanup import ExpandLabels, ShrinkLabels
    from scieasy_blocks_imaging.types import Label

    arr = np.zeros((11, 11), dtype=np.int32)
    arr[4:7, 4:7] = 1
    raster = Array(axes=["y", "x"], shape=arr.shape, dtype=arr.dtype)
    raster._data = arr  # type: ignore[attr-defined]
    label = Label(slots={"raster": raster}, meta=Label.Meta(source_file="label.tif", n_objects=1))

    expanded = ExpandLabels().process_item(label, BlockConfig(params={"distance_px": 2}))
    shrunk = ShrinkLabels().process_item(expanded, BlockConfig(params={"distance_px": 1}))

    assert np.count_nonzero(np.asarray(expanded.slots["raster"]._data)) > np.count_nonzero(arr)
    assert np.count_nonzero(np.asarray(shrunk.slots["raster"]._data)) < np.count_nonzero(
        np.asarray(expanded.slots["raster"]._data)
    )
    assert shrunk.meta is not None
    assert shrunk.meta.source_file == "label.tif"


# ── T-IMG-023 ──────────────────────────────────────────────────────────
def test_t_img_023_track_objects_class() -> None:
    from scieasy_blocks_imaging.tracking.track_objects import TrackObjects

    assert issubclass(TrackObjects, ProcessBlock)


def test_t_img_023_process_item_raises_not_implemented() -> None:
    pytest.skip("T-IMG-023 placeholder; Phase 12 impl pending")


# ── T-IMG-024 ──────────────────────────────────────────────────────────
def test_t_img_024_region_props_class() -> None:
    from scieasy_blocks_imaging.measurement.region_props import RegionProps

    assert issubclass(RegionProps, ProcessBlock)


def test_t_img_024_area_basic() -> None:
    pytest.skip("T-IMG-024 impl pending")


def test_t_img_024_intensity_image() -> None:
    pytest.skip("T-IMG-024 impl pending")


# ── T-IMG-025 ──────────────────────────────────────────────────────────
def test_t_img_025_pairwise_distance_class() -> None:
    from scieasy_blocks_imaging.measurement.pairwise_distance import (
        PairwiseDistance,
    )

    assert issubclass(PairwiseDistance, ProcessBlock)


def test_t_img_025_centroid_metric() -> None:
    pytest.skip("T-IMG-025 impl pending")


# ── T-IMG-026 ──────────────────────────────────────────────────────────
def test_t_img_026_colocalization_class() -> None:
    from scieasy_blocks_imaging.measurement.colocalization import Colocalization

    assert issubclass(Colocalization, ProcessBlock)


def test_t_img_026_pearson_basic() -> None:
    pytest.skip("T-IMG-026 impl pending")


# ── T-IMG-027 ──────────────────────────────────────────────────────────
def test_t_img_027_compute_registration_class() -> None:
    from scieasy_blocks_imaging.registration.compute_registration import (
        ComputeRegistration,
    )

    assert issubclass(ComputeRegistration, ProcessBlock)


def test_t_img_027_phase_correlation() -> None:
    pytest.skip("T-IMG-027 impl pending")


# ── T-IMG-028 ──────────────────────────────────────────────────────────
def test_t_img_028_apply_transform_class() -> None:
    from scieasy_blocks_imaging.registration.apply_transform import ApplyTransform

    assert issubclass(ApplyTransform, ProcessBlock)


def test_t_img_028_warp_basic() -> None:
    pytest.skip("T-IMG-028 impl pending")


# ── T-IMG-029 ──────────────────────────────────────────────────────────
def test_t_img_029_register_series_class() -> None:
    from scieasy_blocks_imaging.registration.register_series import RegisterSeries

    assert issubclass(RegisterSeries, ProcessBlock)


def test_t_img_029_align_to_reference() -> None:
    pytest.skip("T-IMG-029 impl pending")


# ── T-IMG-030 ──────────────────────────────────────────────────────────
def test_t_img_030_projection_classes() -> None:
    from scieasy_blocks_imaging.projection.projection import (
        AxisProjection,
        SelectSlice,
    )

    for cls in (AxisProjection, SelectSlice):
        assert issubclass(cls, ProcessBlock), cls


def test_t_img_030_axis_projection_max() -> None:
    pytest.skip("T-IMG-030 impl pending")


def test_t_img_030_select_slice_index() -> None:
    pytest.skip("T-IMG-030 impl pending")


# ── T-IMG-031 ──────────────────────────────────────────────────────────
def test_t_img_031_scalar_op_classes() -> None:
    from scieasy_blocks_imaging.math.scalar_ops import (
        AddScalar,
        DivideScalar,
        MultiplyScalar,
        SubtractScalar,
    )

    for cls in (AddScalar, SubtractScalar, MultiplyScalar, DivideScalar):
        assert issubclass(cls, ProcessBlock), cls


def test_t_img_031_add_subtract_basic() -> None:
    pytest.skip("T-IMG-031 impl pending")


def test_t_img_031_divide_by_zero_raises() -> None:
    pytest.skip("T-IMG-031 impl pending")


# ── T-IMG-032 ──────────────────────────────────────────────────────────
def test_t_img_032_image_calculator_class() -> None:
    from scieasy_blocks_imaging.math.image_calculator import ImageCalculator

    assert issubclass(ImageCalculator, ProcessBlock)
    assert len(ImageCalculator.input_ports) == 2  # 2-port FIXED


def test_t_img_032_simple_expression() -> None:
    pytest.skip("T-IMG-032 impl pending")


def test_t_img_032_invalid_expression_raises() -> None:
    pytest.skip("T-IMG-032 impl pending")


# ── T-IMG-033 ──────────────────────────────────────────────────────────
def test_t_img_033_render_classes() -> None:
    from scieasy_blocks_imaging.visualization.render import (
        RenderHistogram,
        RenderMontage,
        RenderMovie,
        RenderOverlay,
        RenderPseudoColor,
    )

    for cls in (
        RenderPseudoColor,
        RenderOverlay,
        RenderMontage,
        RenderMovie,
        RenderHistogram,
    ):
        assert issubclass(cls, ProcessBlock), cls


def test_t_img_033_pseudo_color_lut() -> None:
    pytest.skip("T-IMG-033 impl pending")


def test_t_img_033_overlay_alpha() -> None:
    pytest.skip("T-IMG-033 impl pending")


# ── T-IMG-034 ──────────────────────────────────────────────────────────
def test_t_img_034_fiji_block_class() -> None:
    from scieasy_blocks_imaging.interactive.fiji_block import FijiBlock

    assert issubclass(FijiBlock, AppBlock)
    assert FijiBlock.app_command == r"C:\Program Files\Fiji\fiji-windows-x64.exe"


def test_t_img_034_run_routes_outputs() -> None:
    pytest.skip("T-IMG-034 impl pending")


# ── T-IMG-035 ──────────────────────────────────────────────────────────
def test_t_img_035_napari_block_class() -> None:
    from scieasy_blocks_imaging.interactive.napari_block import NapariBlock

    assert issubclass(NapariBlock, AppBlock)
    assert NapariBlock.app_command == "napari"


def test_t_img_035_run_routes_outputs() -> None:
    pytest.skip("T-IMG-035 impl pending")


# ── T-IMG-036 ──────────────────────────────────────────────────────────
def test_t_img_036_cell_profiler_block_class() -> None:
    from scieasy_blocks_imaging.interactive.cell_profiler_block import (
        CellProfilerBlock,
    )

    assert issubclass(CellProfilerBlock, AppBlock)
    assert CellProfilerBlock.app_command == "cellprofiler"


def test_t_img_036_run_routes_outputs() -> None:
    pytest.skip("T-IMG-036 impl pending")


# ── T-IMG-037 ──────────────────────────────────────────────────────────
def test_t_img_037_qupath_block_class() -> None:
    from scieasy_blocks_imaging.interactive.qupath_block import QuPathBlock

    assert issubclass(QuPathBlock, AppBlock)
    assert QuPathBlock.app_command == "qupath"


def test_t_img_037_run_routes_outputs() -> None:
    pytest.skip("T-IMG-037 impl pending")
