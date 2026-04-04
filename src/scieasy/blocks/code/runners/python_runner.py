"""PythonRunner — subprocess-based Python code execution.

ADR-017: All execution in isolated subprocesses. No in-process exec() or importlib.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class PythonRunner:
    """Python code execution environment via subprocess.

    TODO(ADR-017): Implement subprocess-based execution.

    Inline mode:
        - Serialize script string + StorageReference pointers to subprocess payload.
        - Subprocess worker receives payload, reconstructs ViewProxy instances,
          runs script via exec() in isolated process, collects output refs.
        - Cross-process data: only StorageReference pointers (~100 bytes).
        - NO in-process exec() — all execution in child subprocess.

    Script mode:
        - Serialize script path + StorageReference pointers to subprocess payload.
        - Subprocess imports module, calls entry function with ViewProxy inputs.
        - Cross-process data: only StorageReference pointers.
        - NO in-process importlib — all execution in child subprocess.

    Data flow:
        1. Engine serializes inputs as StorageReference pointers.
        2. Subprocess reconstructs ViewProxy from each StorageReference.
        3. Subprocess calls block.run(inputs, config).
        4. Subprocess _auto_flush() any in-memory outputs.
        5. Subprocess returns output StorageReference pointers.
    """

    def execute_inline(self, script: str, namespace: dict[str, Any]) -> dict[str, Any]:
        """Execute *script* via subprocess (NOT in-process exec).

        TODO(ADR-017): Prepare subprocess payload, call spawn_block_process(),
        read output refs from subprocess stdout.
        """
        raise NotImplementedError

    def execute_script(
        self,
        script_path: str | Path,
        entry_function: str,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute *entry_function* via subprocess (NOT in-process importlib).

        TODO(ADR-017): Prepare subprocess payload with script_path,
        call spawn_block_process(), read output refs.
        """
        raise NotImplementedError
