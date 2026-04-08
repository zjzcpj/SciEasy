from __future__ import annotations

import pytest
from scieasy_blocks_lcms.analysis.metabolite_matrix import MetaboliteMatrix
from scieasy_blocks_lcms.types import PeakTable, SampleMetadata

from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

pd = pytest.importorskip("pandas")


def _peak_table(frame: pd.DataFrame) -> PeakTable:
    table = PeakTable(
        columns=list(frame.columns),
        row_count=len(frame),
        meta=PeakTable.Meta(source="ElMAVEN"),
    )
    table._data = frame.copy()
    return table


def _sample_metadata(sample_ids: list[str]) -> SampleMetadata:
    frame = pd.DataFrame({"sample_id": sample_ids, "group": ["A"] * len(sample_ids)})
    table = SampleMetadata(
        columns=list(frame.columns),
        row_count=len(frame),
        meta=SampleMetadata.Meta(sample_id_column="sample_id"),
    )
    table._data = frame
    return table


def test_pivot_long_to_wide() -> None:
    frame = pd.DataFrame(
        {
            "compound": ["glucose", "glucose", "lactate", "lactate"],
            "sample_id": ["S1", "S2", "S1", "S2"],
            "intensity": [10.0, 20.0, 30.0, 40.0],
        }
    )
    result = MetaboliteMatrix().run(
        {
            "peak_table": Collection(items=[_peak_table(frame)], item_type=PeakTable),
            "sample_metadata": Collection(items=[_sample_metadata(["S1", "S2"])], item_type=SampleMetadata),
        },
        BlockConfig(params={}),
    )
    out = result["matrix"][0]
    assert type(out) is DataFrame
    assert list(out.columns) == ["S1", "S2"]
    assert out._data.loc["glucose", "S1"] == 10.0
    assert out._data.loc["lactate", "S2"] == 40.0


def test_default_value_column_intensity() -> None:
    frame = pd.DataFrame(
        {
            "compound": ["glucose", "glucose"],
            "sample_id": ["S1", "S2"],
            "intensity": [12.0, 24.0],
            "area": [1.0, 2.0],
        }
    )
    result = MetaboliteMatrix().run(
        {"peak_table": Collection(items=[_peak_table(frame)], item_type=PeakTable)},
        BlockConfig(params={}),
    )
    assert result["matrix"][0]._data.loc["glucose", "S1"] == 12.0


def test_custom_value_column() -> None:
    frame = pd.DataFrame(
        {
            "compound": ["glucose", "glucose"],
            "sample_id": ["S1", "S2"],
            "intensity": [12.0, 24.0],
            "area": [1.5, 2.5],
        }
    )
    result = MetaboliteMatrix().run(
        {"peak_table": Collection(items=[_peak_table(frame)], item_type=PeakTable)},
        BlockConfig(params={"value_column": "area"}),
    )
    assert result["matrix"][0]._data.loc["glucose", "S2"] == 2.5


def test_default_compound_column() -> None:
    frame = pd.DataFrame(
        {
            "compound": ["glucose", "lactate"],
            "sample_id": ["S1", "S1"],
            "intensity": [12.0, 24.0],
        }
    )
    result = MetaboliteMatrix().run(
        {"peak_table": Collection(items=[_peak_table(frame)], item_type=PeakTable)},
        BlockConfig(params={}),
    )
    assert list(result["matrix"][0]._data.index) == ["glucose", "lactate"]


def test_custom_compound_column() -> None:
    frame = pd.DataFrame(
        {
            "metabolite": ["glucose", "lactate"],
            "sample_id": ["S1", "S1"],
            "intensity": [12.0, 24.0],
        }
    )
    result = MetaboliteMatrix().run(
        {"peak_table": Collection(items=[_peak_table(frame)], item_type=PeakTable)},
        BlockConfig(params={"compound_column": "metabolite"}),
    )
    assert list(result["matrix"][0]._data.index) == ["glucose", "lactate"]


def test_missing_combinations_become_nan() -> None:
    frame = pd.DataFrame(
        {
            "compound": ["glucose", "lactate"],
            "sample_id": ["S1", "S1"],
            "intensity": [10.0, 30.0],
        }
    )
    result = MetaboliteMatrix().run(
        {
            "peak_table": Collection(items=[_peak_table(frame)], item_type=PeakTable),
            "sample_metadata": Collection(items=[_sample_metadata(["S1", "S2"])], item_type=SampleMetadata),
        },
        BlockConfig(params={}),
    )
    assert pd.isna(result["matrix"][0]._data.loc["glucose", "S2"])


def test_output_is_generic_dataframe() -> None:
    frame = pd.DataFrame(
        {
            "compound": ["glucose"],
            "sample_id": ["S1"],
            "intensity": [10.0],
        }
    )
    out = MetaboliteMatrix().run(
        {"peak_table": Collection(items=[_peak_table(frame)], item_type=PeakTable)},
        BlockConfig(params={}),
    )["matrix"][0]
    assert isinstance(out, DataFrame)
    assert not isinstance(out, PeakTable)


def test_preserves_sample_order_from_metadata() -> None:
    frame = pd.DataFrame(
        {
            "compound": ["glucose", "glucose"],
            "sample_id": ["S1", "S2"],
            "intensity": [10.0, 20.0],
        }
    )
    result = MetaboliteMatrix().run(
        {
            "peak_table": Collection(items=[_peak_table(frame)], item_type=PeakTable),
            "sample_metadata": Collection(items=[_sample_metadata(["S2", "S1"])], item_type=SampleMetadata),
        },
        BlockConfig(params={}),
    )
    assert list(result["matrix"][0].columns) == ["S2", "S1"]


def test_missing_required_column_raises() -> None:
    frame = pd.DataFrame({"sample_id": ["S1"], "intensity": [10.0]})
    with pytest.raises(ValueError, match="compound"):
        MetaboliteMatrix().run(
            {"peak_table": Collection(items=[_peak_table(frame)], item_type=PeakTable)},
            BlockConfig(params={}),
        )
