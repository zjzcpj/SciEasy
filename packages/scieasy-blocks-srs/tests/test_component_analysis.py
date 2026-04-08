"""Test stubs for SRS component-analysis blocks (T-SRS-006 ... T-SRS-010).

All tests skipped pending implementation.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="SRS component_analysis impl pending — skeleton stub")


# ---------------------------------------------------------------------------
# T-SRS-006 — SRSVCA
# ---------------------------------------------------------------------------


def test_vca_smoke_3components() -> None:
    """VCA returns 3 endmembers on a synthetic 3-endmember mixture."""


def test_vca_n_components_param() -> None:
    """n_components config controls the row count."""


def test_vca_columns_match_wavenumbers() -> None:
    """Columns are item.meta.wavenumbers_cm1 when set."""


def test_vca_columns_default_to_index_when_no_wavenumbers() -> None:
    """Columns fall back to range(n_w) when meta lacks wavenumbers."""


def test_vca_lambda_axis_required() -> None:
    """Inputs without a lambda axis are rejected."""


def test_vca_index_named_endmember_id() -> None:
    """DataFrame index is named 'endmember_id'."""


def test_vca_internal_helper_callable_from_unmix() -> None:
    """_extract_endmembers is module-level so SRSUnmix can import it."""


# ---------------------------------------------------------------------------
# T-SRS-007 — SRSUnmix
# ---------------------------------------------------------------------------


def test_unmix_with_explicit_references() -> None:
    """NNLS recovers planted abundances on a synthetic 3-endmember mixture."""


def test_unmix_no_references_falls_through_to_vca() -> None:
    """Without references, defaults to auto_vca_n_components=4."""


def test_unmix_auto_vca_n_components_param() -> None:
    """auto_vca_n_components config is honoured."""


def test_unmix_returns_endmember_dataframe_too() -> None:
    """endmembers output port carries the reference DataFrame (passthrough or VCA)."""


def test_unmix_collection_item_type_is_image() -> None:
    """abundance_maps is Collection[Image]."""


def test_unmix_abundance_axes_are_yx() -> None:
    """Each abundance map is a 2D Image with axes ['y','x']."""


def test_unmix_5d_input_with_c() -> None:
    """5D input with extra c axis succeeds."""


def test_unmix_lambda_axis_required() -> None:
    """Inputs without a lambda axis are rejected."""


def test_unmix_logs_when_falling_through_to_vca() -> None:
    """Auto-VCA fallback emits an INFO log message naming the component count."""


# ---------------------------------------------------------------------------
# T-SRS-008 — SRSPCA
# ---------------------------------------------------------------------------


def test_pca_smoke_3components() -> None:
    """PCA runs and returns 3 score maps + a 3-row loadings DataFrame."""


def test_pca_n_components_param() -> None:
    """n_components config is honoured."""


def test_pca_score_maps_axes() -> None:
    """Each score map has axes ['y','x']."""


def test_pca_loadings_columns_are_wavenumbers() -> None:
    """Loadings DataFrame columns equal meta.wavenumbers_cm1."""


def test_pca_loadings_index_is_pc_id() -> None:
    """Loadings DataFrame index is named 'pc_id'."""


def test_pca_scale_param() -> None:
    """scale=True applies StandardScaler before PCA."""


def test_pca_n_components_too_large_raises() -> None:
    """n_components > n_wavenumbers raises ValueError."""


def test_pca_lambda_axis_required() -> None:
    """Inputs without a lambda axis are rejected."""


# ---------------------------------------------------------------------------
# T-SRS-009 — SRSICA
# ---------------------------------------------------------------------------


def test_ica_smoke_3components() -> None:
    """FastICA runs and returns 3 score maps + a 3-row components DataFrame."""


def test_ica_n_components_param() -> None:
    """n_components config is honoured."""


def test_ica_method_param() -> None:
    """Only method='fastica' is accepted; other strings raise."""


def test_ica_lambda_axis_required() -> None:
    """Inputs without a lambda axis are rejected."""


def test_ica_components_index_is_ic_id() -> None:
    """Components DataFrame index is named 'ic_id'."""


def test_ica_components_columns_are_wavenumbers() -> None:
    """Columns equal meta.wavenumbers_cm1."""


def test_ica_score_maps_are_2d_images() -> None:
    """Each IC map is a 2D Image with axes ['y','x']."""


# ---------------------------------------------------------------------------
# T-SRS-010 — SRSKMeansCluster
# ---------------------------------------------------------------------------


def test_kmeans_smoke_3clusters() -> None:
    """K-means with n_clusters=3 produces a Label with values in {0,1,2}."""


def test_kmeans_n_clusters_param() -> None:
    """n_clusters config is honoured."""


def test_kmeans_init_random() -> None:
    """init='random' is accepted."""


def test_kmeans_init_kmeanspp() -> None:
    """Default init is 'k-means++'."""


def test_kmeans_n_init_param() -> None:
    """n_init config is honoured."""


def test_kmeans_label_raster_dtype_int32() -> None:
    """Label raster dtype is int32."""


def test_kmeans_centroids_shape() -> None:
    """Centroid DataFrame is (n_clusters, n_wavenumbers) with 'cluster_id' index."""


def test_kmeans_lambda_axis_required() -> None:
    """Inputs without a lambda axis are rejected."""
