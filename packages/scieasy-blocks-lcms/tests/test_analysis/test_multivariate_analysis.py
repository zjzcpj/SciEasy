from __future__ import annotations

import pytest
from scieasy_blocks_lcms.analysis.multivariate_analysis import MultivariateAnalysis
from scieasy_blocks_lcms.types import SampleMetadata

from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

pd = pytest.importorskip("pandas")
pytest.importorskip("sklearn")
pytest.importorskip("matplotlib")


def _matrix(frame: pd.DataFrame) -> DataFrame:
    table = DataFrame(columns=list(frame.columns), row_count=len(frame))
    table._data = frame.copy()
    return table


def _metadata(sample_ids: list[str], groups: list[str]) -> SampleMetadata:
    frame = pd.DataFrame({"sample_id": sample_ids, "group": groups})
    table = SampleMetadata(
        columns=list(frame.columns),
        row_count=len(frame),
        meta=SampleMetadata.Meta(sample_id_column="sample_id"),
    )
    table._data = frame
    return table


def _run(matrix: pd.DataFrame, config: dict[str, object], metadata: pd.DataFrame | None = None) -> dict[str, object]:
    inputs = {"matrix": Collection(items=[_matrix(matrix)], item_type=DataFrame)}
    if metadata is not None:
        inputs["sample_metadata"] = Collection(
            items=[_metadata(metadata["sample_id"].tolist(), metadata["group"].tolist())],
            item_type=SampleMetadata,
        )
    return MultivariateAnalysis().run(inputs, BlockConfig(params=config))


def _base_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "S1": [1.0, 5.0, 9.0, 13.0],
            "S2": [2.0, 6.0, 10.0, 14.0],
            "S3": [3.0, 7.0, 11.0, 15.0],
            "S4": [4.0, 8.0, 12.0, 16.0],
        },
        index=["c1", "c2", "c3", "c4"],
    )


def test_pca_default_two_components() -> None:
    out = _run(_base_matrix(), {"method": "PCA"})
    scores = out["scores"][0]
    loadings = out["loadings"][0]
    plot = out["plot"][0]
    assert scores._data.shape[0] == 4
    assert loadings._data.shape[0] == 4
    assert plot.mime_type == "image/png"
    assert plot.file_path is not None and plot.file_path.exists()


def test_pca_scores_shape_matches_samples() -> None:
    matrix = _base_matrix().iloc[:, :3]
    out = _run(matrix, {"method": "PCA", "n_components": 2})
    assert out["scores"][0]._data.shape[0] == 3


def test_pca_loadings_shape_matches_features() -> None:
    out = _run(_base_matrix(), {"method": "PCA", "n_components": 2})
    assert out["loadings"][0]._data.shape[0] == 4


def test_plsda_requires_metadata() -> None:
    with pytest.raises(ValueError, match="sample_metadata"):
        _run(_base_matrix(), {"method": "PLSDA", "group_column": "group"})


def test_plsda_binary_classification() -> None:
    matrix = _base_matrix()
    metadata = pd.DataFrame({"sample_id": ["S1", "S2", "S3", "S4"], "group": ["A", "A", "B", "B"]})
    out = _run(matrix, {"method": "PLSDA", "group_column": "group"}, metadata)
    scores = out["scores"][0]._data
    loadings = out["loadings"][0]._data
    assert list(scores["sample_id"]) == ["S1", "S2", "S3", "S4"]
    assert scores.shape[0] == 4
    assert loadings.shape[0] == 4


def test_oplsda_requires_metadata() -> None:
    with pytest.raises(ValueError, match="sample_metadata"):
        _run(_base_matrix(), {"method": "OPLSDA", "group_column": "group"})


def test_n_components_config() -> None:
    metadata = pd.DataFrame({"sample_id": ["S1", "S2", "S3", "S4"], "group": ["A", "A", "B", "B"]})
    out = _run(_base_matrix(), {"method": "PCA", "n_components": 1}, metadata)
    scores = out["scores"][0]._data
    assert list(scores.columns) == ["sample_id", "component_1"]


def test_scale_true_by_default() -> None:
    metadata = pd.DataFrame({"sample_id": ["S1", "S2", "S3", "S4"], "group": ["A", "A", "B", "B"]})
    scaled = _run(_base_matrix(), {"method": "PCA"}, metadata)["scores"][0]._data
    unscaled = _run(_base_matrix(), {"method": "PCA", "scale": False}, metadata)["scores"][0]._data
    assert not scaled.equals(unscaled)


def test_output_scores_dataframe() -> None:
    out = _run(_base_matrix(), {"method": "PCA"})
    assert isinstance(out["scores"][0], DataFrame)


def test_output_loadings_dataframe() -> None:
    out = _run(_base_matrix(), {"method": "PCA"})
    assert isinstance(out["loadings"][0], DataFrame)


def test_output_plot_artifact_png() -> None:
    out = _run(_base_matrix(), {"method": "PCA"})
    plot = out["plot"][0]
    assert plot.mime_type == "image/png"
    assert plot.file_path is not None and plot.file_path.exists()


def test_raises_on_unknown_method() -> None:
    with pytest.raises(ValueError, match="unsupported method"):
        _run(_base_matrix(), {"method": "bogus"})
