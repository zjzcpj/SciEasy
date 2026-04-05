"""Prompt templates for each block and type category.

These dictionaries map category names to prompt-template strings that are
interpolated by the generation functions.

ADR-017: All blocks execute in isolated subprocesses --- templates must NOT
include in-process state transitions.
ADR-020: Inter-block data transport uses Collection --- templates use
``dict[str, Collection]`` for run() signatures.
ADR-022: estimated_memory_gb removed --- templates must NOT reference it.
"""

from __future__ import annotations

BLOCK_TEMPLATES: dict[str, str] = {
    "process": (
        "Generate a ProcessBlock subclass.\n"
        "\n"
        "Requirements:\n"
        "- Declare input_ports with accepted_types matching the input data types.\n"
        "- Declare output_ports with accepted_types matching the output data types.\n"
        "- Override process_item(self, item, config) for Tier-1 (single-item) processing.\n"
        "  The engine auto-iterates Collection items and auto-flushes outputs.\n"
        "- For custom Collection handling, override run() with signature:\n"
        "    def run(self, inputs: dict[str, Collection], config: BlockConfig)"
        " -> dict[str, Collection]:\n"
        "- Use self.pack(items, item_type) to wrap outputs in Collection.\n"
        "- Use self.unpack(collection) or self.map_items(collection, fn) for iteration.\n"
        "\n"
        "Constraints:\n"
        "- Do NOT use dict[str, Any] for port data --- all inter-block data is Collection.\n"
        "- Do NOT call self.transition() --- state transitions are managed by the engine.\n"
        "- Do NOT reference estimated_memory_gb --- it has been removed (ADR-022).\n"
        "- Do NOT import or use ResourceRequest for memory estimation.\n"
    ),
    "io": (
        "Generate an IOBlock subclass for loading or saving data.\n"
        "\n"
        "Requirements:\n"
        "- Declare output_ports (for loaders) or input_ports (for savers).\n"
        "- run() signature:\n"
        "    def run(self, inputs: dict[str, Collection], config: BlockConfig)"
        " -> dict[str, Collection]:\n"
        "- Wrap loaded data in Collection: Collection([data_object], item_type=DataType).\n"
        "- For batch loading, use Collection([item1, item2, ...], item_type=DataType).\n"
        "- Use appropriate format adapters from scieasy.blocks.io.adapters.\n"
        "\n"
        "Constraints:\n"
        "- Do NOT use dict[str, Any] for port data.\n"
        "- Do NOT call self.transition() --- managed by the engine.\n"
        "- Do NOT reference estimated_memory_gb.\n"
    ),
    "code": (
        "Generate a CodeBlock subclass for inline or script execution.\n"
        "\n"
        "Requirements:\n"
        "- Set execution_mode to ExecutionMode.INLINE or ExecutionMode.SCRIPT.\n"
        "- run() signature:\n"
        "    def run(self, inputs: dict[str, Collection], config: BlockConfig)"
        " -> dict[str, Collection]:\n"
        "- Access code via config.get('code') or config.get('script_path').\n"
        "- Wrap outputs in Collection before returning.\n"
        "\n"
        "Constraints:\n"
        "- Do NOT use dict[str, Any] for port data.\n"
        "- Do NOT call self.transition().\n"
        "- Do NOT reference estimated_memory_gb.\n"
    ),
    "app": (
        "Generate an AppBlock subclass for external GUI application integration.\n"
        "\n"
        "Requirements:\n"
        "- Set app_command to the external application executable.\n"
        "- Set output_patterns for expected output file globs.\n"
        "- run() uses FileExchangeBridge to serialize inputs and collect outputs.\n"
        "- Wrap collected Artifact outputs in Collection.\n"
        "\n"
        "Constraints:\n"
        "- app_command must be a simple executable name or absolute path.\n"
        "- Do NOT use dict[str, Any] for port data.\n"
        "- Do NOT call self.transition() except for PAUSED state.\n"
        "- Do NOT reference estimated_memory_gb.\n"
    ),
    "ai": (
        "Generate an AIBlock subclass for LLM-driven processing.\n"
        "\n"
        "Requirements:\n"
        "- Declare input_ports and output_ports with appropriate types.\n"
        "- run() signature:\n"
        "    def run(self, inputs: dict[str, Collection], config: BlockConfig)"
        " -> dict[str, Collection]:\n"
        "- Use config for API keys, model selection, and prompt templates.\n"
        "- Wrap AI-generated outputs in Collection.\n"
        "\n"
        "Constraints:\n"
        "- Do NOT use dict[str, Any] for port data.\n"
        "- Do NOT call self.transition().\n"
        "- Do NOT reference estimated_memory_gb.\n"
    ),
}
"""Prompt templates keyed by block category (e.g. ``"io"``, ``"process"``)."""

TYPE_TEMPLATES: dict[str, str] = {
    "array": (
        "Generate an Array subclass for a specific scientific data type.\n"
        "\n"
        "Requirements:\n"
        "- Inherit from Array (or Image, MSImage, etc. if appropriate).\n"
        "- Set axes ClassVar to the named axis labels (e.g. ['y', 'x', 'channel']).\n"
        "- Set metadata fields appropriate for the domain.\n"
        "- The class is used inside Collection for inter-block transport.\n"
    ),
    "series": (
        "Generate a Series subclass for one-dimensional indexed data.\n"
        "\n"
        "Requirements:\n"
        "- Inherit from Series.\n"
        "- Set index_name and value_name metadata fields.\n"
        "- The class is used inside Collection for inter-block transport.\n"
    ),
    "dataframe": (
        "Generate a DataFrame subclass for tabular scientific data.\n"
        "\n"
        "Requirements:\n"
        "- Inherit from DataFrame.\n"
        "- Set column_schema or expected column names as metadata.\n"
        "- The class is used inside Collection for inter-block transport.\n"
    ),
}
"""Prompt templates keyed by data-type family (e.g. ``"array"``, ``"series"``)."""
