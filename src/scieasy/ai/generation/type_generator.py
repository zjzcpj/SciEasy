"""Generate new DataObject subtypes from a natural-language description."""

from __future__ import annotations


def generate_type(description: str) -> str:
    """Generate ``DataObject`` subtype source code from a description.

    Parameters
    ----------
    description:
        Free-text description of the desired data type, including its
        storage format, shape constraints, and metadata fields.

    Returns
    -------
    str
        Python source code for the generated ``DataObject`` subclass.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
