"""Given data description and analysis goal, propose a complete workflow DAG.

This module builds a block catalog from the BlockRegistry, constructs a
prompt for the LLM, and parses + validates the resulting workflow graph.

ADR-013: AI is optional Layer 4. If no API key is configured, a clear
error is raised rather than crashing.
ADR-020: Workflow nodes use Collection-based transport. The planner
includes this in generated workflow metadata.
"""

from __future__ import annotations

import logging
from typing import Any

from scieasy.ai.config import AIConfig, get_provider
from scieasy.blocks.ai.parsers import extract_json
from scieasy.blocks.registry import BlockRegistry

logger = logging.getLogger(__name__)


def _build_block_catalog(registry: BlockRegistry) -> str:
    """Build a text catalog of available blocks for the LLM prompt.

    Parameters
    ----------
    registry:
        A scanned BlockRegistry containing all available block specs.

    Returns
    -------
    str
        A formatted text catalog listing each block's name, category,
        description, and input/output ports.
    """
    specs = registry.all_specs()
    if not specs:
        return "(No blocks registered.)"

    lines: list[str] = []
    for name, spec in sorted(specs.items()):
        lines.append(f"- **{name}** (category: {spec.category})")
        if spec.description:
            lines.append(f"  Description: {spec.description}")
        if spec.type_name:
            lines.append(f"  Type name: {spec.type_name}")
        if spec.input_ports:
            port_strs = _format_ports(spec.input_ports)
            lines.append(f"  Input ports: {port_strs}")
        if spec.output_ports:
            port_strs = _format_ports(spec.output_ports)
            lines.append(f"  Output ports: {port_strs}")
        lines.append("")

    return "\n".join(lines)


def _format_ports(ports: list[Any]) -> str:
    """Format a list of port specs into a readable string."""
    parts: list[str] = []
    for port in ports:
        if isinstance(port, dict):
            name = port.get("name", "unnamed")
            types = port.get("accepted_types", [])
            type_strs = [t if isinstance(t, str) else getattr(t, "__name__", str(t)) for t in types]
            parts.append(f"{name} ({', '.join(type_strs) if type_strs else 'any'})")
        elif hasattr(port, "name"):
            name = port.name
            types = getattr(port, "accepted_types", [])
            type_strs = [t if isinstance(t, str) else getattr(t, "__name__", str(t)) for t in types]
            parts.append(f"{name} ({', '.join(type_strs) if type_strs else 'any'})")
        else:
            parts.append(str(port))
    return ", ".join(parts) if parts else "none"


def _build_system_prompt(catalog: str) -> str:
    """Build the system prompt for workflow synthesis.

    Parameters
    ----------
    catalog:
        The text block catalog to embed in the prompt.

    Returns
    -------
    str
        System prompt instructing the LLM on the expected output format.
    """
    return (
        "You are a workflow design assistant for SciEasy, a scientific "
        "workflow platform. Your task is to design a workflow DAG (directed "
        "acyclic graph) that processes the user's data to achieve their goal.\n"
        "\n"
        "## Rules\n"
        "1. Use ONLY blocks from the provided catalog below.\n"
        "2. Connect blocks via their declared port names.\n"
        "3. Assign a unique string ID to each node (e.g. 'node-1', 'node-2').\n"
        "4. Include layout positions (x, y) for canvas rendering.\n"
        "5. All inter-block data transport uses Collection-based types "
        "(per ADR-020).\n"
        "6. Provide a brief explanation of the workflow design.\n"
        "\n"
        "## Output format\n"
        "Return a JSON object with exactly this structure:\n"
        "```json\n"
        "{\n"
        '  "nodes": [\n'
        "    {\n"
        '      "id": "node-1",\n'
        '      "block_type": "<block name from catalog>",\n'
        '      "config": {},\n'
        '      "layout": {"x": 100, "y": 100}\n'
        "    }\n"
        "  ],\n"
        '  "edges": [\n'
        "    {\n"
        '      "source": "node-1",\n'
        '      "target": "node-2"\n'
        "    }\n"
        "  ],\n"
        '  "metadata": {\n'
        '    "transport": "collection"\n'
        "  },\n"
        '  "explanation": "Brief explanation of the workflow design."\n'
        "}\n"
        "```\n"
        "\n"
        "## Available blocks\n"
        f"{catalog}\n"
    )


def _build_user_prompt(data_description: str, goal: str) -> str:
    """Build the user prompt from the data description and goal."""
    return (
        f"## Data description\n{data_description}\n\n"
        f"## Analysis goal\n{goal}\n\n"
        "Please design a workflow that processes this data to achieve the "
        "stated goal. Use only blocks from the catalog above."
    )


