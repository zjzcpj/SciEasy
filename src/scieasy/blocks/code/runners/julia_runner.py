"""JuliaRunner — julia subprocess execution.

ADR-017: All execution in isolated subprocesses. No juliacall in-process bridge.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class JuliaRunner:
    """Julia code execution environment via julia subprocess.

    ADR-017: Implement using julia subprocess.

    Design:
        - Inline mode: write Julia script to temp file, call julia subprocess.
        - Script mode: call julia subprocess with script path.
        - JSON serialization for data transfer across process boundary.
        - StorageReference-based data flow: only pointers cross boundary.
        - NO juliacall in-process bridge (ADR-017 prohibits).
    """

    def execute_inline(self, script: str, namespace: dict[str, Any]) -> dict[str, Any]:
        """Execute Julia script via julia subprocess.

        ADR-017: Write script to temp file, spawn julia process,
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
        """Execute Julia script file via julia subprocess.

        ADR-017: Spawn julia process with script_path,
        pass StorageReference pointers via JSON, read output refs.
        """
        raise NotImplementedError
