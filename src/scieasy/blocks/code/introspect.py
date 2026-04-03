"""Script introspection — parse run() signature, extract configure() schema."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def introspect_script(script_path: str | Path) -> dict[str, Any]:
    """Parse a user script and extract its interface metadata.

    Returns a dictionary describing the script's ``run()`` signature,
    ``configure()`` schema (if present), and other discoverable metadata.
    """
    raise NotImplementedError
