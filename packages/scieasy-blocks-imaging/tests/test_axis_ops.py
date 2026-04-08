"""T-IMG-010 skeleton tests — impl pending (Sprint C continuation A)."""

from __future__ import annotations

import importlib

import pytest


def test_t_img_010_module_importable() -> None:
    """The T-IMG-010 module imports cleanly at skeleton time."""
    importlib.import_module("scieasy_blocks_imaging.preprocess.axis_ops")


def test_axis_split_c_returns_collection_per_channel() -> None:
    """T-IMG-010 stub — impl pending."""
    pytest.skip("T-IMG-010 impl pending (skeleton continuation A)")


def test_axis_merge_inverse_of_split() -> None:
    """T-IMG-010 stub — impl pending."""
    pytest.skip("T-IMG-010 impl pending (skeleton continuation A)")


def test_axis_merge_inconsistent_shapes_raises() -> None:
    """T-IMG-010 stub — impl pending."""
    pytest.skip("T-IMG-010 impl pending (skeleton continuation A)")
