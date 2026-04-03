"""Generate any of the five block types from a natural-language description."""

from __future__ import annotations


def generate_block(description: str, category: str | None = None) -> str:
    """Generate block source code from a natural-language description.

    Parameters
    ----------
    description:
        Free-text description of the desired block behaviour.
    category:
        Optional block category hint (e.g. ``"io"``, ``"process"``,
        ``"code"``, ``"app"``, ``"ai"``).  When *None* the generator
        infers the category from the description.

    Returns
    -------
    str
        Python source code for the generated block, ready to be written
        to a module file.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
