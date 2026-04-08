from __future__ import annotations

from pathlib import Path

import pytest
from scieasy_blocks_lcms.external.elmaven_block import ElMAVENBlock, _classify_export
from scieasy_blocks_lcms.types import MIDTable, MSRawFile, PeakTable

from scieasy.blocks.app.app_block import AppBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.collection import Collection


def test_elmaven_block_class_config() -> None:
    block = ElMAVENBlock()
    assert block.watch_timeout == 1800
    assert block.output_patterns == ["*.csv", "*.tsv", "*.xlsx"]
    assert block.input_ports[0].accepted_types == [MSRawFile]
    assert block.output_ports[0].accepted_types == [PeakTable]
    assert block.output_ports[1].accepted_types == [MIDTable]


def test_elmaven_classify_export_peak_vs_mid(tmp_path: Path) -> None:
    peak_path = tmp_path / "peak.csv"
    peak_path.write_text("compound,medMz\nfoo,100.0\n", encoding="utf-8")
    mid_path = tmp_path / "mid.csv"
    mid_path.write_text("Compound,C13,S1\nfoo,0,1.0\n", encoding="utf-8")

    assert _classify_export(peak_path) == "peak_table"
    assert _classify_export(mid_path) == "mid_table"


@pytest.mark.requires_elmaven
def test_elmaven_end_to_end_launch_and_collect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    peak_path = tmp_path / "peak.csv"
    peak_path.write_text("compound,formula,medMz,medRt\nglucose,C6H12O6,179.0,5.2\n", encoding="utf-8")
    mid_path = tmp_path / "mid.csv"
    mid_path.write_text("Compound,C13,S1\nglucose,0,1.0\n", encoding="utf-8")

    def fake_run(self: AppBlock, inputs: dict, config: BlockConfig) -> dict[str, Collection]:
        return {
            "peak": Collection(items=[Artifact(file_path=peak_path)], item_type=Artifact),
            "mid": Collection(items=[Artifact(file_path=mid_path)], item_type=Artifact),
        }

    monkeypatch.setattr(AppBlock, "run", fake_run)

    raw_path = tmp_path / "sample.mzML"
    raw_path.write_text("<mzML />", encoding="utf-8")

    raw = MSRawFile(file_path=raw_path, meta=MSRawFile.Meta(format="mzML"))
    result = ElMAVENBlock().run(
        {"raw_files": Collection(items=[raw], item_type=MSRawFile)},
        BlockConfig(params={"elmaven_path": "elmaven"}),
    )

    assert len(result["peak_table"]) == 1
    assert len(result["mid_table"]) == 1