def _validate_workflow(
    result: dict[str, Any],
    registry: BlockRegistry,
) -> list[str]:
    """Validate the parsed workflow result.

    Parameters
    ----------
    result:
        The parsed JSON dict from the LLM response.
    registry:
        The block registry used to verify block_type references.

    Returns
    -------
    list[str]
        A list of validation error messages. Empty if valid.
    """
    errors: list[str] = []

    # Check top-level keys
    if "nodes" not in result:
        errors.append("Missing required key 'nodes'.")
    if "edges" not in result:
        errors.append("Missing required key 'edges'.")

    if errors:
        return errors

    nodes = result["nodes"]
    edges = result["edges"]

    if not isinstance(nodes, list):
        errors.append("'nodes' must be a list.")
        return errors
    if not isinstance(edges, list):
        errors.append("'edges' must be a list.")
        return errors

    # Validate nodes
    node_ids: set[str] = set()
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"Node at index {i} is not an object.")
            continue
        if "id" not in node:
            errors.append(f"Node at index {i} is missing 'id'.")
        else:
            node_id = node["id"]
            if node_id in node_ids:
                errors.append(f"Duplicate node id: '{node_id}'.")
            node_ids.add(node_id)

        if "block_type" not in node:
            errors.append(f"Node at index {i} is missing 'block_type'.")
        else:
            block_type = node["block_type"]
            spec = registry.get_spec(block_type)
            if spec is None:
                errors.append(f"Node '{node.get('id', i)}' references unknown block_type '{block_type}'.")

    # Validate edges
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"Edge at index {i} is not an object.")
            continue
        if "source" not in edge:
            errors.append(f"Edge at index {i} is missing 'source'.")
        elif edge["source"] not in node_ids:
            errors.append(f"Edge at index {i} references unknown source '{edge['source']}'.")
        if "target" not in edge:
            errors.append(f"Edge at index {i} is missing 'target'.")
        elif edge["target"] not in node_ids:
            errors.append(f"Edge at index {i} references unknown target '{edge['target']}'.")

    return errors


def plan_workflow(data_description: str, goal: str) -> dict[str, Any]:
    """Propose a complete workflow DAG for the given data and goal.

    Parameters
    ----------
    data_description:
        Free-text description of the input dataset(s), including format,
        modality, and approximate size.
    goal:
        Free-text description of the desired analysis outcome.

    Returns
    -------
    dict[str, Any]
        A serialisable workflow graph containing ``"nodes"``,
        ``"edges"``, and ``"explanation"`` keys that conform to the
        workflow schema.

    Raises
    ------
    RuntimeError
        If the LLM fails to produce a valid workflow after all retries.
    ValueError
        If no AI provider is configured (no API key).
    """
    # Load AI configuration from environment
    config = AIConfig.from_env()

    # Obtain the LLM provider -- raises ValueError/ImportError if not
    # configured (ADR-013: AI is optional, clear error on missing key)
    try:
        provider = get_provider(config)
    except (ValueError, ImportError) as exc:
        raise ValueError(
            f"AI provider not available: {exc}. "
            "Set SCIEASY_AI_API_KEY or the provider-specific API key "
            "environment variable to enable AI features."
        ) from exc

    # Build block catalog from registry
    registry = BlockRegistry()
    registry.scan()
    catalog = _build_block_catalog(registry)

    # Build prompts
    system_prompt = _build_system_prompt(catalog)
    user_prompt = _build_user_prompt(data_description, goal)

    # Retry loop
    max_retries = config.max_retries
    last_error: str = ""

    for attempt in range(max_retries):
        # On retry, append validation errors to the prompt
        if attempt > 0 and last_error:
            retry_prompt = (
                f"{user_prompt}\n\n"
                f"## Previous attempt failed validation\n"
                f"Errors:\n{last_error}\n\n"
                f"Please fix these errors and try again."
            )
        else:
            retry_prompt = user_prompt

        try:
            raw_response = provider.generate(
                retry_prompt,
                system=system_prompt,
                config=config,
            )
        except Exception as exc:
            logger.warning(
                "LLM call failed (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                exc,
            )
            last_error = f"LLM call failed: {exc}"
            continue

        # Parse JSON from response
        try:
            result = extract_json(raw_response)
        except ValueError as exc:
            logger.warning(
                "JSON extraction failed (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                exc,
            )
            last_error = f"JSON extraction failed: {exc}"
            continue

        # Validate the workflow structure
        validation_errors = _validate_workflow(result, registry)
        if validation_errors:
            last_error = "\n".join(validation_errors)
            logger.warning(
                "Workflow validation failed (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                last_error,
            )
            continue

        # Success -- ensure required top-level keys in output
        return {
            "nodes": result["nodes"],
            "edges": result["edges"],
            "explanation": result.get("explanation", ""),
            "metadata": result.get("metadata", {"transport": "collection"}),
        }

    raise RuntimeError(f"Failed to generate a valid workflow after {max_retries} attempts. Last error: {last_error}")
