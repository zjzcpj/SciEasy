"""Observe intermediate results, suggest or apply parameter changes.

Uses an LLM to analyse a block's current parameters and intermediate
metrics, then proposes new parameter values that are validated against
the block's declared config schema.

ADR-013: AI is optional -- this module raises a clear error when no
API key is available rather than crashing.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def optimize_params(
    block_id: str,
    intermediate_results: dict[str, Any],
    search_space: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Observe intermediate outputs and suggest parameter adjustments.

    Parameters
    ----------
    block_id:
        Identifier of the block whose parameters should be tuned.
    intermediate_results:
        Key-value mapping of metric names to their current values.
    search_space:
        Optional description of the parameter search space.  When
        *None* the optimiser infers the space from the block schema.

    Returns
    -------
    dict[str, Any]
        A dict with ``"suggestions"`` (param name -> new value) and
        ``"explanation"`` (human-readable rationale).

    Raises
    ------
    ValueError
        If *block_id* is not found in the registry or no AI provider
        is configured.
    RuntimeError
        If the LLM fails to produce valid suggestions after retries.
    """
    from scieasy.ai.config import AIConfig, get_provider
    from scieasy.blocks.ai.parsers import extract_json
    from scieasy.blocks.registry import BlockRegistry

    # 1. Look up block schema -------------------------------------------------
    registry = BlockRegistry()
    registry.scan()
    spec = registry.get_spec(block_id)
    if spec is None:
        raise ValueError(f"Block '{block_id}' is not registered. Cannot optimise parameters for an unknown block.")

    config_schema: dict[str, Any] = spec.config_schema or {
        "type": "object",
        "properties": {},
    }

    # 2. Obtain AI provider ----------------------------------------------------
    try:
        ai_config = AIConfig.from_env()
        provider = get_provider(ai_config)
    except (ValueError, ImportError) as exc:
        raise ValueError(
            f"AI provider not available: {exc}. Set SCIEASY_AI_API_KEY or install the required SDK."
        ) from exc

    # 3. Build prompt ----------------------------------------------------------
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(
        block_name=spec.name,
        block_description=spec.description,
        config_schema=config_schema,
        intermediate_results=intermediate_results,
        search_space=search_space,
    )

    # 4. LLM call with retry ---------------------------------------------------
    max_retries = ai_config.max_retries
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            raw_response = provider.generate(
                user_prompt,
                system=system_prompt,
                config=ai_config,
            )
            parsed = extract_json(raw_response)
            suggestions = parsed.get("suggestions", {})
            explanation = parsed.get("explanation", "")

            # 5. Validate suggestions against schema ---------------------------
            validated = _validate_suggestions(suggestions, config_schema)

            return {
                "suggestions": validated,
                "explanation": str(explanation),
            }
        except (ValueError, KeyError, TypeError) as exc:
            last_error = exc
            logger.warning(
                "Parameter optimisation attempt %d/%d failed: %s",
                attempt,
                max_retries,
                exc,
            )
            continue

    raise RuntimeError(
        f"Failed to produce valid parameter suggestions after {max_retries} attempts. Last error: {last_error}"
    )


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def _build_system_prompt() -> str:
    """Return the system-level instruction for the optimisation task."""
    return (
        "You are an expert parameter optimisation assistant for scientific "
        "workflow blocks. Your task is to analyse intermediate results and "
        "suggest improved parameter values.\n\n"
        "RULES:\n"
        "1. Only suggest parameters that exist in the config schema.\n"
        "2. Values must conform to the declared type and constraints "
        "(min, max, enum).\n"
        "3. Provide a brief explanation for each suggested change.\n"
        "4. If no changes would improve the results, return an empty "
        "suggestions dict.\n\n"
        "RESPONSE FORMAT (strict JSON):\n"
        "{\n"
        '  "suggestions": {"param_name": new_value, ...},\n'
        '  "explanation": "Brief rationale for the suggested changes."\n'
        "}"
    )


def _build_user_prompt(
    *,
    block_name: str,
    block_description: str,
    config_schema: dict[str, Any],
    intermediate_results: dict[str, Any],
    search_space: dict[str, Any] | None,
) -> str:
    """Construct the user prompt with block context and metrics."""
    parts: list[str] = []

    parts.append(f"## Block: {block_name}")
    if block_description:
        parts.append(f"Description: {block_description}")

    # Schema summary
    properties = config_schema.get("properties", {})
    if properties:
        parts.append("\n## Parameter Schema")
        for name, prop in properties.items():
            line = f"- **{name}**: type={prop.get('type', 'any')}"
            if "minimum" in prop:
                line += f", min={prop['minimum']}"
            if "maximum" in prop:
                line += f", max={prop['maximum']}"
            if "enum" in prop:
                line += f", allowed={prop['enum']}"
            if "default" in prop:
                line += f", default={prop['default']}"
            if "description" in prop:
                line += f" -- {prop['description']}"
            parts.append(line)

    # Intermediate results
    parts.append("\n## Intermediate Results (current metrics)")
    parts.append(json.dumps(intermediate_results, indent=2, default=str))

    # Search space constraints
    if search_space:
        parts.append("\n## Search Space Constraints")
        parts.append(json.dumps(search_space, indent=2, default=str))

    parts.append(
        "\nSuggest parameter changes that would improve the results. "
        "Respond with a JSON object containing 'suggestions' and 'explanation'."
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate_suggestions(
    suggestions: dict[str, Any],
    config_schema: dict[str, Any],
) -> dict[str, Any]:
    """Validate suggested parameter values against the block's config schema.

    Only keeps parameters that exist in the schema and whose values pass
    type / range / enum checks.  Silently drops invalid suggestions and
    logs a warning for each.

    Returns
    -------
    dict[str, Any]
        The subset of *suggestions* that passed validation.
    """
    properties = config_schema.get("properties", {})
    validated: dict[str, Any] = {}

    for param_name, value in suggestions.items():
        if param_name not in properties:
            logger.warning("Dropping suggestion for unknown parameter '%s'", param_name)
            continue

        prop_schema = properties[param_name]
        try:
            _check_value(param_name, value, prop_schema)
            validated[param_name] = value
        except ValueError as exc:
            logger.warning("Dropping invalid suggestion: %s", exc)

    return validated


def _check_value(
    name: str,
    value: Any,
    schema: dict[str, Any],
) -> None:
    """Raise :class:`ValueError` if *value* violates *schema* constraints."""
    expected_type = schema.get("type")

    if expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"Parameter '{name}': expected integer, got {type(value).__name__}")
    elif expected_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"Parameter '{name}': expected number, got {type(value).__name__}")
    elif expected_type == "string":
        if not isinstance(value, str):
            raise ValueError(f"Parameter '{name}': expected string, got {type(value).__name__}")
    elif expected_type == "boolean" and not isinstance(value, bool):
        raise ValueError(f"Parameter '{name}': expected boolean, got {type(value).__name__}")

    # Range checks
    if "minimum" in schema and isinstance(value, (int, float)) and value < schema["minimum"]:
        raise ValueError(f"Parameter '{name}': value {value} is below minimum {schema['minimum']}")
    if "maximum" in schema and isinstance(value, (int, float)) and value > schema["maximum"]:
        raise ValueError(f"Parameter '{name}': value {value} exceeds maximum {schema['maximum']}")

    # Enum check
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"Parameter '{name}': value {value!r} is not in allowed values {schema['enum']}")
