"""T-IMG-014 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_014_module_importable() -> None:
    """The T-IMG-014 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.morphology.ridge_filter")


def test_t_img_014_class_has_required_classvars() -> None:
    """RidgeFilter declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.morphology.ridge_filter")
    cls = mod.RidgeFilter
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_ridge_frangi_2d() -> None:
    """T-IMG-014 stub — impl pending."""
    pytest.skip("T-IMG-014 impl pending (skeleton continuation A)")


def test_ridge_invalid_method_raises() -> None:
    """T-IMG-014 stub — impl pending."""
    pytest.skip("T-IMG-014 impl pending (skeleton continuation A)")
