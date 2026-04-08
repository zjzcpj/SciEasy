"""T-IMG-018 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_018_module_importable() -> None:
    """The T-IMG-018 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.segmentation.watershed")


def test_t_img_018_class_has_required_classvars() -> None:
    """Watershed declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.segmentation.watershed")
    cls = mod.Watershed
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_watershed_distance_basic_2d() -> None:
    """T-IMG-018 stub — impl pending."""
    pytest.skip("T-IMG-018 impl pending (skeleton continuation A)")


def test_watershed_with_markers_input() -> None:
    """T-IMG-018 stub — impl pending."""
    pytest.skip("T-IMG-018 impl pending (skeleton continuation A)")


def test_watershed_invalid_method_raises() -> None:
    """T-IMG-018 stub — impl pending."""
    pytest.skip("T-IMG-018 impl pending (skeleton continuation A)")
