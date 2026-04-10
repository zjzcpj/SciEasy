"""AIBlock — LLM-driven processing with prompt templates."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.core.types.text import Text

if TYPE_CHECKING:
    from scieasy.core.types.collection import Collection

logger = logging.getLogger(__name__)


class AIBlock(Block):
    """Block that uses a large language model to process data.

    *model* identifies the LLM backend; *prompt_template* holds the
    template string that is rendered with block inputs before inference.

    The MVP wires existing provider infrastructure (``AIConfig``,
    ``get_provider()``) to a simple prompt-template workflow:

    1. Serialize any input to a text representation.
    2. Substitute into the user-provided prompt template (``{data}``).
    3. Call the configured LLM provider.
    4. Return the response as a ``Text`` DataObject.
    """

    type_name: ClassVar[str] = "ai.llm"
    name: ClassVar[str] = "AI / LLM"
    description: ClassVar[str] = "Process data with a large language model."
    category: ClassVar[str] = "ai"
    version: ClassVar[str] = "0.1.0"

    model: ClassVar[str] = ""
    prompt_template: ClassVar[str] = ""

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="data",
            accepted_types=[],  # Any type
            required=False,
            is_collection=True,
            description="Input data to process (any type). Serialized to text for the LLM.",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="result",
            accepted_types=[Text],
            is_collection=False,
            description="LLM response as Text.",
        ),
    ]

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "default": "",
                "title": "Prompt",
                "description": "Instructions for the LLM. Use {data} to reference the input.",
                "ui_widget": "textarea",
            },
            "provider": {
                "type": "string",
                "enum": ["anthropic", "openai"],
                "default": "anthropic",
                "title": "LLM Provider",
            },
            "model": {
                "type": ["string", "null"],
                "default": None,
                "title": "Model (leave empty for default)",
            },
            "temperature": {
                "type": "number",
                "default": 0.2,
                "minimum": 0.0,
                "maximum": 2.0,
            },
            "max_tokens": {
                "type": "integer",
                "default": 4096,
                "minimum": 1,
            },
            "prompt_file": {
                "type": ["string", "null"],
                "default": None,
                "title": "Load prompt from file (.md / .txt)",
                "ui_widget": "file_browser",
            },
            "system_prompt": {
                "type": ["string", "null"],
                "default": None,
                "title": "System prompt (optional)",
            },
        },
        "required": ["prompt"],
    }

    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        """Run the LLM inference pipeline.

        Steps:
        1. Serialize input data to a text representation.
        2. Build prompt from template (``{data}`` placeholder).
        3. Configure and call the LLM via the provider infrastructure.
        4. Return the response wrapped as ``Text``.
        """
        from scieasy.blocks.ai.providers import AnthropicProvider, OpenAIProvider

        # 1. Serialize input data to text representation.
        raw_data = inputs.get("data")
        data_text = self._serialize_input(raw_data)

        # 2. Build prompt from template.
        # If prompt_file is set and non-empty, read its content as the prompt
        # (overrides the textarea prompt field). Supported: .md, .txt.
        prompt_file = config.get("prompt_file")
        if prompt_file and str(prompt_file).strip():
            from pathlib import Path

            pf = Path(str(prompt_file))
            if not pf.exists():
                raise FileNotFoundError(f"AIBlock: prompt_file not found: {pf}")
            if pf.suffix.lower() not in {".md", ".txt"}:
                raise ValueError(f"AIBlock: prompt_file must be .md or .txt, got {pf.suffix!r}")
            prompt_template = pf.read_text(encoding="utf-8")
        else:
            prompt_template = str(config.get("prompt", ""))
        if not prompt_template:
            raise ValueError("AIBlock: 'prompt' config is required.")

        # Replace {data} placeholder with serialized input.
        prompt = prompt_template.replace("{data}", data_text)

        # 3. Configure and call LLM.
        provider_name = str(config.get("provider", "anthropic"))
        model = config.get("model") or ""
        temperature = float(config.get("temperature", 0.2))
        max_tokens = int(config.get("max_tokens", 4096))
        api_key = ""  # Falls back to provider-specific env var

        provider: AnthropicProvider | OpenAIProvider
        if provider_name == "anthropic":
            provider = AnthropicProvider(api_key=api_key, model=model, max_tokens=max_tokens)
        elif provider_name == "openai":
            provider = OpenAIProvider(api_key=api_key, model=model, max_tokens=max_tokens)
        else:
            raise ValueError(f"AIBlock: unknown provider {provider_name!r}. Use 'anthropic' or 'openai'.")

        system_prompt = config.get("system_prompt")
        response = provider.generate(
            prompt=prompt,
            system=str(system_prompt) if system_prompt else "",
            config={"temperature": temperature, "max_tokens": max_tokens},
        )

        # 4. Wrap response as Text.
        result = Text(content=response, format="plain")
        return {"result": result}  # type: ignore[dict-item]  # non-collection output port

    def _serialize_input(self, data: Any) -> str:
        """Convert any input to a text representation for the LLM."""
        if data is None:
            return "(no input data)"

        from scieasy.core.types.base import DataObject
        from scieasy.core.types.collection import Collection

        if isinstance(data, Collection):
            parts = []
            for i, item in enumerate(data):
                parts.append(f"[Item {i}]: {self._describe_object(item)}")
            return "\n".join(parts)

        if isinstance(data, DataObject):
            return self._describe_object(data)

        return str(data)

    def _describe_object(self, obj: Any) -> str:
        """Create a text description of a DataObject for LLM context."""
        from scieasy.core.types.array import Array
        from scieasy.core.types.dataframe import DataFrame
        from scieasy.core.types.text import Text as TextType

        type_name = type(obj).__name__
        desc = f"Type: {type_name}"

        if isinstance(obj, TextType):
            content = obj.content if hasattr(obj, "content") else ""
            return f"{desc}\nContent: {content}"

        if isinstance(obj, Array):
            desc += f", axes={obj.axes}, shape={obj.shape}, dtype={obj.dtype}"
            # Don't send raw array data to LLM — too large.
            return desc

        if isinstance(obj, DataFrame):
            desc += f", columns={obj.columns}, rows={obj.row_count}"
            # Optionally include first few rows for context.
            try:
                table = obj.to_memory()
                preview = table.slice(0, 5).to_pylist()
                desc += f"\nFirst 5 rows: {preview}"
            except Exception:
                pass
            return desc

        # Generic fallback.
        if hasattr(obj, "storage_ref") and obj.storage_ref:
            desc += f", path={obj.storage_ref.path}"
        return desc
