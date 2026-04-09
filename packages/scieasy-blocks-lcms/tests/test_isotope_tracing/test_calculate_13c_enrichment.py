"""Tests for T-LCMS-008 Calculate13CEnrichment."""

from __future__ import annotations

import pytest
from scieasy_blocks_lcms.isotope_tracing.calculate_13c_enrichment import Calculate13CEnrichment
from scieasy_blocks_lcms.types import MIDTable

from scieasy.blocks.base.config import BlockConfig


def _pd():
    return pytest.importorskip("pandas")


def _make_mid_table(frame, *, tracer_atoms: list[str], sample_columns: list[str]) -> MIDTable:
    table = MIDTable(
        columns=list(frame.columns),
        row_count=len(frame),
        meta=MIDTable.Meta(tracer_atoms=tracer_atoms, sample_columns=sample_columns),
    )
    table._data = frame
    return table


def test_single_tracer_half_labeling() -> None:
    pd = _pd()
    frame = pd.DataFrame({"Compound": ["glucose", "glucose"], "C13": [0, 6], "S1": [0.5, 0.5]})
    result = Calculate13CEnrichment().process_item(
        _make_mid_table(frame, tracer_atoms=["C13"], sample_columns=["S1"]),
        BlockConfig(params={}),
    )
    out = result._data
    assert list(out.columns) == ["compound", "sample", "enrichment"]
    assert out.loc[0, "compound"] == "glucose"
    assert out.loc[0, "sample"] == "S1"
    assert out.loc[0, "enrichment"] == pytest.approx(0.5)


def test_multi_tracer_produces_one_column_per_tracer() -> None:
    pd = _pd()
    frame = pd.DataFrame(
        {
            "Compound": ["cytosine", "cytosine", "cytosine"],
            "C13": [0, 1, 2],
            "H2": [0, 1, 0],
            "S1": [0.25, 0.25, 0.5],
        }
    )
    result = Calculate13CEnrichment().process_item(
        _make_mid_table(frame, tracer_atoms=["C13", "H2"], sample_columns=["S1"]),
        BlockConfig(params={}),
    )
    out = result._data
    assert list(out.columns) == ["compound", "sample", "enrichment_C13", "enrichment_H2"]
    assert out.loc[0, "enrichment_C13"] == pytest.approx((0.0 * 0.25 + 1.0 * 0.25 + 2.0 * 0.5) / 2.0)
    assert out.loc[0, "enrichment_H2"] == pytest.approx((0.0 * 0.25 + 1.0 * 0.25 + 0.0 * 0.5) / 1.0)


def test_empty_mid_table_returns_empty_dataframe() -> None:
    pd = _pd()
    frame = pd.DataFrame(columns=["Compound", "C13", "S1"])
    result = Calculate13CEnrichment().process_item(
        _make_mid_table(frame, tracer_atoms=["C13"], sample_columns=["S1"]),
        BlockConfig(params={}),
    )
    out = result._data
    assert out.empty
    assert list(out.columns) == ["compound", "sample", "enrichment"]


def test_missing_tracer_atom_column_raises() -> None:
    pd = _pd()
    frame = pd.DataFrame({"Compound": ["glucose"], "S1": [1.0]})
    with pytest.raises(ValueError, match="tracer atom column"):
        Calculate13CEnrichment().process_item(
            _make_mid_table(frame, tracer_atoms=["C13"], sample_columns=["S1"]),
            BlockConfig(params={}),
        )
