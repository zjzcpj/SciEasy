"""Verify LCMS loader blocks use file_browser with multi-file path schema.

Regression test for issue #525: all LCMS load blocks should use
``ui_widget: file_browser`` with ``type: ["string", "array"]`` path
config, matching the LoadImage pattern.
"""

from __future__ import annotations

import pytest
from scieasy_blocks_lcms.io.load_mid_table import LoadMIDTable
from scieasy_blocks_lcms.io.load_ms_raw_files import LoadMSRawFiles
from scieasy_blocks_lcms.io.load_peak_table import LoadPeakTable
from scieasy_blocks_lcms.io.load_sample_metadata import LoadSampleMetadata


@pytest.mark.parametrize(
    "block_cls",
    [LoadMSRawFiles, LoadPeakTable, LoadMIDTable, LoadSampleMetadata],
    ids=lambda c: c.__name__,
)
def test_path_config_uses_file_browser(block_cls: type) -> None:
    path_prop = block_cls.config_schema["properties"]["path"]
    assert path_prop["ui_widget"] == "file_browser", f"{block_cls.__name__} should use file_browser"
    assert path_prop["type"] == ["string", "array"], f"{block_cls.__name__} should accept string or array"
    assert path_prop["items"] == {"type": "string"}, f"{block_cls.__name__} items should be string"
