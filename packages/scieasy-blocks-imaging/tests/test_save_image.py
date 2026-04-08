"""T-IMG-003 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_003_module_importable() -> None:
    """The T-IMG-003 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.io.save_image")


def test_t_img_003_class_has_required_classvars() -> None:
    """SaveImage declares the mandatory ProcessBlock/IOBlock ClassVars."""
    mod = importlib.import_module("scieasy_blocks_imaging.io.save_image")
    cls = mod.SaveImage
    assert hasattr(cls, "type_name")
    assert hasattr(cls, "name")
    assert hasattr(cls, "category")
    assert hasattr(cls, "config_schema")


def test_save_single_image_to_file() -> None:
    """T-IMG-003 stub — impl pending."""
    pytest.skip("T-IMG-003 impl pending (skeleton continuation A)")


def test_save_collection_to_directory_indexed() -> None:
    """T-IMG-003 stub — impl pending."""
    pytest.skip("T-IMG-003 impl pending (skeleton continuation A)")


def test_save_length_n_to_file_path_raises() -> None:
    """T-IMG-003 stub — impl pending."""
    pytest.skip("T-IMG-003 impl pending (skeleton continuation A)")


def test_save_tiff_round_trip_preserves_meta() -> None:
    """T-IMG-003 stub — impl pending."""
    pytest.skip("T-IMG-003 impl pending (skeleton continuation A)")
