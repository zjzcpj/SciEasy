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
    from scieasy_blocks_srs.types import SRSImage

    with pytest.raises(NotImplementedError, match="T-SRS-001"):
        SRSImage()


def test_lcms_types_placeholder_raises() -> None:
    """Representative: instantiating T-LCMS-002 MSRawFile raises NotImplementedError."""
    from scieasy_blocks_lcms.types import MSRawFile

    with pytest.raises(NotImplementedError, match="T-LCMS-002"):
        MSRawFile()
