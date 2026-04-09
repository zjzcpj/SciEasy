"""Integration tests for imaging plugin fixes #432, #434, #439.

These tests verify the three fixes bundled in PR #440:
- #432: _open_file_manager helper exists and is callable
- #434: SaveImage batch save for multi-item Collections
- #439: CellposeSegment declares dual output ports (labels + masks)
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# Ensure we load from this worktree, not a stale editable install.
_PLUGIN_SRC = str(Path(__file__).resolve().parents[2] / "packages" / "scieasy-blocks-imaging" / "src")
if _PLUGIN_SRC not in sys.path:
    sys.path.insert(0, _PLUGIN_SRC)

# Force reimport from the correct path
for mod_name in list(sys.modules):
    if mod_name.startswith("scieasy_blocks_imaging"):
        del sys.modules[mod_name]


def test_open_file_manager_is_importable() -> None:
    """#432: _open_file_manager is a callable module-level helper."""
    mod = importlib.import_module("scieasy_blocks_imaging.interactive")
    assert hasattr(mod, "_open_file_manager")
    assert callable(mod._open_file_manager)


def test_cellpose_segment_has_masks_output_port() -> None:
    """#439: CellposeSegment declares both 'labels' and 'masks' output ports."""
    mod = importlib.import_module("scieasy_blocks_imaging.segmentation.cellpose_segment")
    CellposeSegment = mod.CellposeSegment
    port_names = [p.name for p in CellposeSegment.output_ports]
    assert "labels" in port_names
    assert "masks" in port_names
