from __future__ import annotations

import numpy as np
import pytest
from scieasy_blocks_lcms.analysis.univariate_stats import UnivariateStats
from scieasy_blocks_lcms.types import SampleMetadata

from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

pd = pytest.importorskip("pandas")
pytest.importorskip("scipy")
pytest.importorskip("statsmodels")


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


def _run(matrix: pd.DataFrame, metadata: pd.DataFrame, config: dict[str, object]) -> pd.DataFrame:
    result = UnivariateStats().run(
        {
            "matrix": Collection(items=[_matrix(matrix)], item_type=DataFrame),
            "sample_metadata": Collection(
                items=[_metadata(metadata["sample_id"].tolist(), metadata["group"].tolist())], item_type=SampleMetadata
            ),
        },
        BlockConfig(params=config),
    )
    return result["stats"][0]._data


def test_ttest_two_groups() -> None:
    matrix = pd.DataFrame({"A1": [2.0, 3.0], "A2": [2.0, 3.0], "B1": [1.0, 1.0], "B2": [1.0, 1.0]}, index=["c1", "c2"])
    metadata = pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]})
    out = _run(matrix, metadata, {"group_column": "group", "test": "t-test", "correction": "none"})
    assert list(out.columns) == ["compound", "fold_change", "pvalue", "pvalue_adj", "significant"]
    assert out["pvalue"].between(0.0, 1.0).all()


def test_anova_three_groups() -> None:
    matrix = pd.DataFrame(
        {"A1": [2.0], "B1": [1.0], "C1": [3.0]},
        index=["c1"],
    )
    metadata = pd.DataFrame({"sample_id": ["A1", "B1", "C1"], "group": ["A", "B", "C"]})
    out = _run(matrix, metadata, {"group_column": "group", "test": "anova", "correction": "none"})
    assert np.isnan(out.loc[0, "fold_change"])
    assert out.loc[0, "pvalue_adj"] == pytest.approx(out.loc[0, "pvalue"])


def test_wilcoxon_two_groups() -> None:
    matrix = pd.DataFrame({"A1": [2.0], "A2": [2.0], "B1": [1.0], "B2": [1.0]}, index=["c1"])
    metadata = pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]})
    out = _run(matrix, metadata, {"group_column": "group", "test": "wilcoxon", "correction": "none"})
    assert out.loc[0, "pvalue"] <= 1.0


def test_fold_change_computed() -> None:
    matrix = pd.DataFrame({"A1": [4.0], "A2": [4.0], "B1": [1.0], "B2": [1.0]}, index=["c1"])
    metadata = pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]})
    out = _run(matrix, metadata, {"group_column": "group", "test": "t-test", "correction": "none"})
    assert out.loc[0, "fold_change"] == pytest.approx(2.0)


def test_bonferroni_correction() -> None:
    matrix = pd.DataFrame({"A1": [4.0, 8.0], "A2": [4.0, 8.0], "B1": [1.0, 2.0], "B2": [1.0, 2.0]}, index=["c1", "c2"])
    metadata = pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]})
    out = _run(matrix, metadata, {"group_column": "group", "test": "t-test", "correction": "bonferroni"})
    assert np.allclose(out["pvalue_adj"].to_numpy(), np.minimum(1.0, out["pvalue"].to_numpy() * len(out)))


def test_fdr_correction() -> None:
    matrix = pd.DataFrame({"A1": [4.0, 8.0], "A2": [4.0, 8.0], "B1": [1.0, 2.0], "B2": [1.0, 2.0]}, index=["c1", "c2"])
    metadata = pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]})
    out = _run(matrix, metadata, {"group_column": "group", "test": "t-test", "correction": "fdr"})
    assert out["pvalue_adj"].between(0.0, 1.0).all()


def test_significance_flag() -> None:
    matrix = pd.DataFrame({"A1": [5.0], "A2": [5.0], "B1": [1.0], "B2": [1.0]}, index=["c1"])
    metadata = pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]})
    out = _run(matrix, metadata, {"group_column": "group", "test": "t-test", "correction": "none", "alpha": 0.05})
    assert bool(out.loc[0, "significant"]) is True


def test_raises_on_single_group() -> None:
    matrix = pd.DataFrame({"A1": [2.0], "A2": [3.0]}, index=["c1"])
    metadata = pd.DataFrame({"sample_id": ["A1", "A2"], "group": ["A", "A"]})
    with pytest.raises(ValueError, match="exactly two groups"):
        _run(matrix, metadata, {"group_column": "group", "test": "t-test"})


def test_raises_on_anova_with_two_groups() -> None:
    matrix = pd.DataFrame({"A1": [2.0], "B1": [3.0]}, index=["c1"])
    metadata = pd.DataFrame({"sample_id": ["A1", "B1"], "group": ["A", "B"]})
    with pytest.raises(ValueError, match="anova"):
        _run(matrix, metadata, {"group_column": "group", "test": "anova"})


def test_raises_on_ttest_with_three_groups() -> None:
    matrix = pd.DataFrame({"A1": [2.0], "B1": [3.0], "C1": [4.0]}, index=["c1"])
    metadata = pd.DataFrame({"sample_id": ["A1", "B1", "C1"], "group": ["A", "B", "C"]})
    with pytest.raises(ValueError, match="exactly two groups"):
        _run(matrix, metadata, {"group_column": "group", "test": "t-test"})


def test_output_columns_match_spec() -> None:
    matrix = pd.DataFrame({"A1": [4.0], "A2": [4.0], "B1": [1.0], "B2": [1.0]}, index=["c1"])
    metadata = pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]})
    out = _run(matrix, metadata, {"group_column": "group", "test": "t-test", "correction": "none"})
    assert list(out.columns) == ["compound", "fold_change", "pvalue", "pvalue_adj", "significant"]


def test_empty_matrix_returns_empty_dataframe() -> None:
    matrix = pd.DataFrame(columns=["A1", "A2", "B1", "B2"])
    metadata = pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]})
    out = _run(matrix, metadata, {"group_column": "group", "test": "t-test", "correction": "none"})
    assert out.empty
