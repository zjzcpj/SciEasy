"""Generate any of the five block types from a natural-language description.

This module implements the full block generation pipeline:

1. **Category inference** -- infer block category from description keywords
   when not explicitly provided.
2. **Prompt construction** -- combine system prompt, category template, and
   user description.
3. **LLM call** -- invoke the configured ``LLMProvider``.
4. **Code extraction** -- use ``extract_code()`` to pull Python from the
   response.
5. **Validation** -- run ``validate_generated_code()`` to check contracts.
6. **Retry loop** -- on validation failure, feed errors back to the LLM
   (up to ``config.max_retries`` attempts).
7. **Block name extraction** -- parse the class name via ``ast``.

ADR-017: Generated blocks execute in isolated subprocesses.
ADR-020: Inter-block data transport uses Collection.
ADR-022: estimated_memory_gb removed from all templates.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field
from typing import Any

from scieasy.ai.config import AIConfig, get_provider
from scieasy.ai.generation.templates import BLOCK_TEMPLATES
from scieasy.ai.generation.validator import validate_generated_code
from scieasy.blocks.ai.parsers import extract_code

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category inference
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "io": [
        "load",
        "save",
        "read",
        "write",
        "import",
        "export",
        "open",
        "parse",
        "fetch",
        "download",
        "upload",
    ],
    "process": [
        "filter",
        "transform",
        "denoise",
        "segment",
        "threshold",
        "normalize",
        "resize",
        "crop",
        "merge",
        "split",
        "align",
        "register",
        "convert",
        "enhance",
        "smooth",
        "sharpen",
        "detect",
        "extract",
        "classify",
        "cluster",
        "reduce",
        "compute",
        "calculate",
        "analyze",
        "measure",
        "quantify",
    ],
    "code": [
        "script",
        "execute",
        "eval",
        "inline",
        "custom code",
        "run code",
        "python code",
        "r code",
    ],
    "app": [
        "gui",
        "external",
        "application",
        "napari",
        "imagej",
        "fiji",
        "cellprofiler",
        "ilastik",
        "manual",
    ],
    "ai": [
        "llm",
        "language model",
        "gpt",
        "claude",
        "chatgpt",
        "prompt",
        "ai-powered",
        "generative",
    ],
}


def infer_category(description: str) -> str:
    """Infer block category from description keywords.

    Returns the category with the most keyword matches, defaulting
    to ``"process"`` when no keywords match.
    """
    desc_lower = description.lower()
    scores: dict[str, int] = {}
    for category, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in desc_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return "process"

    return max(scores, key=scores.get)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Block name extraction
# ---------------------------------------------------------------------------


def _extract_block_name(code: str) -> str:
    """Extract the first class name from generated code using ``ast``.

    Returns ``"GeneratedBlock"`` if no class can be parsed.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "GeneratedBlock"

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            return node.name

    return "GeneratedBlock"


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a SciEasy block code generator.\n"
    "\n"
    "SciEasy blocks follow these architectural contracts:\n"
    "- ADR-017: All blocks execute in isolated subprocesses. Do NOT include\n"
    "  self.transition() calls -- state transitions are managed by the engine.\n"
    "  (Exception: AppBlock may use self.transition(BlockState.PAUSED) for\n"
    "  manual review steps.)\n"
    "- ADR-020: Inter-block data transport uses Collection. The run() method\n"
    "  signature must be:\n"
    "    def run(self, inputs: dict[str, Collection], config: BlockConfig)"
    " -> dict[str, Collection]:\n"
    "- ADR-022: estimated_memory_gb has been removed. Do NOT reference it.\n"
    "\n"
    "Return ONLY Python code in a single fenced code block.\n"
    "Do not include explanations, comments outside the code, or multiple\n"
    "code blocks.\n"
)


# ---------------------------------------------------------------------------
# Generation result
# ---------------------------------------------------------------------------


@dataclass
class GenerationResult:
    """Result of a block generation attempt.

    Attributes
    ----------
    code:
        Generated Python source code.
    block_name:
        Class name extracted from the generated code.
    validation_report:
        Output from ``validate_generated_code()``.
    attempts:
        Number of LLM calls made (1 = first attempt succeeded).
    category:
        Block category used for generation.
    """

    code: str
    block_name: str
    validation_report: dict[str, Any] = field(default_factory=dict)
    attempts: int = 1
    category: str = ""


# ---------------------------------------------------------------------------
# Main generation function
# ---------------------------------------------------------------------------


def generate_block(
    description: str,
    category: str | None = None,
    config: AIConfig | None = None,
) -> GenerationResult:
    """Generate block source code from a natural-language description.

    Parameters
    ----------
    description:
        Free-text description of the desired block behaviour.
    category:
        Optional block category hint (e.g. ``"io"``, ``"process"``,
        ``"code"``, ``"app"``, ``"ai"``).  When *None* the generator
        infers the category from the description.
    config:
        AI configuration.  When *None* settings are loaded from
        environment variables via ``AIConfig.from_env()``.

    Returns
    -------
    GenerationResult
        The generated code, block name, validation report, attempt
        count, and resolved category.
    """
    if config is None:
        config = AIConfig.from_env()

    # 1. Category inference
    resolved_category = category if category else infer_category(description)

    # 2. Prompt construction
    category_template = BLOCK_TEMPLATES.get(resolved_category, BLOCK_TEMPLATES["process"])
    user_prompt = f"{category_template}\n\nUser request:\n{description}\n"

    # 3. Get LLM provider
    provider = get_provider(config)

    # 4. Generation + validation loop
    max_attempts = max(1, config.max_retries)
    last_code = ""
    last_report: dict[str, Any] = {"passed": False, "errors": ["No generation attempted"], "warnings": []}

    for attempt in range(1, max_attempts + 1):
        logger.info("Block generation attempt %d/%d for category=%r", attempt, max_attempts, resolved_category)

        # On retry, append validation errors to the prompt
        if attempt > 1 and last_report.get("errors"):
            error_feedback = "\n".join(last_report["errors"])
            retry_prompt = (
                f"{user_prompt}\n\n"
                f"Your previous attempt had the following validation errors:\n"
                f"{error_feedback}\n\n"
                f"Please fix these issues and return corrected code."
            )
        else:
            retry_prompt = user_prompt

        # LLM call
        raw_response = provider.generate(retry_prompt, system=_SYSTEM_PROMPT, config=config)

        # Code extraction
        code = extract_code(raw_response, language="python")
        if not code:
            last_code = ""
            last_report = {
                "passed": False,
                "errors": ["LLM returned empty or unparseable response."],
                "warnings": [],
            }
            continue

        last_code = code

        # Validation
        report = validate_generated_code(code)
        last_report = report

        if report["passed"]:
            block_name = _extract_block_name(code)
            return GenerationResult(
                code=code,
                block_name=block_name,
                validation_report=report,
                attempts=attempt,
                category=resolved_category,
            )

        logger.warning(
            "Block generation attempt %d failed validation: %s",
            attempt,
            report["errors"],
        )

    # All attempts exhausted -- return last attempt with its validation report
    block_name = _extract_block_name(last_code) if last_code else "GeneratedBlock"
    return GenerationResult(
        code=last_code,
        block_name=block_name,
        validation_report=last_report,
        attempts=max_attempts,
        category=resolved_category,
    )
