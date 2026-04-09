"""Tests for T-LCMS-010 CompareGroupMID."""

from __future__ import annotations

import pytest
from scieasy_blocks_lcms.isotope_tracing.compare_group_mid import CompareGroupMID
from scieasy_blocks_lcms.types import MIDTable, SampleMetadata

from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.collection import Collection


def _pd():
    return pytest.importorskip("pandas")


def _make_mid_table(frame) -> MIDTable:
    table = MIDTable(
        columns=list(frame.columns),
        row_count=len(frame),
        meta=MIDTable.Meta(tracer_atoms=["C13"], sample_columns=["A1", "A2", "B1", "B2"]),
    )
    table._data = frame
    return table


def _make_sample_metadata(frame) -> SampleMetadata:
    table = SampleMetadata(
        columns=list(frame.columns),
        row_count=len(frame),
        meta=SampleMetadata.Meta(sample_id_column="sample_id"),
    )
    table._data = frame
    return table


def test_ttest_and_fdr_correction() -> None:
    pd = _pd()
    mid = _make_mid_table(
        pd.DataFrame(
            {
                "Compound": ["glucose", "glucose"],
                "C13": [0, 1],
                "A1": [1.0, 0.0],
                "A2": [1.0, 0.0],
                "B1": [0.0, 1.0],
                "B2": [0.0, 1.0],
            }
        )
    )
    meta = _make_sample_metadata(pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]}))
    result = CompareGroupMID().run(
        {
            "mid_table": Collection(items=[mid], item_type=MIDTable),
            "sample_metadata": Collection(items=[meta], item_type=SampleMetadata),
        },
        BlockConfig(params={"group_column": "group", "test": "t-test", "correction": "fdr"}),
    )
    out = result["comparison"][0]._data
    assert set(out.columns) == {
        "compound",
        "isotopologue",
        "group1",
        "group2",
        "group1_mean",
        "group2_mean",
        "pvalue",
        "pvalue_adj",
        "significant",
    }
    assert set(out["isotopologue"]) == {"M+0", "M+1"}
    assert out["pvalue_adj"].between(0.0, 1.0).all()


def test_summed_labeled_mode_omits_isotopologue_column() -> None:
    pd = _pd()
    mid = _make_mid_table(
        pd.DataFrame(
            {
                "Compound": ["glucose", "glucose"],
                "C13": [0, 1],
                "A1": [0.9, 0.1],
                "A2": [0.8, 0.2],
                "B1": [0.3, 0.7],
                "B2": [0.2, 0.8],
            }
        )
    )
    meta = _make_sample_metadata(pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]}))
    result = CompareGroupMID().run(
        {
            "mid_table": Collection(items=[mid], item_type=MIDTable),
            "sample_metadata": Collection(items=[meta], item_type=SampleMetadata),
        },
        BlockConfig(params={"group_column": "group", "per_isotopologue": False, "correction": "none"}),
    )
    out = result["comparison"][0]._data
    assert "isotopologue" not in out.columns
    assert len(out) == 1


def test_missing_group_column_raises() -> None:
    pd = _pd()
    mid = _make_mid_table(
        pd.DataFrame({"Compound": ["g"], "C13": [0], "A1": [1.0], "A2": [1.0], "B1": [1.0], "B2": [1.0]})
    )
    meta = _make_sample_metadata(pd.DataFrame({"sample_id": ["A1", "A2", "B1", "B2"], "group": ["A", "A", "B", "B"]}))
    with pytest.raises(ValueError, match="group column"):
        CompareGroupMID().run(
            {
                "mid_table": Collection(items=[mid], item_type=MIDTable),
                "sample_metadata": Collection(items=[meta], item_type=SampleMetadata),
            },
            BlockConfig(params={"group_column": "condition"}),
        )


def test_more_than_two_groups_not_supported() -> None:
    pd = _pd()
    mid = MIDTable(
        columns=["Compound", "C13", "A1", "B1", "C1"],
        row_count=1,
        meta=MIDTable.Meta(tracer_atoms=["C13"], sample_columns=["A1", "B1", "C1"]),
    )
    mid._data = pd.DataFrame({"Compound": ["g"], "C13": [0], "A1": [1.0], "B1": [1.0], "C1": [1.0]})
    meta = _make_sample_metadata(pd.DataFrame({"sample_id": ["A1", "B1", "C1"], "group": ["A", "B", "C"]}))
    with pytest.raises(NotImplementedError, match="UnivariateStats"):
        CompareGroupMID().run(
            {
                "mid_table": Collection(items=[mid], item_type=MIDTable),
                "sample_metadata": Collection(items=[meta], item_type=SampleMetadata),
            },
            BlockConfig(params={"group_column": "group"}),
        )
