"""RRunner — rpy2 bridge or Rscript subprocess."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class RRunner:
    """R code execution environment.

    Not yet implemented.  Planned backends: rpy2 (in-process) or
    Rscript subprocess with JSON serialisation.
    """

    def execute_inline(self, script: str, namespace: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            "R inline execution is not yet implemented. "
            "Install rpy2 and contribute an implementation, or use PythonRunner with rpy2 interop."
        )

    def execute_script(
        self,
        script_path: str | Path,
        entry_function: str,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError(
            "R script execution is not yet implemented. "
            "Install rpy2 and contribute an implementation, or use PythonRunner with rpy2 interop."
        )
