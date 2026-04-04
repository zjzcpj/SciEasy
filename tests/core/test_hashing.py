"""Tests for content_hash() — all supported data types and edge cases."""

from __future__ import annotations

import numpy as np
import pyarrow as pa

from scieasy.utils.hashing import content_hash


class TestContentHash:
    """content_hash — deterministic hashing for lineage tracking."""

    def test_hash_bytes(self) -> None:
        result = content_hash(b"hello world")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_str(self) -> None:
        result = content_hash("hello world")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_numpy_array(self) -> None:
        arr = np.array([1.0, 2.0, 3.0])
        result = content_hash(arr)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_pyarrow_table(self) -> None:
        table = pa.table({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = content_hash(table)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_fallback_object(self) -> None:
        result = content_hash({"key": "value"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_deterministic(self) -> None:
        data = b"deterministic input"
        assert content_hash(data) == content_hash(data)

    def test_hash_different_inputs_differ(self) -> None:
        assert content_hash(b"input_a") != content_hash(b"input_b")

    def test_hash_empty_bytes(self) -> None:
        result = content_hash(b"")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_empty_string(self) -> None:
        result = content_hash("")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_different_shape_same_bytes(self) -> None:
        a = np.array([1, 2, 3, 4, 5, 6])
        b = np.array([[1, 2, 3], [4, 5, 6]])
        assert content_hash(a) != content_hash(b)

    def test_different_dtype_same_values(self) -> None:
        a = np.array([1, 2], dtype=np.int32)
        b = np.array([1, 2], dtype=np.int64)
        assert content_hash(a) != content_hash(b)

    def test_zero_dim_array(self) -> None:
        result = content_hash(np.array(42))
        assert isinstance(result, str)
        assert len(result) > 0
