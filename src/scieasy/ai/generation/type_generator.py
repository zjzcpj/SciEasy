"""Generate new DataObject subtypes from a natural-language description.

Uses an LLM provider to generate Python source code for a DataObject
subclass, then validates it through the type validation pipeline
(syntax, inheritance, axes, dry-run).

ADR-013: AI is Layer 4 -- this module imports from ``scieasy.ai.config``
and ``scieasy.blocks.ai`` but core modules must not import this.
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from scieasy.ai.config import AIConfig, get_provider
from scieasy.ai.generation.templates import TYPE_TEMPLATES
from scieasy.ai.generation.validator import validate_generated_type
from scieasy.blocks.ai.parsers import extract_code

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class TypeGenerationResult:
    """Result of a type generation attempt.

    Attributes
    ----------
    code:
        Generated Python source code for the DataObject subclass.
    type_name:
        Extracted class name from the generated code.
    type_family:
        Category of the generated type (``"array"``, ``"series"``,
        or ``"dataframe"``).
    validation_report:
        Output of ``validate_generated_type()`` for the final code.
    attempts:
        Number of generation attempts before success (or giving up).
    """

    code: str
    type_name: str
    type_family: str
    validation_report: dict[str, Any] = field(default_factory=dict)
    attempts: int = 1


# ---------------------------------------------------------------------------
# Family inference
# ---------------------------------------------------------------------------

# Keyword patterns mapped to type families.
_FAMILY_KEYWORDS: dict[str, list[str]] = {
    "array": [
        "image",
        "spatial",
        "hypercube",
        "raster",
        "matrix",
        "ndarray",
        "pixel",
        "voxel",
        "microscop",
        "fluorescen",
    ],
    "series": [
        "spectrum",
        "spectra",
        "chromatogram",
        "time.?series",
        "1d",
        "one.?dimensional",
        "waveform",
        "signal",
        "trace",
    ],
    "dataframe": [
        "table",
        "column",
        "tabular",
        "csv",
        "row",
        "record",
        "peak.?list",
        "annotation",
        "metadata.?table",
    ],
}


def infer_type_family(description: str) -> str:
    """Infer the type family from a natural-language *description*.

    Scans the description for known keyword patterns and returns the
    best-matching family.  Falls back to ``"array"`` when no strong
    signal is found (arrays are the most common scientific data type).

    Parameters
    ----------
    description:
        Free-text description of the desired data type.

    Returns
    -------
    str
        One of ``"array"``, ``"series"``, or ``"dataframe"``.
    """
    desc_lower = description.lower()
    scores: dict[str, int] = {"array": 0, "series": 0, "dataframe": 0}
    for family, keywords in _FAMILY_KEYWORDS.items():
        for kw in keywords:
            if re.search(kw, desc_lower):
                scores[family] += 1
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return "array"  # Default fallback.
    return best


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a SciEasy data type generator.\n"
    "\n"
    "Your job is to produce a Python class that is a DataObject subclass.\n"
    "\n"
    "DataObject contract requirements:\n"
    "- The class MUST inherit from one of: Array, Image, MSImage, SRSImage, "
    "FluorImage, Series, Spectrum, RamanSpectrum, MassSpectrum, DataFrame, "
    "PeakTable, MetabPeakTable.\n"
    "- For Array-family types, you MUST declare an `axes` ClassVar with named "
    "axis labels (e.g. `axes: ClassVar[list[str]] = ['y', 'x', 'channel']`).\n"
    "- The class is used inside Collection for inter-block data transport.\n"
    "- Import the parent class from scieasy.core.types (e.g. "
    "`from scieasy.core.types.array import Array`).\n"
    "- Import ClassVar from typing.\n"
    "- Include type annotations and a docstring.\n"
    "\n"
    "Return ONLY Python code in a fenced code block.\n"
    "Do NOT include usage examples or explanations outside the code block.\n"
)


def _build_prompt(description: str, type_family: str) -> str:
    """Build the user prompt from description and type template."""
    template = TYPE_TEMPLATES.get(type_family, "")
    prompt = f"Template guidelines:\n{template}\n\nUser request:\n{description}\n"
    return prompt


def _build_retry_prompt(
    description: str,
    type_family: str,
    previous_code: str,
    validation_errors: list[str],
) -> str:
    """Build a retry prompt that includes previous errors."""
    template = TYPE_TEMPLATES.get(type_family, "")
    error_text = "\n".join(f"- {e}" for e in validation_errors)
    prompt = (
        f"Template guidelines:\n{template}\n\n"
        f"User request:\n{description}\n\n"
        f"Your previous attempt had validation errors:\n{error_text}\n\n"
        f"Previous code:\n```python\n{previous_code}\n```\n\n"
        f"Fix the errors and return corrected Python code in a fenced code block.\n"
    )
    return prompt


# ---------------------------------------------------------------------------
# Type name extraction
# ---------------------------------------------------------------------------


def _extract_type_name(code: str) -> str:
    """Extract the first class name from generated *code* using AST.

    Returns
    -------
    str
        The class name, or ``"UnknownType"`` if parsing fails.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "UnknownType"

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            return node.name
    return "UnknownType"


# ---------------------------------------------------------------------------
# Main generation function
# ---------------------------------------------------------------------------


def generate_type(
    description: str,
    type_family: str | None = None,
    config: AIConfig | None = None,
) -> TypeGenerationResult:
    """Generate ``DataObject`` subtype source code from a description.

    Parameters
    ----------
    description:
        Free-text description of the desired data type, including its
        storage format, shape constraints, and metadata fields.
    type_family:
        Type family hint (``"array"``, ``"series"``, or ``"dataframe"``).
        When *None* the family is inferred from the description.
    config:
        LLM configuration.  When *None* settings are loaded from
        environment variables.

    Returns
    -------
    TypeGenerationResult
        The generated code, extracted type name, validation report,
        and number of attempts.

    Raises
    ------
    RuntimeError
        If all retry attempts fail validation.
    """
    if config is None:
        config = AIConfig.from_env()

    # Step 1: Family inference.
    if type_family is None:
        type_family = infer_type_family(description)

    provider = get_provider(config)
    max_attempts = max(1, config.max_retries)

    code = ""
    validation_report: dict[str, Any] = {}

    for attempt in range(1, max_attempts + 1):
        # Step 2: Prompt construction.
        if attempt == 1:
            prompt = _build_prompt(description, type_family)
        else:
            prompt = _build_retry_prompt(
                description,
                type_family,
                code,
                validation_report.get("errors", []),
            )

        # Step 3: LLM call.
        logger.info("Type generation attempt %d/%d", attempt, max_attempts)
        raw_response = provider.generate(prompt, system=_SYSTEM_PROMPT, config=config)

        # Step 4: Code extraction.
        code = extract_code(raw_response)
        if not code:
            validation_report = {
                "passed": False,
                "errors": ["LLM returned empty or unparseable response."],
                "warnings": [],
            }
            continue

        # Step 5: Validation.
        validation_report = validate_generated_type(code)

        if validation_report["passed"]:
            # Step 6: Extract type name.
            type_name = _extract_type_name(code)
            return TypeGenerationResult(
                code=code,
                type_name=type_name,
                type_family=type_family,
                validation_report=validation_report,
                attempts=attempt,
            )

        logger.warning(
            "Attempt %d validation failed: %s",
            attempt,
            validation_report.get("errors", []),
        )

    # All attempts exhausted.
    raise RuntimeError(
        f"Type generation failed after {max_attempts} attempts. "
        f"Last validation errors: {validation_report.get('errors', [])}"
    )
