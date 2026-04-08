"""T-IMG-002 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_002_module_importable() -> None:
    """The T-IMG-002 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.io.load_image")


def test_t_img_002_class_has_required_classvars() -> None:
    """LoadImage declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.io.load_image")
    cls = mod.LoadImage
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_load_single_tif_returns_collection_length_one() -> None:
    """T-IMG-002 stub — impl pending."""
    pytest.skip("T-IMG-002 impl pending (skeleton continuation A)")


def test_load_directory_returns_collection_length_n() -> None:
    """T-IMG-002 stub — impl pending."""
    pytest.skip("T-IMG-002 impl pending (skeleton continuation A)")


def test_load_unsupported_extension_raises() -> None:
    """T-IMG-002 stub — impl pending."""
    pytest.skip("T-IMG-002 impl pending (skeleton continuation A)")


def test_load_propagates_source_file_into_meta() -> None:
    """T-IMG-002 stub — impl pending."""
    pytest.skip("T-IMG-002 impl pending (skeleton continuation A)")
