"""Tests for the LoadNpy example block."""

from __future__ import annotations

import numpy as np
import pytest
from load_npy import LoadNpy

from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.array import Array
from scieasy.testing import BlockTestHarness


class TestLoadNpyContract:
    def test_validate_block(self):
        harness = BlockTestHarness(LoadNpy)
        errors = harness.validate_block()
        assert not errors, errors


class TestLoadNpyLogic:
    def test_load_2d(self, tmp_path):
        data = np.random.rand(64, 64).astype(np.float32)
        path = tmp_path / "test.npy"
        np.save(str(path), data)

        block = LoadNpy()
        config = BlockConfig(path=str(path))
        result = block._load_simple(path, config)

        assert isinstance(result, Array)
        assert result.axes == ["y", "x"]
        assert result.shape == (64, 64)
        np.testing.assert_array_equal(result._data, data)  # type: ignore[attr-defined]

    def test_load_3d_with_axes_override(self, tmp_path):
        data = np.random.rand(3, 64, 64).astype(np.float32)
        path = tmp_path / "test.npy"
        np.save(str(path), data)

        block = LoadNpy()
        config = BlockConfig(path=str(path), axes="cyx")
        result = block._load_simple(path, config)

        assert result.axes == ["c", "y", "x"]

    def test_file_not_found(self, tmp_path):
        block = LoadNpy()
        config = BlockConfig(path=str(tmp_path / "nonexistent.npy"))
        with pytest.raises(FileNotFoundError):
            block.load(config)

    def test_wrong_extension(self, tmp_path):
        path = tmp_path / "test.csv"
        path.write_text("a,b\n1,2\n")
        block = LoadNpy()
        config = BlockConfig(path=str(path))
        with pytest.raises(ValueError, match=r"expected \.npy"):
            block.load(config)
