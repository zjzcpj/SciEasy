"""Phase 11 skeleton smoke test.

Verifies that every placeholder module in the three plugin packages is
importable and that a representative placeholder class raises
``NotImplementedError`` when instantiated.

This test is intentionally tautological — its purpose is to catch silent
scope drift in the skeleton PR, not to validate business logic. Each
implementation agent replaces the ``NotImplementedError`` body with real
code and updates its own ticket's tests.

The plugin packages are not yet ``pip install``-ed at skeleton time, so
this test prepends their ``src`` directories to ``sys.path`` before
importing. Once the Sprint C/D/E packaging tickets (T-IMG-038 /
T-SRS-013 / T-LCMS-020) land and each plugin is installed editable in
CI, this shim becomes redundant and the test keeps passing via the
normal import path. See
``docs/specs/phase11-implementation-standards.md`` §Q4 for context.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PLUGIN_SRC_DIRS = [
    _REPO_ROOT / "packages" / "scieasy-blocks-imaging" / "src",
    _REPO_ROOT / "packages" / "scieasy-blocks-srs" / "src",
    _REPO_ROOT / "packages" / "scieasy-blocks-lcms" / "src",
]
for _src in _PLUGIN_SRC_DIRS:
    _src_str = str(_src)
    if _src.is_dir() and _src_str not in sys.path:
        sys.path.insert(0, _src_str)


PLUGIN_MODULES: list[str] = [
    # ── imaging ─────────────────────────────────────────────────────
    "scieasy_blocks_imaging",
    "scieasy_blocks_imaging.types",
    "scieasy_blocks_imaging.io",
    "scieasy_blocks_imaging.io.load_image",
    "scieasy_blocks_imaging.io.save_image",
    "scieasy_blocks_imaging.preprocess",
    "scieasy_blocks_imaging.preprocess.denoise",
    "scieasy_blocks_imaging.preprocess.background_subtract",
    "scieasy_blocks_imaging.preprocess.normalize",
    "scieasy_blocks_imaging.preprocess.flat_field_correct",
    "scieasy_blocks_imaging.preprocess.geometry",
    "scieasy_blocks_imaging.preprocess.convert_dtype",
    "scieasy_blocks_imaging.preprocess.axis_ops",
    "scieasy_blocks_imaging.preprocess.deconvolve",
    "scieasy_blocks_imaging.morphology",
    "scieasy_blocks_imaging.morphology.morphology_op",
    "scieasy_blocks_imaging.morphology.edge_detect",
    "scieasy_blocks_imaging.morphology.ridge_filter",
    "scieasy_blocks_imaging.morphology.sharpen",
    "scieasy_blocks_imaging.morphology.fft_filter",
    "scieasy_blocks_imaging.segmentation",
    "scieasy_blocks_imaging.segmentation.threshold",
    "scieasy_blocks_imaging.segmentation.watershed",
    "scieasy_blocks_imaging.segmentation.cellpose_segment",
    "scieasy_blocks_imaging.segmentation.blob_detect",
    "scieasy_blocks_imaging.segmentation.connected_components",
    "scieasy_blocks_imaging.segmentation.cleanup",
    "scieasy_blocks_imaging.tracking",
    "scieasy_blocks_imaging.tracking.track_objects",
    "scieasy_blocks_imaging.measurement",
    "scieasy_blocks_imaging.measurement.region_props",
    "scieasy_blocks_imaging.measurement.pairwise_distance",
    "scieasy_blocks_imaging.measurement.colocalization",
    "scieasy_blocks_imaging.registration",
    "scieasy_blocks_imaging.registration.compute_registration",
    "scieasy_blocks_imaging.registration.apply_transform",
    "scieasy_blocks_imaging.registration.register_series",
    "scieasy_blocks_imaging.projection",
    "scieasy_blocks_imaging.projection.projection",
    "scieasy_blocks_imaging.math",
    "scieasy_blocks_imaging.math.scalar_ops",
    "scieasy_blocks_imaging.math.image_calculator",
    "scieasy_blocks_imaging.visualization",
    "scieasy_blocks_imaging.visualization.render",
    "scieasy_blocks_imaging.interactive",
    "scieasy_blocks_imaging.interactive.fiji_block",
    "scieasy_blocks_imaging.interactive.napari_block",
    "scieasy_blocks_imaging.interactive.cell_profiler_block",
    "scieasy_blocks_imaging.interactive.qupath_block",
    # ── SRS ─────────────────────────────────────────────────────────
    "scieasy_blocks_srs",
    "scieasy_blocks_srs.types",
    "scieasy_blocks_srs.preprocess",
    "scieasy_blocks_srs.preprocess.srs_calibrate",
    "scieasy_blocks_srs.preprocess.srs_baseline",
    "scieasy_blocks_srs.preprocess.srs_denoise",
    "scieasy_blocks_srs.preprocess.srs_normalize",
    "scieasy_blocks_srs.component_analysis",
    "scieasy_blocks_srs.component_analysis.srs_vca",
    "scieasy_blocks_srs.component_analysis.srs_unmix",
    "scieasy_blocks_srs.component_analysis.srs_pca",
    "scieasy_blocks_srs.component_analysis.srs_ica",
    "scieasy_blocks_srs.component_analysis.srs_kmeans",
    "scieasy_blocks_srs.spectral_extraction",
    "scieasy_blocks_srs.spectral_extraction.extract_spectrum",
    "scieasy_blocks_srs.spectral_extraction.band_ratio",
    # ── LC-MS ───────────────────────────────────────────────────────
    "scieasy_blocks_lcms",
    "scieasy_blocks_lcms.types",
    "scieasy_blocks_lcms.io",
    "scieasy_blocks_lcms.io.load_ms_raw_files",
    "scieasy_blocks_lcms.io.load_peak_table",
    "scieasy_blocks_lcms.io.load_mid_table",
    "scieasy_blocks_lcms.io.load_sample_metadata",
    "scieasy_blocks_lcms.io.save_table",
    "scieasy_blocks_lcms.external",
    "scieasy_blocks_lcms.external.elmaven_block",
    "scieasy_blocks_lcms.external.accucor_r",
    "scieasy_blocks_lcms.external.graphpad_block",
    "scieasy_blocks_lcms.isotope_tracing",
    "scieasy_blocks_lcms.isotope_tracing.calculate_13c_enrichment",
    "scieasy_blocks_lcms.isotope_tracing.fractional_labeling",
    "scieasy_blocks_lcms.isotope_tracing.compare_group_mid",
    "scieasy_blocks_lcms.isotope_tracing.flux_estimate",
    "scieasy_blocks_lcms.isotope_tracing.pool_size_normalize",
    "scieasy_blocks_lcms.analysis",
    "scieasy_blocks_lcms.analysis.metabolite_matrix",
    "scieasy_blocks_lcms.analysis.matrix_preprocess",
    "scieasy_blocks_lcms.analysis.univariate_stats",
    "scieasy_blocks_lcms.analysis.multivariate_analysis",
    "scieasy_blocks_lcms.analysis.pathway_enrichment",
    "scieasy_blocks_lcms.analysis.consumption_secretion_analysis",
]


@pytest.mark.parametrize("module_name", PLUGIN_MODULES)
def test_skeleton_module_importable(module_name: str) -> None:
    """Every placeholder module imports cleanly (no ``NotImplementedError``
    at import time, no typos, no missing ``__init__.py`` files)."""
    importlib.import_module(module_name)


# ── Sprint C imaging continuation A (T-IMG-002..020) — issue #350 ────────
# These 19 modules are upgraded from one-line placeholders to full
# skeleton classes (ClassVars + method signatures + NotImplementedError
# bodies). The parametrized test below pins the contract: every module
# must remain importable after the impl agent fills the bodies in.
_CONTINUATION_A_MODULES: list[str] = [
    "scieasy_blocks_imaging.io.load_image",
    "scieasy_blocks_imaging.io.save_image",
    "scieasy_blocks_imaging.preprocess.denoise",
    "scieasy_blocks_imaging.preprocess.background_subtract",
    "scieasy_blocks_imaging.preprocess.normalize",
    "scieasy_blocks_imaging.preprocess.flat_field_correct",
    "scieasy_blocks_imaging.preprocess.geometry",
    "scieasy_blocks_imaging.preprocess.convert_dtype",
    "scieasy_blocks_imaging.preprocess.axis_ops",
    "scieasy_blocks_imaging.preprocess.deconvolve",
    "scieasy_blocks_imaging.morphology.morphology_op",
    "scieasy_blocks_imaging.morphology.edge_detect",
    "scieasy_blocks_imaging.morphology.ridge_filter",
    "scieasy_blocks_imaging.morphology.sharpen",
    "scieasy_blocks_imaging.morphology.fft_filter",
    "scieasy_blocks_imaging.segmentation.threshold",
    "scieasy_blocks_imaging.segmentation.watershed",
    "scieasy_blocks_imaging.segmentation.cellpose_segment",
    "scieasy_blocks_imaging.segmentation.blob_detect",
]


@pytest.mark.parametrize("module_name", _CONTINUATION_A_MODULES)
def test_continuation_a_modules_importable(module_name: str) -> None:
    """Sprint C continuation A skeletons (T-IMG-002..020) importable."""
    importlib.import_module(module_name)


def test_image_placeholder_raises() -> None:
    """T-IMG-001 has landed (Sprint C imaging skeleton, PR #346).

    This smoke test was originally added by PR #309 to verify the bare
    placeholder for T-IMG-001 raised NotImplementedError on construction.
    The Sprint C imaging skeleton agent has now upgraded T-IMG-001 to a
    proper ``Image(Array)`` skeleton with `required_axes`, `Meta` model,
    and validators. The new behavior is verified by the dedicated test
    file at ``packages/scieasy-blocks-imaging/tests/test_types.py``.

    Per CLAUDE.md §6.7 (tests are part of the change), this smoke-test
    function is preserved as a marker that T-IMG-001 reached "skeleton
    complete" status. Construction is now skipped here — the per-plugin
    test file is the authoritative coverage.
    """
    pytest.skip("T-IMG-001 skeleton landed; coverage moved to packages/scieasy-blocks-imaging/tests/test_types.py")


def test_srs_image_placeholder_raises() -> None:
    """Representative: instantiating T-SRS-001 SRSImage raises NotImplementedError."""
    pytest.skip("T-SRS-001 skeleton landed; coverage moved to packages/scieasy-blocks-srs/tests/test_types.py")


def test_lcms_types_placeholder_raises() -> None:
    """Representative: T-LCMS-002 get_types() is now concrete."""
    from scieasy_blocks_lcms.types import get_types

    names = [cls.__name__ for cls in get_types()]
    assert names == ["MSRawFile", "PeakTable", "MIDTable", "SampleMetadata"]


def test_lcms_foundation_chunk1_impl_smoke(tmp_path: Path) -> None:
    """Smoke test that LCMS foundation chunk 1 bodies are concrete."""
    pytest.importorskip("pandas")
    from scieasy_blocks_lcms.external.accucor_r import AccuCorR
    from scieasy_blocks_lcms.io.load_mid_table import LoadMIDTable
    from scieasy_blocks_lcms.io.load_ms_raw_files import LoadMSRawFiles
    from scieasy_blocks_lcms.io.load_peak_table import LoadPeakTable
    from scieasy_blocks_lcms.io.load_sample_metadata import LoadSampleMetadata
    from scieasy_blocks_lcms.types import MSRawFile

    from scieasy.blocks.base.config import BlockConfig

    mzml_path = tmp_path / "sample.mzML"
    mzml_path.write_text(
        '<mzML><run startTimeStamp="2026-04-08T01:02:03Z"><instrumentConfiguration id="IC1" name="QE" />'
        '<cvParam accession="MS:1000130" /></run></mzML>',
        encoding="utf-8",
    )
    raw_files = LoadMSRawFiles().load(BlockConfig(params={"path": str(tmp_path), "pattern": "*.mzML"}))
    assert isinstance(raw_files[0], MSRawFile)

    peak_path = tmp_path / "peak.csv"
    peak_path.write_text("compound,formula,medMz,medRt\nglucose,C6H12O6,179.0,5.2\n", encoding="utf-8")
    peak_table = LoadPeakTable().load(BlockConfig(params={"path": str(peak_path)}))[0]
    assert peak_table.meta.source == "ElMAVEN"

    sample_meta_path = tmp_path / "sample_metadata.csv"
    sample_meta_path.write_text("sample_id,group\nS1,UL\n", encoding="utf-8")
    sample_metadata = LoadSampleMetadata().load(BlockConfig(params={"path": str(sample_meta_path)}))[0]
    assert sample_metadata.meta.sample_id_column == "sample_id"

    mid_path = tmp_path / "mid.csv"
    mid_path.write_text("Compound,C13,S1\nglucose,0,1.0\n", encoding="utf-8")
    mid_table = LoadMIDTable().load(BlockConfig(params={"path": str(mid_path)}))[0]
    assert mid_table.meta.correction_tool == "AccuCor"

    script_path = AccuCorR()._resolve_script_path(BlockConfig(params={}))
    assert Path(script_path).exists()


_CONTINUATION_B_MODULES = [
    "scieasy_blocks_imaging.segmentation.connected_components",
    "scieasy_blocks_imaging.segmentation.cleanup",
    "scieasy_blocks_imaging.tracking.track_objects",
    "scieasy_blocks_imaging.measurement.region_props",
    "scieasy_blocks_imaging.measurement.pairwise_distance",
    "scieasy_blocks_imaging.measurement.colocalization",
    "scieasy_blocks_imaging.registration.compute_registration",
    "scieasy_blocks_imaging.registration.apply_transform",
    "scieasy_blocks_imaging.registration.register_series",
    "scieasy_blocks_imaging.projection.projection",
    "scieasy_blocks_imaging.math.scalar_ops",
    "scieasy_blocks_imaging.math.image_calculator",
    "scieasy_blocks_imaging.visualization.render",
    "scieasy_blocks_imaging.interactive.fiji_block",
    "scieasy_blocks_imaging.interactive.napari_block",
    "scieasy_blocks_imaging.interactive.cell_profiler_block",
    "scieasy_blocks_imaging.interactive.qupath_block",
]


@pytest.mark.parametrize("module_name", _CONTINUATION_B_MODULES)
def test_continuation_b_modules_importable(module_name: str) -> None:
    """Sprint C imaging continuation B skeletons importable (T-IMG-021..037).

    Each module exposes its block class(es) inheriting from ``ProcessBlock``
    or ``AppBlock`` with full ClassVar annotations. ``process_item`` / ``run``
    bodies raise ``NotImplementedError`` until the impl agent fills them in.
    """
    importlib.import_module(module_name)


def test_lcms_block_skeletons_inherit_real_bases() -> None:
    """Sanity-check #345: every LC-MS skeleton block subclasses a real base class.

    This guards against the regression where a placeholder file gets
    written but the class signature drifts away from the spec
    (e.g. forgetting to inherit from ``IOBlock`` / ``ProcessBlock`` /
    ``AppBlock`` / ``CodeBlock``). Each entry below pairs a block
    class with the lowest-level real base it must subclass.
    """
    from scieasy_blocks_lcms.analysis import (
        ConsumptionSecretionAnalysis,
        MatrixPreprocess,
        MetaboliteMatrix,
        MultivariateAnalysis,
        PathwayEnrichment,
        UnivariateStats,
    )
    from scieasy_blocks_lcms.external import AccuCorR, ElMAVENBlock, GraphPadBlock
    from scieasy_blocks_lcms.io import (
        LoadMIDTable,
        LoadMSRawFiles,
        LoadPeakTable,
        LoadSampleMetadata,
        SaveTable,
    )
    from scieasy_blocks_lcms.isotope_tracing import (
        Calculate13CEnrichment,
        CompareGroupMID,
        FluxEstimate,
        FractionalLabeling,
        PoolSizeNormalize,
    )

    from scieasy.blocks.app.app_block import AppBlock
    from scieasy.blocks.code.code_block import CodeBlock
    from scieasy.blocks.io.io_block import IOBlock
    from scieasy.blocks.process.process_block import ProcessBlock

    expected: list[tuple[type, type]] = [
        (LoadMSRawFiles, IOBlock),
        (LoadPeakTable, IOBlock),
        (LoadMIDTable, IOBlock),
        (LoadSampleMetadata, IOBlock),
        (SaveTable, IOBlock),
        (ElMAVENBlock, AppBlock),
        (AccuCorR, CodeBlock),
        (GraphPadBlock, AppBlock),
        (Calculate13CEnrichment, ProcessBlock),
        (FractionalLabeling, ProcessBlock),
        (CompareGroupMID, ProcessBlock),
        (FluxEstimate, ProcessBlock),
        (PoolSizeNormalize, ProcessBlock),
        (MetaboliteMatrix, ProcessBlock),
        (MatrixPreprocess, ProcessBlock),
        (UnivariateStats, ProcessBlock),
        (MultivariateAnalysis, ProcessBlock),
        (PathwayEnrichment, ProcessBlock),
        (ConsumptionSecretionAnalysis, ProcessBlock),
    ]
    for cls, base in expected:
        assert issubclass(cls, base), f"{cls.__name__} must subclass {base.__name__}"


def test_lcms_isotope_tracing_core_impl_smoke() -> None:
    """Smoke test that T-LCMS-008/T-LCMS-009 bodies are concrete (PR #371).

    This lives in the root ``tests/`` tree so the Phase 11 workflow
    compliance job recognizes the implementation PR as having top-level
    smoke coverage in addition to the package-local LCMS tests.
    """
    pd = pytest.importorskip("pandas")
    from scieasy_blocks_lcms.isotope_tracing import Calculate13CEnrichment, FractionalLabeling
    from scieasy_blocks_lcms.types import MIDTable

    from scieasy.blocks.base.config import BlockConfig

    frame = pd.DataFrame({"Compound": ["glucose", "glucose"], "C13": [0, 6], "S1": [0.4, 0.6]})
    mid = MIDTable(
        columns=list(frame.columns),
        row_count=len(frame),
        meta=MIDTable.Meta(tracer_atoms=["C13"], sample_columns=["S1"]),
    )
    mid._data = frame

    enrichment = Calculate13CEnrichment().process_item(mid, BlockConfig(params={}))._data
    fractional = FractionalLabeling().process_item(mid, BlockConfig(params={}))._data

    assert enrichment.loc[0, "enrichment"] == pytest.approx(0.6)
    assert fractional.loc[0, "fractional_labeling"] == pytest.approx(0.6)


def test_lcms_analysis_core_impl_smoke(tmp_path: Path) -> None:
    """Smoke test that the LCMS analysis core blocks are concrete."""
    pytest.importorskip("pandas")
    pytest.importorskip("scipy")
    pytest.importorskip("statsmodels")
    pytest.importorskip("sklearn")
    pytest.importorskip("matplotlib")

    import pandas as pd
    from scieasy_blocks_lcms.analysis.matrix_preprocess import MatrixPreprocess
    from scieasy_blocks_lcms.analysis.metabolite_matrix import MetaboliteMatrix
    from scieasy_blocks_lcms.analysis.multivariate_analysis import MultivariateAnalysis
    from scieasy_blocks_lcms.analysis.univariate_stats import UnivariateStats
    from scieasy_blocks_lcms.types import PeakTable, SampleMetadata

    from scieasy.blocks.base.config import BlockConfig
    from scieasy.core.types.collection import Collection

    long_frame = pd.DataFrame(
        {
            "compound": ["glucose", "glucose", "lactate", "lactate"],
            "sample_id": ["S1", "S2", "S1", "S2"],
            "intensity": [10.0, 12.0, 3.0, 6.0],
        }
    )
    peak = PeakTable(
        columns=list(long_frame.columns),
        row_count=len(long_frame),
        meta=PeakTable.Meta(source="ElMAVEN"),
    )
    peak._data = long_frame

    metadata_frame = pd.DataFrame({"sample_id": ["S1", "S2"], "group": ["A", "B"]})
    metadata = SampleMetadata(
        columns=list(metadata_frame.columns),
        row_count=len(metadata_frame),
        meta=SampleMetadata.Meta(sample_id_column="sample_id"),
    )
    metadata._data = metadata_frame

    matrix_out = MetaboliteMatrix().run(
        {
            "peak_table": Collection(items=[peak], item_type=PeakTable),
            "sample_metadata": Collection(items=[metadata], item_type=SampleMetadata),
        },
        BlockConfig(params={}),
    )
    matrix = matrix_out["matrix"][0]
    assert matrix._data.loc["glucose", "S1"] == pytest.approx(10.0)

    processed = MatrixPreprocess().process_item(matrix, BlockConfig(params={"impute_method": "none", "scale": "none"}))
    assert processed._data.shape == matrix._data.shape

    stats = UnivariateStats().run(
        {
            "matrix": Collection(items=[processed], item_type=type(processed)),
            "sample_metadata": Collection(items=[metadata], item_type=SampleMetadata),
        },
        BlockConfig(params={"group_column": "group", "test": "t-test", "correction": "none"}),
    )
    assert not stats["stats"][0]._data.empty

    multivariate = MultivariateAnalysis().run(
        {
            "matrix": Collection(items=[processed], item_type=type(processed)),
            "sample_metadata": Collection(items=[metadata], item_type=SampleMetadata),
        },
        BlockConfig(params={"method": "PCA"}),
    )
    assert multivariate["plot"][0].file_path is not None
    assert multivariate["plot"][0].file_path.exists()


def test_imaging_io_impl_smoke(tmp_path: Path) -> None:
    """Smoke test that T-IMG-002/T-IMG-003 bodies are concrete (impl PR #354).

    Instantiating :class:`LoadImage` and :class:`SaveImage` and running a
    tiny TIFF round-trip proves the skeleton ``NotImplementedError``
    stubs have been replaced. Deliberately placed in the top-level
    ``tests/plugins`` suite so the Phase 11 Verify Workflow Compliance
    gate (which requires ``tests/`` changes) recognises the impl PR.
    """
    pytest.importorskip("tifffile")
    import numpy as np
    from scieasy_blocks_imaging.io.load_image import LoadImage
    from scieasy_blocks_imaging.io.save_image import SaveImage
    from scieasy_blocks_imaging.types import Image

    from scieasy.blocks.base.config import BlockConfig
    from scieasy.core.types.collection import Collection

    arr = np.arange(6, dtype=np.uint8).reshape(2, 3)
    img = Image(axes=["y", "x"], shape=arr.shape, dtype=arr.dtype)
    img._data = arr
    col = Collection(items=[img], item_type=Image)

    out_path = tmp_path / "smoke.tif"
    SaveImage().save(col, BlockConfig(params={"path": str(out_path)}))
    loaded = LoadImage().load(BlockConfig(params={"path": str(out_path)}))
    assert isinstance(loaded, Collection)
    assert len(loaded) == 1
    assert loaded[0].axes == ["y", "x"]
    assert np.array_equal(loaded[0]._data, arr)


def test_imaging_preprocess_a_impl_smoke() -> None:
    """Smoke test that T-IMG-004..007 preprocess subset A bodies are concrete.

    Runs one minimal call per block to prove the skeleton
    ``NotImplementedError`` stubs have been replaced. Gated on
    ``skimage`` because the runtime denoise/background-subtract paths
    depend on it.
    """
    pytest.importorskip("skimage")
    import numpy as np
    from scieasy_blocks_imaging.preprocess.background_subtract import BackgroundSubtract
    from scieasy_blocks_imaging.preprocess.denoise import Denoise
    from scieasy_blocks_imaging.preprocess.flat_field_correct import FlatFieldCorrect
    from scieasy_blocks_imaging.preprocess.normalize import Normalize
    from scieasy_blocks_imaging.types import Image

    from scieasy.blocks.base.config import BlockConfig
    from scieasy.core.types.collection import Collection

    def _img(arr: np.ndarray) -> Image:
        out = Image(axes=["y", "x"], shape=arr.shape, dtype=arr.dtype)
        out._data = arr
        return out

    base = np.arange(16, dtype=np.float64).reshape(4, 4)

    # Denoise gaussian.
    d_out = Denoise().process_item(_img(base), BlockConfig(params={"method": "gaussian", "sigma": 0.5}))
    assert d_out.shape == (4, 4)

    # BackgroundSubtract constant.
    b_out = BackgroundSubtract().process_item(
        _img(base),
        BlockConfig(params={"method": "constant", "value": 1.0, "clip_to_zero": False}),
    )
    assert b_out.shape == (4, 4)

    # Normalize minmax.
    n_out = Normalize().process_item(_img(base), BlockConfig(params={"method": "minmax"}))
    n_arr = np.asarray(n_out._data)
    assert float(n_arr.min()) == 0.0
    assert float(n_arr.max()) == 1.0

    # FlatFieldCorrect basic.
    flat = _img(np.full((4, 4), 2.0, dtype=np.float64))
    ff_result = FlatFieldCorrect().run(
        {
            "image": Collection(items=[_img(np.full((4, 4), 10.0))], item_type=Image),
            "flat_field": Collection(items=[flat], item_type=Image),
        },
        BlockConfig(params={"method": "basic"}),
    )
    ff_out = ff_result["image"][0]
    assert np.allclose(np.asarray(ff_out._data), 10.0)


def test_imaging_preprocess_b_impl_smoke() -> None:
    """Smoke test that T-IMG-008..010 bodies are concrete."""
    import numpy as np
    from scieasy_blocks_imaging.preprocess.axis_ops import AxisMerge, AxisSplit
    from scieasy_blocks_imaging.preprocess.convert_dtype import ConvertDType
    from scieasy_blocks_imaging.preprocess.geometry import Rotate
    from scieasy_blocks_imaging.types import Image

    from scieasy.blocks.base.config import BlockConfig
    from scieasy.core.types.collection import Collection

    def _img(arr: np.ndarray, axes: list[str]) -> Image:
        out = Image(axes=axes, shape=arr.shape, dtype=arr.dtype)
        out._data = arr
        return out

    base = np.arange(12, dtype=np.uint8).reshape(3, 4)
    rotated = Rotate().process_item(_img(base, ["y", "x"]), BlockConfig(params={"angle": 90.0}))
    assert rotated.shape == (4, 3)

    converted = ConvertDType().process_item(
        _img(base, ["y", "x"]),
        BlockConfig(params={"target_dtype": "float32", "rescale": "linear"}),
    )
    assert converted.dtype == np.dtype(np.float32)

    stack = _img(np.arange(2 * 3 * 4, dtype=np.uint8).reshape(2, 3, 4), ["c", "y", "x"])
    split = AxisSplit().run({"image": Collection(items=[stack], item_type=Image)}, BlockConfig(params={"axis": "c"}))
    merged = AxisMerge().run({"images": split["images"]}, BlockConfig(params={"axis": "c"}))
    assert merged["image"][0].shape == (2, 3, 4)


def test_imaging_morphology_impl_smoke() -> None:
    """Smoke test that T-IMG-012..016 bodies are concrete."""
    pytest.importorskip("skimage")
    import numpy as np
    from scieasy_blocks_imaging.morphology.edge_detect import EdgeDetect
    from scieasy_blocks_imaging.morphology.fft_filter import FFTFilter
    from scieasy_blocks_imaging.morphology.morphology_op import MorphologyOp
    from scieasy_blocks_imaging.morphology.ridge_filter import RidgeFilter
    from scieasy_blocks_imaging.morphology.sharpen import Sharpen
    from scieasy_blocks_imaging.types import Image

    from scieasy.blocks.base.config import BlockConfig

    def _img(arr: np.ndarray) -> Image:
        out = Image(axes=["y", "x"], shape=arr.shape, dtype=arr.dtype)
        out._data = arr
        return out

    base = np.zeros((32, 32), dtype=np.float32)
    base[12:20, 15:17] = 1.0

    morph = MorphologyOp().process_item(
        _img(base),
        BlockConfig(params={"op": "dilate", "selem_shape": "disk", "selem_size": 1}),
    )
    assert morph.shape == (32, 32)

    edges = EdgeDetect().process_item(_img(base), BlockConfig(params={"method": "sobel"}))
    assert edges.shape == (32, 32)

    ridge = RidgeFilter().process_item(
        _img(base),
        BlockConfig(params={"method": "frangi", "sigma_min": 1.0, "sigma_max": 2.0, "num_sigma": 2}),
    )
    assert ridge.shape == (32, 32)

    sharp = Sharpen().process_item(_img(base), BlockConfig(params={"method": "unsharp", "amount": 1.0}))
    assert sharp.shape == (32, 32)

    fft = FFTFilter().process_item(_img(base), BlockConfig(params={"type": "lowpass", "cutoff_high": 0.2}))
    assert fft.shape == (32, 32)


def test_imaging_types_impl_smoke() -> None:
    """Smoke test that T-IMG-001 type classes are concrete."""
    import numpy as np
    from scieasy_blocks_imaging.types import Image, Label, Mask, Transform

    from scieasy.core.types.array import Array

    image = Image(axes=["y", "x"], shape=(4, 4), dtype=np.float32)
    mask = Mask(axes=["y", "x"], shape=(4, 4), dtype=bool)
    label = Label(slots={"raster": Array(axes=["y", "x"], shape=(4, 4), dtype=np.int32)})
    transform = Transform(
        axes=["row", "col"], shape=(2, 3), dtype=np.float32, meta=Transform.Meta(transform_type="affine")
    )

    assert image.shape == (4, 4)
    assert mask.dtype == bool
    assert "raster" in label.slots
    assert transform.shape == (2, 3)


def test_imaging_cellpose_impl_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke test that T-IMG-019 is wired into the imaging plugin surface."""
    from types import SimpleNamespace

    import numpy as np
    from scieasy_blocks_imaging import CellposeSegment, get_blocks
    from scieasy_blocks_imaging.types import Image, Label

    from scieasy.blocks.base.config import BlockConfig
    from scieasy.core.types.collection import Collection

    class _FakeModel:
        def __init__(self, *, gpu: bool = False) -> None:
            self.gpu = gpu

        def eval(self, data: np.ndarray, **kwargs: object) -> tuple[np.ndarray, None, None, None]:
            labels = np.zeros(np.asarray(data).shape, dtype=np.int32)
            labels[1:3, 1:3] = 1
            return labels, None, None, None

    monkeypatch.setattr(
        "scieasy_blocks_imaging.segmentation.cellpose_segment._import_cellpose_models",
        lambda: SimpleNamespace(
            Cellpose=lambda *, model_type, gpu: _FakeModel(gpu=gpu),
            CellposeModel=lambda *, pretrained_model, gpu: _FakeModel(gpu=gpu),
        ),
    )

    image = Image(axes=["y", "x"], shape=(4, 4), dtype=np.float32)
    image._data = np.ones((4, 4), dtype=np.float32)
    result = CellposeSegment().run({"images": Collection(items=[image], item_type=Image)}, BlockConfig(params={}))

    assert CellposeSegment in get_blocks()
    assert isinstance(result["labels"][0], Label)


def test_srs_types_impl_smoke() -> None:
    """Smoke test that T-SRS-001 SRSImage is concrete."""
    import numpy as np
    from scieasy_blocks_srs import SRSImage, get_types

    from scieasy.core.units import PhysicalQuantity

    img = SRSImage(
        axes=["lambda", "y", "x"],
        shape=(3, 4, 4),
        dtype=np.float32,
        meta=SRSImage.Meta(
            wavenumbers_cm1=[2850.0, 2880.0, 2930.0],
            integration_time=PhysicalQuantity(5.0, "ms"),
            laser_power=8.0,
        ),
    )

    assert img.meta is not None
    assert img.meta.wavenumbers_cm1 == [2850.0, 2880.0, 2930.0]
    assert get_types() == [SRSImage]


def test_imaging_segmentation_core_impl_smoke() -> None:
    """Smoke test that the segmentation core bundle is wired into the imaging plugin surface."""
    pytest.importorskip("skimage")
    pytest.importorskip("scipy")
    import numpy as np
    from scieasy_blocks_imaging import ConnectedComponents, RemoveSmallObjects, Threshold, Watershed, get_blocks
    from scieasy_blocks_imaging.types import Image, Label, Mask

    from scieasy.blocks.base.config import BlockConfig
    from scieasy.core.types.collection import Collection

    image = Image(axes=["y", "x"], shape=(16, 16), dtype=np.float32)
    arr = np.zeros((16, 16), dtype=np.float32)
    arr[4:8, 4:8] = 1.0
    arr[9:13, 9:13] = 1.0
    image._data = arr  # type: ignore[attr-defined]

    thresholded = Threshold().run(
        {"image": Collection(items=[image], item_type=Image)}, BlockConfig(params={"method": "otsu"})
    )
    mask = thresholded["mask"][0]
    labels = ConnectedComponents().run({"mask": thresholded["mask"]}, BlockConfig(params={"connectivity": 1}))
    cleaned = RemoveSmallObjects().process_item(labels["label"][0], BlockConfig(params={"min_size": 4}))
    watershed = Watershed().run(
        {"image": Collection(items=[image], item_type=Image), "mask": thresholded["mask"]},
        BlockConfig(params={"method": "distance", "min_distance": 2}),
    )

    assert Threshold in get_blocks()
    assert Watershed in get_blocks()
    assert isinstance(mask, Mask)
    assert isinstance(cleaned, Label)
    assert isinstance(watershed["label"][0], Label)


def test_imaging_measurement_impl_smoke() -> None:
    """Smoke test that the measurement bundle is wired into the imaging plugin surface."""
    pytest.importorskip("skimage")
    import numpy as np
    from scieasy_blocks_imaging import Colocalization, PairwiseDistance, RegionProps, get_blocks
    from scieasy_blocks_imaging.types import Image, Label

    from scieasy.blocks.base.config import BlockConfig
    from scieasy.core.types.array import Array

    label_arr = np.zeros((4, 4), dtype=np.int32)
    label_arr[1:3, 1:3] = 1
    raster = Array(axes=["y", "x"], shape=label_arr.shape, dtype=label_arr.dtype)
    raster._data = label_arr  # type: ignore[attr-defined]
    label = Label(slots={"raster": raster}, meta=Label.Meta(source_file="smoke.tif", n_objects=1))

    image_a = Image(axes=["y", "x"], shape=label_arr.shape, dtype=np.float32)
    image_a._data = label_arr.astype(np.float32)  # type: ignore[attr-defined]
    image_b = Image(axes=["y", "x"], shape=label_arr.shape, dtype=np.float32)
    image_b._data = label_arr.astype(np.float32) * 2.0  # type: ignore[attr-defined]

    props = RegionProps().run(
        {"label": label, "intensity_image": image_a},
        BlockConfig(params={"properties": ["area", "mean_intensity"]}),
    )["properties"]
    distances = PairwiseDistance().process_item(label, BlockConfig(params={"metric": "centroid"}))
    coloc = Colocalization().run(
        {"channel_a": image_a, "channel_b": image_b},
        BlockConfig(params={"metrics": ["pearson"]}),
    )["metrics"]

    assert RegionProps in get_blocks()
    assert PairwiseDistance in get_blocks()
    assert Colocalization in get_blocks()
    assert props.row_count == 1
    assert distances.row_count == 0
    assert coloc.row_count == 1


def test_imaging_finish_impl_smoke() -> None:
    """Smoke test the final Phase 11 imaging package surface."""
    pytest.importorskip("skimage")
    from scieasy_blocks_imaging import (
        AxisProjection,
        CellProfilerBlock,
        ComputeRegistration,
        ConvertDType,
        ImageCalculator,
        RenderPseudoColor,
        get_block_package,
        get_blocks,
        get_types,
    )
    from scieasy_blocks_imaging.types import Image, Label, Mask, Transform

    from scieasy.blocks.base.package_info import PackageInfo

    info, blocks = get_block_package()

    assert isinstance(info, PackageInfo)
    assert info.name == "scieasy-blocks-imaging"
    assert get_types() == [Image, Mask, Label, Transform]
    assert ConvertDType in get_blocks()
    assert ComputeRegistration in blocks
    assert AxisProjection in blocks
    assert ImageCalculator in blocks
    assert RenderPseudoColor in blocks
    assert CellProfilerBlock in blocks
    assert len(blocks) == 51

    for block_cls in (
        ConvertDType,
        ComputeRegistration,
        AxisProjection,
        ImageCalculator,
        RenderPseudoColor,
        CellProfilerBlock,
    ):
        block = block_cls()
        assert block.type_name
