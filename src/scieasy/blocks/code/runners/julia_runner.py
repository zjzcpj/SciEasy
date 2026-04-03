"""JuliaRunner — juliacall or subprocess."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class JuliaRunner:
    """Julia code execution environment.

    Not yet implemented.  Planned backends: juliacall (in-process) or
    Julia subprocess with JSON serialisation.
    """

    def execute_inline(self, script: str, namespace: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            "Julia inline execution is not yet implemented. "
            "Install juliacall and contribute an implementation."
        )

    def execute_script(
        self,
        script_path: str | Path,
        entry_function: str,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "Julia script execution is not yet implemented. "
            "Install juliacall and contribute an implementation."
        )
