"""PythonRunner — exec() for inline, importlib for script mode."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


class PythonRunner:
    """Python code execution environment.

    Inline mode: runs the script string via ``exec()`` in the provided namespace.
    The namespace is returned, with internal keys (starting with ``_``) stripped.

    Script mode: loads the script file via ``importlib``, calls the entry function
    with ``(inputs, config)`` arguments, and returns its result (expected dict).
    """

    def execute_inline(self, script: str, namespace: dict[str, Any]) -> dict[str, Any]:
        """Execute *script* source code within *namespace* and return results.

        After execution, keys starting with ``_`` and built-in modules are
        stripped from the namespace.  The caller should look for the expected
        output keys.
        """
        exec(script, namespace)  # noqa: S102

        # Strip private/internal keys.
        result: dict[str, Any] = {}
        skip_types = {type(importlib)}  # module type
        for key, value in namespace.items():
            if key.startswith("_"):
                continue
            if key == "config":
                continue
            if type(value) in skip_types:
                continue
            result[key] = value

        return result

    def execute_script(
        self,
        script_path: str | Path,
        entry_function: str,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute *entry_function* from *script_path* with *inputs* and *config*.

        Loads the script as a Python module via importlib, calls the named
        function, and returns its result (must be a dict mapping output port
        names to values).
        """
        path = Path(script_path)
        if not path.exists():
            raise FileNotFoundError(f"Script not found: {path}")

        # Use mtime in module name for hot-reload safety.
        mod_name = f"_scieasy_user_{path.stem}_{int(path.stat().st_mtime)}"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load script: {path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        func = getattr(module, entry_function, None)
        if func is None:
            raise AttributeError(f"Script {path.name} has no function '{entry_function}'")

        result = func(inputs, config)
        if not isinstance(result, dict):
            raise TypeError(f"Entry function '{entry_function}' must return a dict, got {type(result).__name__}")
        return result
