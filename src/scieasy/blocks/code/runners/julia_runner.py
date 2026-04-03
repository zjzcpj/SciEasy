"""JuliaRunner — juliacall or subprocess."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class JuliaRunner:
    """Julia code execution environment."""

    def execute_inline(self, script: str, namespace: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def execute_script(
        self,
        script_path: str | Path,
        entry_function: str,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError
