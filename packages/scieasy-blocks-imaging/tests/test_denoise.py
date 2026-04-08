"""T-IMG-004 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_004_module_importable() -> None:
    """The T-IMG-004 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.preprocess.denoise")


def test_t_img_004_class_has_required_classvars() -> None:
    """Denoise declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.preprocess.denoise")
    cls = mod.Denoise
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_denoise_gaussian_2d_basic() -> None:
    """T-IMG-004 stub — impl pending."""
    pytest.skip("T-IMG-004 impl pending (skeleton continuation A)")


def test_denoise_invalid_method_raises() -> None:
    """T-IMG-004 stub — impl pending."""
    pytest.skip("T-IMG-004 impl pending (skeleton continuation A)")


def test_denoise_negative_sigma_raises() -> None:
    """T-IMG-004 stub — impl pending."""
    pytest.skip("T-IMG-004 impl pending (skeleton continuation A)")


def test_denoise_5d_iterates_over_extra_axes() -> None:
    """T-IMG-004 stub — impl pending."""
    pytest.skip("T-IMG-004 impl pending (skeleton continuation A)")
