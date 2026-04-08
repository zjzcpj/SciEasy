"""T-IMG-012 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_012_module_importable() -> None:
    """The T-IMG-012 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.morphology.morphology_op")


def test_t_img_012_class_has_required_classvars() -> None:
    """MorphologyOp declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.morphology.morphology_op")
    cls = mod.MorphologyOp
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_morphology_erode_2d() -> None:
    """T-IMG-012 stub — impl pending."""
    pytest.skip("T-IMG-012 impl pending (skeleton continuation A)")


def test_morphology_dilate_2d() -> None:
    """T-IMG-012 stub — impl pending."""
    pytest.skip("T-IMG-012 impl pending (skeleton continuation A)")


def test_morphology_invalid_op_raises() -> None:
    """T-IMG-012 stub — impl pending."""
    pytest.skip("T-IMG-012 impl pending (skeleton continuation A)")
