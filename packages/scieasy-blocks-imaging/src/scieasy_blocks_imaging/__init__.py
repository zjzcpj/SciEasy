"""SciEasy imaging plugin — Phase 11 skeleton.

Public entry points:

- :func:`get_types` — return the four canonical imaging type classes
  (Image / Mask / Label / Transform). Used by the
  ``scieasy.types`` plugin entry-point (T-IMG-038).
- :func:`get_blocks` — return the list of imaging block classes.
  Skeleton returns an empty list; impl agent populates as each
  T-IMG-NNN block becomes importable.
"""

from __future__ import annotations

from scieasy_blocks_imaging.types import Image, Label, Mask, Transform


def get_types() -> list[type]:
    """Return the imaging plugin's exported type classes."""
    return [Image, Mask, Label, Transform]


def get_blocks() -> list[type]:
    """Return the imaging plugin's exported block classes.

    Skeleton: returns an empty list. Impl agent appends each
    T-IMG-002..T-IMG-037 class as it lands.
    """
    return []


__all__ = ["Image", "Label", "Mask", "Transform", "get_blocks", "get_types"]
