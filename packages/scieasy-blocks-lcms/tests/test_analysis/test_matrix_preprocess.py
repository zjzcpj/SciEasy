from __future__ import annotations

import numpy as np
import pytest
from scieasy_blocks_lcms.analysis.matrix_preprocess import MatrixPreprocess

from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.dataframe import DataFrame

pd = pytest.importorskip("pandas")


def _matrix(frame: pd.DataFrame) -> DataFrame:
    table = DataFrame(columns=list(frame.columns), row_count=len(frame))
    table._data = frame.copy()
    return table


def test_log_transform_default_true() -> None:
    frame = pd.DataFrame({"S1": [2.0, 4.0], "S2": [6.0, 8.0]}, index=["c1", "c2"])
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "none", "scale": "none"})
    )
    out = result._data
    expected = np.log2(frame + 1.0)
    assert np.allclose(out.to_numpy(), expected.to_numpy())


def test_log_transform_handles_zeros_via_pseudocount() -> None:
    frame = pd.DataFrame({"S1": [0.0, 2.0], "S2": [4.0, 8.0]}, index=["c1", "c2"])
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "none", "scale": "none"})
    )
    out = result._data
    assert out.loc["c1", "S1"] == pytest.approx(0.0)


def test_impute_knn() -> None:
    pytest.importorskip("sklearn")
    frame = pd.DataFrame(
        {"S1": [1.0, 5.0, 9.0], "S2": [2.0, np.nan, 10.0], "S3": [3.0, 7.0, 11.0]},
        index=["c1", "c2", "c3"],
    )
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "knn", "log_transform": False, "scale": "none"})
    )
    out = result._data
    assert out.shape == frame.shape
    assert not out.isna().any().any()


def test_impute_mean() -> None:
    frame = pd.DataFrame({"S1": [1.0, 4.0], "S2": [np.nan, 6.0], "S3": [3.0, np.nan]}, index=["c1", "c2"])
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "mean", "log_transform": False, "scale": "none"})
    )
    out = result._data
    assert out.loc["c1", "S2"] == pytest.approx(2.0)
    assert out.loc["c2", "S3"] == pytest.approx(5.0)


def test_impute_zero() -> None:
    frame = pd.DataFrame({"S1": [1.0, 4.0], "S2": [np.nan, 6.0]}, index=["c1", "c2"])
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "zero", "log_transform": False, "scale": "none"})
    )
    out = result._data
    assert out.loc["c1", "S2"] == pytest.approx(0.0)


def test_impute_none() -> None:
    frame = pd.DataFrame({"S1": [1.0, 4.0], "S2": [np.nan, 6.0]}, index=["c1", "c2"])
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "none", "log_transform": False, "scale": "none"})
    )
    out = result._data
    assert np.isnan(out.loc["c1", "S2"])


def test_scale_auto_is_zscore() -> None:
    frame = pd.DataFrame({"S1": [1.0, 2.0], "S2": [3.0, 4.0], "S3": [5.0, 6.0]}, index=["c1", "c2"])
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "none", "log_transform": False, "scale": "auto"})
    )
    out = result._data
    assert np.allclose(out.mean(axis=1).to_numpy(), 0.0)
    assert np.allclose(out.std(axis=1, ddof=0).to_numpy(), 1.0)


def test_scale_pareto() -> None:
    frame = pd.DataFrame({"S1": [1.0, 2.0], "S2": [3.0, 6.0], "S3": [5.0, 10.0]}, index=["c1", "c2"])
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "none", "log_transform": False, "scale": "pareto"})
    )
    out = result._data
    centred = frame.sub(frame.mean(axis=1), axis=0)
    expected = centred.div(frame.std(axis=1, ddof=0).pow(0.5), axis=0)
    assert np.allclose(out.to_numpy(), expected.to_numpy())


def test_scale_none() -> None:
    frame = pd.DataFrame({"S1": [1.0, 2.0], "S2": [3.0, 4.0]}, index=["c1", "c2"])
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "none", "log_transform": False, "scale": "none"})
    )
    out = result._data
    assert out.equals(frame)


def test_pipeline_order_impute_log_scale() -> None:
    frame = pd.DataFrame({"S1": [1.0], "S2": [np.nan], "S3": [3.0]}, index=["c1"])
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "mean", "scale": "none"})
    )
    out = result._data
    expected = pd.DataFrame({"S1": [np.log2(1.5)], "S2": [np.log2(2.5)], "S3": [np.log2(3.5)]}, index=["c1"])
    assert np.allclose(out.to_numpy(), expected.to_numpy())


def test_preserves_dataframe_shape() -> None:
    frame = pd.DataFrame({"S1": [1.0, 2.0, 3.0], "S2": [4.0, 5.0, 6.0]}, index=["c1", "c2", "c3"])
    result = MatrixPreprocess().process_item(
        _matrix(frame), BlockConfig(params={"impute_method": "none", "log_transform": False, "scale": "none"})
    )
    assert result._data.shape == frame.shape


def test_raises_on_unknown_impute_method() -> None:
    frame = pd.DataFrame({"S1": [1.0], "S2": [2.0]}, index=["c1"])
    with pytest.raises(ValueError, match="impute_method"):
        MatrixPreprocess().process_item(_matrix(frame), BlockConfig(params={"impute_method": "unknown"}))


def test_raises_on_unknown_scale_method() -> None:
    frame = pd.DataFrame({"S1": [1.0], "S2": [2.0]}, index=["c1"])
    with pytest.raises(ValueError, match="scale"):
        MatrixPreprocess().process_item(
            _matrix(frame), BlockConfig(params={"impute_method": "none", "scale": "bogus", "log_transform": False})
        )
