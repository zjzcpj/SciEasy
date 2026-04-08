"""Imaging plugin test configuration.

Prepends the plugin ``src`` directory to ``sys.path`` so the package is
importable at skeleton time before T-IMG-038 wires up the
``pyproject.toml`` entry point and editable install.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
