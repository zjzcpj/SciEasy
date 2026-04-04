"""Tests for BlockConfig, BlockResult, and BatchResult."""

from __future__ import annotations

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.result import BatchResult, BlockResult


class TestBlockConfig:
    """BlockConfig — validated parameter container."""

    def test_get_existing_key(self) -> None:
        config = BlockConfig(params={"threshold": 0.5})
        assert config.get("threshold") == 0.5

    def test_get_missing_returns_default(self) -> None:
        config = BlockConfig(params={"threshold": 0.5})
        assert config.get("missing", "fallback") == "fallback"

    def test_get_missing_no_default_returns_none(self) -> None:
        config = BlockConfig(params={})
        assert config.get("missing") is None

    def test_default_params_empty(self) -> None:
        config = BlockConfig()
        assert config.params == {}

    def test_extra_fields_allowed(self) -> None:
        config = BlockConfig(params={"a": 1}, custom_field="hello")
        assert config.custom_field == "hello"  # type: ignore[attr-defined]


class TestBlockResult:
    """BlockResult — single block execution outcome."""

    def test_creation(self) -> None:
        err = ValueError("test")
        result = BlockResult(outputs={"out": 42}, duration_ms=100, error=err)
        assert result.outputs == {"out": 42}
        assert result.duration_ms == 100
        assert result.error is err

    def test_defaults(self) -> None:
        result = BlockResult(outputs={})
        assert result.duration_ms == 0
        assert result.error is None


class TestBatchResult:
    """BatchResult — aggregate batch execution outcome."""

    def test_creation(self) -> None:
        result = BatchResult(
            succeeded=[(0, "ok")],
            failed=[(1, ValueError("bad"))],
            skipped=[2],
        )
        assert len(result.succeeded) == 1
        assert len(result.failed) == 1
        assert result.skipped == [2]

    def test_defaults_empty(self) -> None:
        result = BatchResult()
        assert result.succeeded == []
        assert result.failed == []
        assert result.skipped == []
