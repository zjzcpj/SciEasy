from __future__ import annotations

from pathlib import Path

import pytest
from scieasy_blocks_lcms.io.load_ms_raw_files import LoadMSRawFiles
from scieasy_blocks_lcms.types import MSRawFile

from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.collection import Collection


def _write_mzml(path: Path, *, positive: bool = True) -> None:
    polarity_accession = "MS:1000130" if positive else "MS:1000129"
    path.write_text(
        f"""
<mzML>
  <run startTimeStamp="2026-04-08T01:02:03Z">
    <instrumentConfiguration id="IC1" name="Q Exactive HF" />
    <cvParam accession="{polarity_accession}" />
  </run>
</mzML>
""".strip(),
        encoding="utf-8",
    )


def test_load_single_mzml_file(tmp_path: Path) -> None:
    path = tmp_path / "sample.mzML"
    _write_mzml(path)

    result = LoadMSRawFiles().load(BlockConfig(params={"path": str(tmp_path), "pattern": "*.mzML"}))
    assert isinstance(result, Collection)
    assert len(result) == 1
    item = result[0]
    assert isinstance(item, MSRawFile)
    assert item.meta.format == "mzML"
    assert item.meta.polarity == "+"
    assert item.meta.instrument == "Q Exactive HF"
    assert item.meta.sample_id == "sample"


def test_load_recursive_flag_controls_subdirs(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    _write_mzml(nested / "deep.mzML", positive=False)

    non_recursive = LoadMSRawFiles().load(
        BlockConfig(params={"path": str(tmp_path), "pattern": "*.mzML", "recursive": False})
    )
    recursive = LoadMSRawFiles().load(
        BlockConfig(params={"path": str(tmp_path), "pattern": "*.mzML", "recursive": True})
    )

    assert len(non_recursive) == 0
    assert len(recursive) == 1
    assert recursive[0].meta.polarity == "-"


def test_load_raises_on_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        LoadMSRawFiles().load(BlockConfig(params={"path": str(tmp_path / "missing")}))


def test_load_empty_glob_returns_empty_collection(tmp_path: Path) -> None:
    result = LoadMSRawFiles().load(BlockConfig(params={"path": str(tmp_path), "pattern": "*.mzML"}))
    assert isinstance(result, Collection)
    assert len(result) == 0


def test_load_raw_file_records_path_only(tmp_path: Path) -> None:
    raw_path = tmp_path / "sample.raw"
    raw_path.write_bytes(b"RAW")

    result = LoadMSRawFiles().load(BlockConfig(params={"path": str(tmp_path), "pattern": "*.raw"}))
    assert result[0].file_path == raw_path
    assert result[0].meta.format == "raw"
    assert result[0].meta.instrument is None


def test_load_d_folder_records_path_only(tmp_path: Path) -> None:
    d_path = tmp_path / "sample.d"
    d_path.mkdir()

    result = LoadMSRawFiles().load(BlockConfig(params={"path": str(tmp_path), "pattern": "*.d"}))
    assert result[0].file_path == d_path
    assert result[0].meta.format == "d"


def test_format_hint_override(tmp_path: Path) -> None:
    path = tmp_path / "sample.mzML"
    _write_mzml(path)

    result = LoadMSRawFiles().load(
        BlockConfig(params={"path": str(tmp_path), "pattern": "*.mzML", "format_hint": "mzXML"})
    )
    assert result[0].meta.format == "mzXML"
