"""Tests for AIConfig and get_provider factory."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from scieasy.ai.config import AIConfig, get_provider
from scieasy.blocks.ai.providers import (
    AnthropicProvider,
    LLMProvider,
    OpenAIProvider,
)


class TestAIConfigDefaults:
    """Verify AIConfig defaults and basic behaviour."""

    def test_default_values(self) -> None:
        """AIConfig has sensible defaults."""
        cfg = AIConfig()
        assert cfg.provider == "anthropic"
        assert cfg.model == ""
        assert cfg.api_key == ""
        assert cfg.temperature == 0.2
        assert cfg.max_tokens == 4096
        assert cfg.max_retries == 3

    def test_custom_values(self) -> None:
        """AIConfig accepts custom values."""
        cfg = AIConfig(
            provider="openai",
            model="gpt-4o",
            api_key="sk-test",
            temperature=0.8,
            max_tokens=2048,
            max_retries=5,
        )
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4o"
        assert cfg.api_key == "sk-test"
        assert cfg.temperature == 0.8
        assert cfg.max_tokens == 2048
        assert cfg.max_retries == 5

    def test_resolved_model_anthropic(self) -> None:
        """Default model resolves for anthropic provider."""
        cfg = AIConfig(provider="anthropic")
        assert cfg._resolved_model == "claude-sonnet-4-20250514"

    def test_resolved_model_openai(self) -> None:
        """Default model resolves for openai provider."""
        cfg = AIConfig(provider="openai")
        assert cfg._resolved_model == "gpt-4o"

    def test_resolved_model_explicit(self) -> None:
        """Explicit model overrides the default."""
        cfg = AIConfig(provider="anthropic", model="claude-opus-4-20250514")
        assert cfg._resolved_model == "claude-opus-4-20250514"

    def test_resolved_model_unknown_provider(self) -> None:
        """Unknown provider gets empty resolved model."""
        cfg = AIConfig(provider="local-llm")
        assert cfg._resolved_model == ""


class TestAIConfigFromEnv:
    """Verify AIConfig.from_env() with mocked environment."""

    def test_all_env_vars(self) -> None:
        """from_env() reads all recognised environment variables."""
        env = {
            "SCIEASY_AI_PROVIDER": "openai",
            "SCIEASY_AI_API_KEY": "sk-env-key",
            "SCIEASY_AI_MODEL": "gpt-4-turbo",
            "SCIEASY_AI_TEMPERATURE": "0.5",
            "SCIEASY_AI_MAX_TOKENS": "2048",
            "SCIEASY_AI_MAX_RETRIES": "5",
        }
        with patch.dict(os.environ, env, clear=False):
            cfg = AIConfig.from_env()

        assert cfg.provider == "openai"
        assert cfg.api_key == "sk-env-key"
        assert cfg.model == "gpt-4-turbo"
        assert cfg.temperature == 0.5
        assert cfg.max_tokens == 2048
        assert cfg.max_retries == 5

    def test_defaults_when_no_env(self) -> None:
        """from_env() uses defaults when environment variables are absent."""
        # Clear all SCIEASY_AI_ vars
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("SCIEASY_AI_")}
        with patch.dict(os.environ, clean_env, clear=True):
            cfg = AIConfig.from_env()

        assert cfg.provider == "anthropic"
        assert cfg.api_key == ""
        assert cfg.model == ""
        assert cfg.temperature == 0.2
        assert cfg.max_tokens == 4096
        assert cfg.max_retries == 3

    def test_partial_env(self) -> None:
        """from_env() fills only provided vars, uses defaults for the rest."""
        env = {"SCIEASY_AI_PROVIDER": "openai"}
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("SCIEASY_AI_")}
        clean_env.update(env)
        with patch.dict(os.environ, clean_env, clear=True):
            cfg = AIConfig.from_env()

        assert cfg.provider == "openai"
        assert cfg.temperature == 0.2  # default


class TestGetProvider:
    """Test get_provider() factory function."""

    def test_anthropic_provider(self) -> None:
        """get_provider returns AnthropicProvider for 'anthropic' config."""
        mock_sdk = MagicMock()
        cfg = AIConfig(provider="anthropic", api_key="test-key")
        with patch("scieasy.blocks.ai.providers._anthropic_sdk", mock_sdk):
            provider = get_provider(cfg)
        assert isinstance(provider, AnthropicProvider)
        assert isinstance(provider, LLMProvider)

    def test_openai_provider(self) -> None:
        """get_provider returns OpenAIProvider for 'openai' config."""
        mock_sdk = MagicMock()
        cfg = AIConfig(provider="openai", api_key="test-key")
        with patch("scieasy.blocks.ai.providers._openai_sdk", mock_sdk):
            provider = get_provider(cfg)
        assert isinstance(provider, OpenAIProvider)
        assert isinstance(provider, LLMProvider)

    def test_unknown_provider_raises(self) -> None:
        """get_provider raises ValueError for an unknown provider."""
        cfg = AIConfig(provider="unknown-llm", api_key="key")
        with pytest.raises(ValueError, match="Unknown AI provider"):
            get_provider(cfg)

    def test_none_config_uses_env(self) -> None:
        """get_provider(None) calls from_env() and creates provider."""
        mock_sdk = MagicMock()
        env = {
            "SCIEASY_AI_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "env-key",
        }
        clean_env = {k: v for k, v in os.environ.items() if not k.startswith("SCIEASY_AI_")}
        clean_env.update(env)
        with (
            patch.dict(os.environ, clean_env, clear=True),
            patch("scieasy.blocks.ai.providers._anthropic_sdk", mock_sdk),
        ):
            provider = get_provider()
        assert isinstance(provider, AnthropicProvider)

    def test_default_model_used(self) -> None:
        """get_provider uses default model when config.model is empty."""
        mock_sdk = MagicMock()
        cfg = AIConfig(provider="openai", api_key="key", model="")
        with patch("scieasy.blocks.ai.providers._openai_sdk", mock_sdk):
            provider = get_provider(cfg)
        # The provider should have been created with default model "gpt-4o"
        assert provider._model == "gpt-4o"

    def test_explicit_model_used(self) -> None:
        """get_provider passes explicit model from config."""
        mock_sdk = MagicMock()
        cfg = AIConfig(provider="openai", api_key="key", model="gpt-4-turbo")
        with patch("scieasy.blocks.ai.providers._openai_sdk", mock_sdk):
            provider = get_provider(cfg)
        assert provider._model == "gpt-4-turbo"

    def test_missing_sdk_propagates(self) -> None:
        """get_provider propagates ImportError if SDK is missing."""
        cfg = AIConfig(provider="anthropic", api_key="key")
        with (
            patch("scieasy.blocks.ai.providers._anthropic_sdk", None),
            pytest.raises(ImportError, match="anthropic"),
        ):
            get_provider(cfg)
