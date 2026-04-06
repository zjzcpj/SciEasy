"""AI configuration and provider factory.

``AIConfig`` centralises all LLM-related settings (provider name, model,
API key, generation parameters).  ``get_provider()`` is the single factory
function that turns an ``AIConfig`` into a concrete ``LLMProvider``
instance.

ADR-013: AI is Layer 4 -- this module may import from ``scieasy.blocks``
(providers live there) but ``scieasy.blocks`` must never import this
module at runtime.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from scieasy.blocks.ai.providers import (
    AnthropicProvider,
    LLMProvider,
    OpenAIProvider,
)

# Default models per provider
_DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
}


@dataclass
class AIConfig:
    """Configuration for AI / LLM features.

    Attributes
    ----------
    provider:
        Provider backend name -- ``"anthropic"`` or ``"openai"``.
    model:
        Model identifier (e.g. ``"claude-sonnet-4-20250514"``, ``"gpt-4o"``).
        When empty the provider's default model is used.
    api_key:
        API key.  When empty the provider reads from its standard
        environment variable (``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY``).
    temperature:
        Sampling temperature.
    max_tokens:
        Maximum tokens in the generated response.
    max_retries:
        Maximum number of retries on transient errors.
    """

    provider: str = "anthropic"
    model: str = ""
    api_key: str = ""
    temperature: float = 0.2
    max_tokens: int = 4096
    max_retries: int = 3

    # Private: resolved model after applying defaults
    _resolved_model: str = field(init=False, repr=False, default="")

    def __post_init__(self) -> None:
        self._resolved_model = self.model or _DEFAULT_MODELS.get(self.provider, "")

    @classmethod
    def from_env(cls) -> AIConfig:
        """Create an ``AIConfig`` populated from environment variables.

        Recognised variables:

        * ``SCIEASY_AI_PROVIDER`` -- provider name (default ``"anthropic"``)
        * ``SCIEASY_AI_API_KEY``  -- API key (overrides provider-specific vars)
        * ``SCIEASY_AI_MODEL``    -- model identifier
        * ``SCIEASY_AI_TEMPERATURE`` -- sampling temperature
        * ``SCIEASY_AI_MAX_TOKENS``  -- max response tokens
        * ``SCIEASY_AI_MAX_RETRIES`` -- retry count
        """
        provider = os.environ.get("SCIEASY_AI_PROVIDER", "anthropic")
        api_key = os.environ.get("SCIEASY_AI_API_KEY", "")
        model = os.environ.get("SCIEASY_AI_MODEL", "")

        temperature_str = os.environ.get("SCIEASY_AI_TEMPERATURE", "")
        temperature = float(temperature_str) if temperature_str else 0.2

        max_tokens_str = os.environ.get("SCIEASY_AI_MAX_TOKENS", "")
        max_tokens = int(max_tokens_str) if max_tokens_str else 4096

        max_retries_str = os.environ.get("SCIEASY_AI_MAX_RETRIES", "")
        max_retries = int(max_retries_str) if max_retries_str else 3

        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
        )


def get_provider(config: AIConfig | None = None) -> LLMProvider:
    """Return an ``LLMProvider`` instance for the given configuration.

    Parameters
    ----------
    config:
        AI configuration.  When *None* settings are loaded from
        environment variables via ``AIConfig.from_env()``.

    Returns
    -------
    LLMProvider
        A concrete provider instance ready for ``generate()`` calls.

    Raises
    ------
    ValueError
        If ``config.provider`` is not a recognised provider name.
    ImportError
        If the required SDK package is not installed.
    """
    if config is None:
        config = AIConfig.from_env()

    model = config.model or _DEFAULT_MODELS.get(config.provider, "")

    if config.provider == "anthropic":
        return AnthropicProvider(
            api_key=config.api_key,
            model=model,
            max_tokens=config.max_tokens,
        )
    elif config.provider == "openai":
        return OpenAIProvider(
            api_key=config.api_key,
            model=model,
            max_tokens=config.max_tokens,
        )
    else:
        raise ValueError(f"Unknown AI provider: {config.provider!r}. Supported providers: 'anthropic', 'openai'.")
