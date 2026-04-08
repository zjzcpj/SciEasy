"""T-IMG-015 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_015_module_importable() -> None:
    """The T-IMG-015 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.morphology.sharpen")


def test_t_img_015_class_has_required_classvars() -> None:
    """Sharpen declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.morphology.sharpen")
    cls = mod.Sharpen
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_sharpen_unsharp_2d() -> None:
    """T-IMG-015 stub — impl pending."""
    pytest.skip("T-IMG-015 impl pending (skeleton continuation A)")


def test_sharpen_invalid_method_raises() -> None:
    """T-IMG-015 stub — impl pending."""
    pytest.skip("T-IMG-015 impl pending (skeleton continuation A)")
