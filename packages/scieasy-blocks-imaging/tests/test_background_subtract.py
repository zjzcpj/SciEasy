"""T-IMG-005 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_005_module_importable() -> None:
    """The T-IMG-005 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.preprocess.background_subtract")


def test_t_img_005_class_has_required_classvars() -> None:
    """BackgroundSubtract declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.preprocess.background_subtract")
    cls = mod.BackgroundSubtract
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_background_rollingball_2d() -> None:
    """T-IMG-005 stub — impl pending."""
    pytest.skip("T-IMG-005 impl pending (skeleton continuation A)")


def test_background_constant_subtracts_value() -> None:
    """T-IMG-005 stub — impl pending."""
    pytest.skip("T-IMG-005 impl pending (skeleton continuation A)")


def test_background_invalid_method_raises() -> None:
    """T-IMG-005 stub — impl pending."""
    pytest.skip("T-IMG-005 impl pending (skeleton continuation A)")
