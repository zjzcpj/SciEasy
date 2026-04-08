"""T-IMG-019 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_019_module_importable() -> None:
    """The T-IMG-019 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.segmentation.cellpose_segment")


def test_t_img_019_class_has_required_classvars() -> None:
    """CellposeSegment declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.segmentation.cellpose_segment")
    cls = mod.CellposeSegment
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_cellpose_class_exists_in_palette() -> None:
    """T-IMG-019 stub — impl pending."""
    pytest.skip("T-IMG-019 impl pending (skeleton continuation A)")


def test_cellpose_setup_loads_model_once() -> None:
    """T-IMG-019 stub — impl pending."""
    pytest.skip("T-IMG-019 impl pending (skeleton continuation A)")


def test_cellpose_teardown_releases_state() -> None:
    """T-IMG-019 stub — impl pending."""
    pytest.skip("T-IMG-019 impl pending (skeleton continuation A)")


def test_cellpose_missing_dependency_raises_friendly_import_error() -> None:
    """T-IMG-019 stub — impl pending."""
    pytest.skip("T-IMG-019 impl pending (skeleton continuation A)")
