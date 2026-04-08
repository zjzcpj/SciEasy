"""T-IMG-006 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_006_module_importable() -> None:
    """The T-IMG-006 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.preprocess.normalize")


def test_t_img_006_class_has_required_classvars() -> None:
    """Normalize declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.preprocess.normalize")
    cls = mod.Normalize
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_normalize_minmax_2d_to_0_1() -> None:
    """T-IMG-006 stub — impl pending."""
    pytest.skip("T-IMG-006 impl pending (skeleton continuation A)")


def test_normalize_zscore_mean_zero_std_one() -> None:
    """T-IMG-006 stub — impl pending."""
    pytest.skip("T-IMG-006 impl pending (skeleton continuation A)")


def test_normalize_invalid_method_raises() -> None:
    """T-IMG-006 stub — impl pending."""
    pytest.skip("T-IMG-006 impl pending (skeleton continuation A)")
