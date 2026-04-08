"""T-IMG-020 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_020_module_importable() -> None:
    """The T-IMG-020 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.segmentation.blob_detect")


def test_t_img_020_class_has_required_classvars() -> None:
    """BlobDetect declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.segmentation.blob_detect")
    cls = mod.BlobDetect
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_blob_log_basic() -> None:
    """T-IMG-020 stub — impl pending."""
    pytest.skip("T-IMG-020 impl pending (skeleton continuation A)")


def test_blob_invalid_method_raises() -> None:
    """T-IMG-020 stub — impl pending."""
    pytest.skip("T-IMG-020 impl pending (skeleton continuation A)")
