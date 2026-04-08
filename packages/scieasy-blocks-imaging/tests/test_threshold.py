"""T-IMG-017 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_017_module_importable() -> None:
    """The T-IMG-017 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.segmentation.threshold")


def test_t_img_017_class_has_required_classvars() -> None:
    """Threshold declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.segmentation.threshold")
    cls = mod.Threshold
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_threshold_otsu_returns_mask() -> None:
    """T-IMG-017 stub — impl pending."""
    pytest.skip("T-IMG-017 impl pending (skeleton continuation A)")


def test_threshold_manual_without_value_raises() -> None:
    """T-IMG-017 stub — impl pending."""
    pytest.skip("T-IMG-017 impl pending (skeleton continuation A)")


def test_threshold_invalid_method_raises() -> None:
    """T-IMG-017 stub — impl pending."""
    pytest.skip("T-IMG-017 impl pending (skeleton continuation A)")
