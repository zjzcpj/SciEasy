"""T-IMG-013 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_013_module_importable() -> None:
    """The T-IMG-013 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.morphology.edge_detect")


def test_t_img_013_class_has_required_classvars() -> None:
    """EdgeDetect declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.morphology.edge_detect")
    cls = mod.EdgeDetect
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_edge_sobel_2d() -> None:
    """T-IMG-013 stub — impl pending."""
    pytest.skip("T-IMG-013 impl pending (skeleton continuation A)")


def test_edge_canny_thresholds_param() -> None:
    """T-IMG-013 stub — impl pending."""
    pytest.skip("T-IMG-013 impl pending (skeleton continuation A)")


def test_edge_invalid_method_raises() -> None:
    """T-IMG-013 stub — impl pending."""
    pytest.skip("T-IMG-013 impl pending (skeleton continuation A)")
