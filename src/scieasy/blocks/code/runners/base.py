"""CodeRunner protocol — execute_inline, execute_script."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CodeRunner(Protocol):
    """Structural protocol for language-specific code execution environments.

    Each runner knows how to execute user code either inline (string) or
    from a script file, returning the output namespace.
    """

    # TODO(ADR-017): execute_inline() and execute_script() must operate via subprocess,
    # never in-process. Signature may change to return subprocess handle or output refs.

    def execute_inline(self, script: str, namespace: dict[str, Any]) -> dict[str, Any]:
        """Execute *script* source code within *namespace* and return results."""
        ...

    def execute_script(
        self,
        script_path: str | Path,
        entry_function: str,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute *entry_function* from *script_path* with *inputs* and *config*."""
        ...
