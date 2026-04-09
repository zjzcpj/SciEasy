"""Tests for T-LCMS-009 FractionalLabeling."""

from __future__ import annotations

import pytest
from scieasy_blocks_lcms.isotope_tracing.fractional_labeling import FractionalLabeling
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


def test_fractional_labeling_basic() -> None:
    pd = _pd()
    frame = pd.DataFrame({"Compound": ["glucose", "glucose"], "C13": [0, 1], "S1": [0.75, 0.25]})
    result = FractionalLabeling().process_item(
        _make_mid_table(frame, tracer_atoms=["C13"], sample_columns=["S1"]),
        BlockConfig(params={}),
    )
    out = result._data
    assert list(out.columns) == ["compound", "sample", "fractional_labeling"]
    assert out.loc[0, "fractional_labeling"] == pytest.approx(0.25)


def test_multitracer_m0_requires_all_atoms_zero() -> None:
    pd = _pd()
    frame = pd.DataFrame(
        {
            "Compound": ["cytosine", "cytosine", "cytosine"],
            "C13": [0, 1, 0],
            "H2": [0, 0, 1],
            "S1": [0.2, 0.3, 0.5],
        }
    )
    result = FractionalLabeling().process_item(
        _make_mid_table(frame, tracer_atoms=["C13", "H2"], sample_columns=["S1"]),
        BlockConfig(params={}),
    )
    out = result._data
    assert out.loc[0, "fractional_labeling"] == pytest.approx(0.8)


def test_missing_m0_row_raises() -> None:
    pd = _pd()
    frame = pd.DataFrame({"Compound": ["glucose"], "C13": [1], "S1": [1.0]})
    with pytest.raises(ValueError, match="missing an M\\+0 row"):
        FractionalLabeling().process_item(
            _make_mid_table(frame, tracer_atoms=["C13"], sample_columns=["S1"]),
            BlockConfig(params={}),
        )
