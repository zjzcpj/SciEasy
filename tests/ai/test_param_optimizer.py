"""Tests for AI parameter optimisation with mocked LLM provider."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from scieasy.ai.optimization.param_optimizer import (
    _build_system_prompt,
    _build_user_prompt,
    _check_value,
    _validate_suggestions,
    optimize_params,
)
from scieasy.blocks.registry import BlockSpec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_spec(
    name: str = "TestBlock",
    description: str = "A test block",
    config_schema: dict | None = None,
) -> BlockSpec:
    """Build a minimal BlockSpec for testing."""
    if config_schema is None:
        config_schema = {
            "type": "object",
            "properties": {
                "threshold": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.5,
                    "description": "Detection threshold",
                },
                "iterations": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10,
                },
                "method": {
                    "type": "string",
                    "enum": ["fast", "accurate", "balanced"],
                    "default": "balanced",
                },
            },
        }
    return BlockSpec(
        name=name,
        description=description,
        config_schema=config_schema,
    )


def _mock_registry(spec: BlockSpec | None = None):
    """Return a mock BlockRegistry instance that returns *spec* for any lookup."""
    if spec is None:
        spec = _make_spec()
    mock_reg = MagicMock()
    mock_reg.get_spec.return_value = spec
    return mock_reg


def _mock_provider(response_json: dict) -> MagicMock:
    """Return a mock LLMProvider whose generate() returns *response_json*."""
    mock = MagicMock()
    mock.generate.return_value = json.dumps(response_json)
    return mock


def _patch_optimizer(
    spec: BlockSpec | None = None,
    provider: MagicMock | None = None,
    max_retries: int = 3,
    provider_side_effect: Exception | None = None,
):
    """Return a combined context manager patching BlockRegistry, AIConfig, get_provider.

    Because optimize_params uses lazy imports inside the function body,
    we patch at the source locations.
    """
    if spec is None:
        spec = _make_spec()

    mock_reg_cls = MagicMock()
    mock_reg_instance = _mock_registry(spec)
    mock_reg_cls.return_value = mock_reg_instance

    mock_cfg = MagicMock()
    mock_cfg.max_retries = max_retries

    mock_cfg_cls = MagicMock()
    mock_cfg_cls.from_env.return_value = mock_cfg

    get_provider_kwargs: dict = {}
    if provider_side_effect is not None:
        get_provider_kwargs["side_effect"] = provider_side_effect
    elif provider is not None:
        get_provider_kwargs["return_value"] = provider
    else:
        get_provider_kwargs["return_value"] = MagicMock()

    class _Combined:
        """Combine multiple patches into a single context manager."""

        def __enter__(self):
            self._p1 = patch("scieasy.blocks.registry.BlockRegistry", mock_reg_cls)
            self._p2 = patch("scieasy.ai.config.AIConfig", mock_cfg_cls)
            self._p3 = patch("scieasy.ai.config.get_provider", **get_provider_kwargs)
            self._p1.start()
            self._p2.start()
            self._p3.start()
            return self

        def __exit__(self, *args):
            self._p3.stop()
            self._p2.stop()
            self._p1.stop()

    return _Combined()


# ---------------------------------------------------------------------------
# test_optimize_params_success
# ---------------------------------------------------------------------------


class TestOptimizeParamsSuccess:
    """LLM returns valid JSON with parameter suggestions."""

    def test_returns_suggestions_and_explanation(self) -> None:
        """Happy path: valid suggestions are returned."""
        spec = _make_spec()
        llm_response = {
            "suggestions": {"threshold": 0.7, "iterations": 20},
            "explanation": "Increase threshold for precision.",
        }
        mock_prov = _mock_provider(llm_response)

        with _patch_optimizer(spec=spec, provider=mock_prov):
            result = optimize_params(
                block_id="TestBlock",
                intermediate_results={"accuracy": 0.85},
            )

        assert "suggestions" in result
        assert "explanation" in result
        assert result["suggestions"]["threshold"] == 0.7
        assert result["suggestions"]["iterations"] == 20
        assert result["explanation"] == "Increase threshold for precision."

    def test_empty_suggestions_accepted(self) -> None:
        """LLM returns empty suggestions (no changes recommended)."""
        spec = _make_spec()
        llm_response = {
            "suggestions": {},
            "explanation": "Parameters already optimal.",
        }
        mock_prov = _mock_provider(llm_response)

        with _patch_optimizer(spec=spec, provider=mock_prov):
            result = optimize_params(
                block_id="TestBlock",
                intermediate_results={"accuracy": 0.99},
            )

        assert result["suggestions"] == {}


# ---------------------------------------------------------------------------
# test_optimize_params_invalid_json
# ---------------------------------------------------------------------------


class TestOptimizeParamsInvalidJson:
    """LLM returns garbage text that cannot be parsed as JSON."""

    def test_retries_then_raises(self) -> None:
        """All retries fail -> RuntimeError."""
        spec = _make_spec()

        mock_prov = MagicMock()
        mock_prov.generate.return_value = "I cannot help with that."

        with (
            _patch_optimizer(spec=spec, provider=mock_prov, max_retries=2),
            pytest.raises(RuntimeError, match="Failed to produce valid"),
        ):
            optimize_params(
                block_id="TestBlock",
                intermediate_results={"loss": 0.5},
            )

        # Should have been called max_retries times.
        assert mock_prov.generate.call_count == 2


# ---------------------------------------------------------------------------
# test_optimize_params_invalid_param_value
# ---------------------------------------------------------------------------


class TestOptimizeParamsInvalidParamValue:
    """LLM suggests a value outside schema range."""

    def test_out_of_range_value_dropped(self) -> None:
        """Value exceeding maximum is dropped; other valid ones remain."""
        spec = _make_spec()
        llm_response = {
            "suggestions": {
                "threshold": 5.0,  # max is 1.0 -> should be dropped
                "iterations": 50,  # valid
            },
            "explanation": "Crank threshold up.",
        }
        mock_prov = _mock_provider(llm_response)

        with _patch_optimizer(spec=spec, provider=mock_prov):
            result = optimize_params(
                block_id="TestBlock",
                intermediate_results={"loss": 0.3},
            )

        # threshold should be dropped (out of range), iterations kept
        assert "threshold" not in result["suggestions"]
        assert result["suggestions"]["iterations"] == 50

    def test_invalid_enum_value_dropped(self) -> None:
        """Value not in enum is dropped."""
        spec = _make_spec()
        llm_response = {
            "suggestions": {"method": "turbo"},  # not in enum
            "explanation": "Use turbo mode.",
        }
        mock_prov = _mock_provider(llm_response)

        with _patch_optimizer(spec=spec, provider=mock_prov):
            result = optimize_params(
                block_id="TestBlock",
                intermediate_results={},
            )

        assert "method" not in result["suggestions"]


# ---------------------------------------------------------------------------
# test_optimize_params_no_api_key
# ---------------------------------------------------------------------------


class TestOptimizeParamsNoApiKey:
    """No AI provider is configured."""

    def test_raises_value_error(self) -> None:
        """Missing API key produces a clear ValueError."""
        spec = _make_spec()

        with (
            _patch_optimizer(
                spec=spec,
                provider_side_effect=ValueError("No API key"),
            ),
            pytest.raises(ValueError, match="AI provider not available"),
        ):
            optimize_params(
                block_id="TestBlock",
                intermediate_results={},
            )


# ---------------------------------------------------------------------------
# test_optimize_params_unknown_block
# ---------------------------------------------------------------------------


class TestOptimizeParamsUnknownBlock:
    """Block ID not found in the registry."""

    def test_raises_value_error(self) -> None:
        """Unknown block_id raises ValueError with descriptive message."""
        mock_reg_cls = MagicMock()
        mock_reg_instance = MagicMock()
        mock_reg_instance.get_spec.return_value = None
        mock_reg_cls.return_value = mock_reg_instance

        with (
            patch("scieasy.blocks.registry.BlockRegistry", mock_reg_cls),
            pytest.raises(ValueError, match="not registered"),
        ):
            optimize_params(
                block_id="NonExistentBlock",
                intermediate_results={},
            )


# ---------------------------------------------------------------------------
# Unit tests for internal helpers
# ---------------------------------------------------------------------------


class TestValidateSuggestions:
    """Direct tests for _validate_suggestions."""

    def test_keeps_valid_drops_invalid(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "alpha": {"type": "number", "minimum": 0, "maximum": 1},
                "beta": {"type": "integer", "minimum": 1},
            },
        }
        suggestions = {
            "alpha": 0.5,  # valid
            "beta": 0,  # below minimum -> dropped
            "gamma": 42,  # not in schema -> dropped
        }
        result = _validate_suggestions(suggestions, schema)
        assert result == {"alpha": 0.5}

    def test_empty_suggestions(self) -> None:
        schema = {"type": "object", "properties": {"x": {"type": "number"}}}
        assert _validate_suggestions({}, schema) == {}


class TestCheckValue:
    """Direct tests for _check_value."""

    def test_number_ok(self) -> None:
        _check_value("x", 0.5, {"type": "number", "minimum": 0, "maximum": 1})

    def test_number_too_low(self) -> None:
        with pytest.raises(ValueError, match="below minimum"):
            _check_value("x", -1, {"type": "number", "minimum": 0})

    def test_number_too_high(self) -> None:
        with pytest.raises(ValueError, match="exceeds maximum"):
            _check_value("x", 10, {"type": "number", "maximum": 5})

    def test_string_enum_valid(self) -> None:
        _check_value("m", "fast", {"type": "string", "enum": ["fast", "slow"]})

    def test_string_enum_invalid(self) -> None:
        with pytest.raises(ValueError, match="not in allowed"):
            _check_value("m", "turbo", {"type": "string", "enum": ["fast", "slow"]})

    def test_integer_type_mismatch(self) -> None:
        with pytest.raises(ValueError, match="expected integer"):
            _check_value("n", 1.5, {"type": "integer"})

    def test_boolean_type_mismatch(self) -> None:
        with pytest.raises(ValueError, match="expected boolean"):
            _check_value("flag", 1, {"type": "boolean"})

    def test_boolean_ok(self) -> None:
        _check_value("flag", True, {"type": "boolean"})

    def test_string_type_mismatch(self) -> None:
        with pytest.raises(ValueError, match="expected string"):
            _check_value("name", 42, {"type": "string"})


class TestBuildPrompts:
    """Smoke tests for prompt construction helpers."""

    def test_system_prompt_is_non_empty(self) -> None:
        prompt = _build_system_prompt()
        assert "parameter" in prompt.lower()
        assert "JSON" in prompt

    def test_user_prompt_contains_block_info(self) -> None:
        prompt = _build_user_prompt(
            block_name="MyBlock",
            block_description="Does stuff",
            config_schema={
                "type": "object",
                "properties": {
                    "alpha": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
            intermediate_results={"loss": 0.42},
            search_space=None,
        )
        assert "MyBlock" in prompt
        assert "Does stuff" in prompt
        assert "alpha" in prompt
        assert "0.42" in prompt

    def test_user_prompt_includes_search_space(self) -> None:
        prompt = _build_user_prompt(
            block_name="B",
            block_description="",
            config_schema={"type": "object", "properties": {}},
            intermediate_results={},
            search_space={"alpha": {"min": 0.1, "max": 0.9}},
        )
        assert "Search Space" in prompt
