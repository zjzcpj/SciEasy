"""Prompt templates for each block and type category.

These dictionaries map category names to prompt-template strings that are
interpolated by the generation functions.  Populated in later phases.
"""

from __future__ import annotations

BLOCK_TEMPLATES: dict[str, str] = {}
"""Prompt templates keyed by block category (e.g. ``"io"``, ``"process"``)."""

TYPE_TEMPLATES: dict[str, str] = {}
"""Prompt templates keyed by data-type family (e.g. ``"array"``, ``"series"``)."""
