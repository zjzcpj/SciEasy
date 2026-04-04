"""RRunner — Rscript subprocess execution.

ADR-017: All execution in isolated subprocesses. No rpy2 in-process bridge.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class RRunner:
    """R code execution environment via Rscript subprocess.

    TODO(ADR-017): Implement using Rscript subprocess.

    Design:
        - Inline mode: write R script to temp file, call Rscript subprocess.
        - Script mode: call Rscript subprocess with script path.
        - JSON serialization for data transfer across process boundary.
        - StorageReference-based data flow: only pointers cross boundary.
        - NO rpy2 in-process bridge (ADR-017 prohibits).
    """

    def execute_inline(self, script: str, namespace: dict[str, Any]) -> dict[str, Any]:
        """Execute R script via Rscript subprocess.

        TODO(ADR-017): Write script to temp file, spawn Rscript process,
        pass StorageReference pointers via JSON stdin, read output refs.
        """
        raise NotImplementedError

    def execute_script(
        self,
        script_path: str | Path,
        entry_function: str,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute R script file via Rscript subprocess.

        TODO(ADR-017): Spawn Rscript process with script_path,
        pass StorageReference pointers via JSON, read output refs.
        """
        raise NotImplementedError
