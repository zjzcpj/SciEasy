"""Tests for Collection operation blocks — merge, split, filter, slice (ADR-021)."""

from __future__ import annotations

import pytest

from scieasy.blocks.process.builtins.filter_collection import FilterCollection
from scieasy.blocks.process.builtins.merge_collection import MergeCollection
from scieasy.blocks.process.builtins.slice_collection import SliceCollection
from scieasy.blocks.process.builtins.split_collection import SplitCollection
from scieasy.core.types.array import Image
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy.blocks.base.state import BlockState


def _make_images(n: int) -> list[Image]:
    """Create *n* Image objects with distinct shapes and metadata."""
    return [Image(shape=(i, i), ndim=2, dtype="uint8", metadata={"index": i}) for i in range(1, n + 1)]


# ---------------------------------------------------------------------------
# MergeCollection
# ---------------------------------------------------------------------------


class TestMergeCollection:
    """MergeCollection — concatenate two same-typed Collections."""

    def test_merge_same_type(self) -> None:
        images_a = _make_images(2)
        images_b = _make_images(3)
        col_a = Collection(images_a, item_type=Image)
        col_b = Collection(images_b, item_type=Image)

        block = MergeCollection()
        block.transition(BlockState.READY)
        result = block.run({"input_a": col_a, "input_b": col_b}, block.config)

        merged = result["output"]
        assert isinstance(merged, Collection)
        assert len(merged) == 5
        assert merged.item_type is Image

    def test_merge_type_mismatch(self) -> None:
        col_images = Collection(_make_images(2), item_type=Image)
        col_df = Collection(
            [DataFrame(columns=["a"]), DataFrame(columns=["b"])],
            item_type=DataFrame,
        )

        block = MergeCollection()
        block.transition(BlockState.READY)
        with pytest.raises(TypeError, match="different item types"):
            block.run({"input_a": col_images, "input_b": col_df}, block.config)

    def test_merge_non_collection_raises(self) -> None:
        block = MergeCollection()
        block.transition(BlockState.READY)
        with pytest.raises(TypeError, match="requires Collection inputs"):
            block.run({"input_a": "not_a_collection", "input_b": "neither"}, block.config)


# ---------------------------------------------------------------------------
# SplitCollection
# ---------------------------------------------------------------------------


class TestSplitCollection:
    """SplitCollection — split a Collection at an index."""

    def test_split_at_index(self) -> None:
        images = _make_images(4)
        col = Collection(images, item_type=Image)

        block = SplitCollection(config={"params": {"split_index": 2}})
        block.transition(BlockState.READY)
        result = block.run({"input": col}, block.config)

        assert len(result["output_a"]) == 2
        assert len(result["output_b"]) == 2
        assert result["output_a"].item_type is Image
        assert result["output_b"].item_type is Image

    def test_split_default_midpoint(self) -> None:
        images = _make_images(6)
        col = Collection(images, item_type=Image)

        block = SplitCollection()
        block.transition(BlockState.READY)
        result = block.run({"input": col}, block.config)

        assert len(result["output_a"]) == 3
        assert len(result["output_b"]) == 3

    def test_split_non_collection_raises(self) -> None:
        block = SplitCollection()
        block.transition(BlockState.READY)
        with pytest.raises(TypeError, match="requires a Collection input"):
            block.run({"input": "not_a_collection"}, block.config)


# ---------------------------------------------------------------------------
# FilterCollection
# ---------------------------------------------------------------------------


class TestFilterCollection:
    """FilterCollection — filter by metadata key/value."""

    def test_filter_by_metadata(self) -> None:
        images = _make_images(4)
        col = Collection(images, item_type=Image)

        block = FilterCollection(config={"params": {"predicate_key": "index", "predicate_value": 2}})
        block.transition(BlockState.READY)
        result = block.run({"input": col}, block.config)

        filtered = result["output"]
        assert isinstance(filtered, Collection)
        assert len(filtered) == 1
        assert filtered[0].metadata["index"] == 2
        assert filtered.item_type is Image

    def test_filter_empty_result(self) -> None:
        images = _make_images(3)
        col = Collection(images, item_type=Image)

        block = FilterCollection(config={"params": {"predicate_key": "index", "predicate_value": 999}})
        block.transition(BlockState.READY)
        result = block.run({"input": col}, block.config)

        filtered = result["output"]
        assert isinstance(filtered, Collection)
        assert len(filtered) == 0
        assert filtered.item_type is Image

    def test_filter_missing_key_raises(self) -> None:
        col = Collection(_make_images(2), item_type=Image)

        block = FilterCollection(config={"params": {}})
        block.transition(BlockState.READY)
        with pytest.raises(ValueError, match="predicate_key"):
            block.run({"input": col}, block.config)

    def test_filter_non_collection_raises(self) -> None:
        block = FilterCollection(config={"params": {"predicate_key": "k", "predicate_value": "v"}})
        block.transition(BlockState.READY)
        with pytest.raises(TypeError, match="requires a Collection input"):
            block.run({"input": "not_a_collection"}, block.config)


# ---------------------------------------------------------------------------
# SliceCollection
# ---------------------------------------------------------------------------


class TestSliceCollection:
    """SliceCollection — extract sub-range from a Collection."""

    def test_slice_range(self) -> None:
        images = _make_images(5)
        col = Collection(images, item_type=Image)

        block = SliceCollection(config={"params": {"start": 0, "end": 2}})
        block.transition(BlockState.READY)
        result = block.run({"input": col}, block.config)

        sliced = result["output"]
        assert isinstance(sliced, Collection)
        assert len(sliced) == 2
        assert sliced[0].metadata["index"] == 1
        assert sliced[1].metadata["index"] == 2
        assert sliced.item_type is Image

    def test_slice_default_full_range(self) -> None:
        images = _make_images(3)
        col = Collection(images, item_type=Image)

        block = SliceCollection()
        block.transition(BlockState.READY)
        result = block.run({"input": col}, block.config)

        assert len(result["output"]) == 3

    def test_slice_non_collection_raises(self) -> None:
        block = SliceCollection()
        block.transition(BlockState.READY)
        with pytest.raises(TypeError, match="requires a Collection input"):
            block.run({"input": "not_a_collection"}, block.config)
