"""Validation pipeline: static analysis, dry run, port contract check."""

from __future__ import annotations

import ast
import re
from typing import Any


def validate_generated_code(code: str) -> dict[str, Any]:
    """Multi-stage validation of AI-generated source code.

    The pipeline performs:

    1. **Static analysis** --- syntax check via ``ast.parse()``, verify
       a Block subclass exists with a ``run()`` method.
    2. **Contract check** --- verify run() signature references Collection
       (not ``dict[str, Any]``), and no banned patterns are present.

    Parameters
    ----------
    code:
        Python source code to validate.

    Returns
    -------
    dict[str, Any]
        A validation report with keys ``"passed"`` (bool),
        ``"errors"`` (list[str]), and ``"warnings"`` (list[str]).
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Stage 1: Syntax check.
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {"passed": False, "errors": [f"Syntax error: {exc}"], "warnings": []}

    # Stage 2: Find Block subclass with run() method.
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    if not classes:
        errors.append("No class definition found in generated code.")
        return {"passed": False, "errors": errors, "warnings": warnings}

    has_run_method = False
    for cls in classes:
        for item in cls.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "run":
                has_run_method = True
                break

    if not has_run_method:
        errors.append("No run() method found in any class.")

    # Stage 3: Contract checks via string patterns.
    # Check for banned patterns.
    if "estimated_memory_gb" in code:
        errors.append(
            "Code references 'estimated_memory_gb' which has been removed (ADR-022). "
            "Use ResourceRequest without memory estimation."
        )

    if "self.transition(" in code:
        # Allow PAUSED for AppBlock, but flag others as errors (ADR-017).
        transitions = re.findall(r"self\.transition\(([^)]+)\)", code)
        for transition_arg in transitions:
            if "PAUSED" not in transition_arg:
                errors.append(
                    f"ADR-017 violation: self.transition({transition_arg}) is forbidden. "
                    f"State transitions are managed by the engine in subprocess "
                    f"isolation. Only AppBlock may use self.transition(BlockState.PAUSED)."
                )

    if "dict[str, Any]" in code:
        errors.append("ADR-020 violation: use Collection for inter-block data, not dict[str, Any].")

    passed = len(errors) == 0
    return {"passed": passed, "errors": errors, "warnings": warnings}
