"""T-IMG-007 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_007_module_importable() -> None:
    """The T-IMG-007 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.preprocess.flat_field_correct")


def test_t_img_007_class_has_required_classvars() -> None:
    """FlatFieldCorrect declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.preprocess.flat_field_correct")
    cls = mod.FlatFieldCorrect
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_flatfield_basic_no_dark() -> None:
    """T-IMG-007 stub — impl pending."""
    pytest.skip("T-IMG-007 impl pending (skeleton continuation A)")


def test_flatfield_with_dark_frame() -> None:
    """T-IMG-007 stub — impl pending."""
    pytest.skip("T-IMG-007 impl pending (skeleton continuation A)")


def test_flatfield_shape_mismatch_raises() -> None:
    """T-IMG-007 stub — impl pending."""
    pytest.skip("T-IMG-007 impl pending (skeleton continuation A)")
