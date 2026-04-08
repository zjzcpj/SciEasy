"""T-IMG-016 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_016_module_importable() -> None:
    """The T-IMG-016 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.morphology.fft_filter")


def test_t_img_016_class_has_required_classvars() -> None:
    """FFTFilter declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.morphology.fft_filter")
    cls = mod.FFTFilter
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_fft_lowpass_2d() -> None:
    """T-IMG-016 stub — impl pending."""
    pytest.skip("T-IMG-016 impl pending (skeleton continuation A)")


def test_fft_invalid_type_raises() -> None:
    """T-IMG-016 stub — impl pending."""
    pytest.skip("T-IMG-016 impl pending (skeleton continuation A)")
