"""Validation pipeline: static analysis, dry run, port contract check.

Stage 1 -- Syntax check via ``ast.parse()``.
Stage 2 -- Structural check (class + run method for blocks, class for types).
Stage 3 -- Contract checks via string patterns (banned patterns, ADR compliance).
Stage 4 -- Dry-run execution in restricted namespace.
Stage 5 -- Port contract check (input_ports/output_ports vs run() signature).
"""

from __future__ import annotations

import ast
import re
from typing import Any

# ---------------------------------------------------------------------------
# Block validation (stages 1-3, existing)
# ---------------------------------------------------------------------------


def validate_generated_code(code: str) -> dict[str, Any]:
    """Multi-stage validation of AI-generated block source code.

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
        # Allow PAUSED for AppBlock, but flag others.
        transitions = re.findall(r"self\.transition\(([^)]+)\)", code)
        for transition_arg in transitions:
            if "PAUSED" not in transition_arg:
                warnings.append(
                    f"Code calls self.transition({transition_arg}). "
                    f"State transitions are managed by the engine in subprocess "
                    f"isolation (ADR-017). Remove unless this is an AppBlock "
                    f"PAUSED transition."
                )

    if "dict[str, Any]" in code:
        warnings.append("Code uses 'dict[str, Any]' for port data. Use 'dict[str, Collection]' per ADR-020.")

    passed = len(errors) == 0
    return {"passed": passed, "errors": errors, "warnings": warnings}


# ---------------------------------------------------------------------------
# Stage 4: Dry-run execution
# ---------------------------------------------------------------------------


def dry_run_generated_code(code: str) -> dict[str, Any]:
    """Stage 4: Execute generated code in a restricted namespace.

    Compiles and executes the code to verify it loads without runtime
    errors.  The namespace is isolated -- only builtins are available
    unless the code imports its own dependencies.

    Parameters
    ----------
    code:
        Python source code to execute.

    Returns
    -------
    dict[str, Any]
        Validation report with ``"passed"``, ``"errors"``, ``"warnings"``.
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        namespace: dict[str, Any] = {}
        exec(code, namespace)
        # Verify at least one class was defined.
        classes = [v for v in namespace.values() if isinstance(v, type)]
        if not classes:
            errors.append("Code executed but no class was defined.")
    except SyntaxError as exc:
        errors.append(f"Dry run syntax error: {exc}")
    except ImportError as exc:
        errors.append(f"Dry run import error: {exc}")
    except Exception as exc:
        errors.append(f"Dry run failed: {exc}")

    return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings}


# ---------------------------------------------------------------------------
# Stage 5: Port contract check
# ---------------------------------------------------------------------------


def validate_port_contracts(code: str) -> dict[str, Any]:
    """Stage 5: Verify declared ports are consistent with ``run()`` signature.

    Checks:

    1. ``input_ports`` and ``output_ports`` are declared as class-level
       assignments (typically ``ClassVar`` lists).
    2. A ``run()`` method exists with at least ``self`` and one more
       parameter (the inputs dict).
    3. The ``run()`` method contains a return statement.

    Parameters
    ----------
    code:
        Python source code to validate.

    Returns
    -------
    dict[str, Any]
        Validation report with ``"passed"``, ``"errors"``, ``"warnings"``.
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {"passed": False, "errors": [f"Syntax error: {exc}"], "warnings": []}

    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    if not classes:
        errors.append("No class definition found.")
        return {"passed": False, "errors": errors, "warnings": warnings}

    for cls in classes:
        has_input_ports = False
        has_output_ports = False
        run_method: ast.FunctionDef | None = None

        for item in cls.body:
            # Check for port declarations as class-level assignments.
            if isinstance(item, (ast.Assign, ast.AnnAssign)):
                targets: list[str] = []
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            targets.append(target.id)
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    targets.append(item.target.id)

                if "input_ports" in targets:
                    has_input_ports = True
                if "output_ports" in targets:
                    has_output_ports = True

            # Find run() method.
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == "run":
                run_method = item  # type: ignore[assignment]

        if not has_input_ports and not has_output_ports:
            warnings.append(f"Class '{cls.name}' does not declare input_ports or output_ports.")

        if run_method is not None:
            # Check run() has at least self + inputs parameter.
            arg_count = len(run_method.args.args)
            if arg_count < 2:
                warnings.append(
                    f"Class '{cls.name}' run() has {arg_count} parameter(s); expected at least 2 (self, inputs)."
                )

            # Check for return statement in run().
            has_return = _has_return_statement(run_method)
            if not has_return:
                warnings.append(f"Class '{cls.name}' run() does not contain a return statement.")
        else:
            errors.append(f"Class '{cls.name}' does not define a run() method.")

    return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings}


def _has_return_statement(node: ast.AST) -> bool:
    """Return True if *node* contains at least one ``return`` statement."""
    return any(isinstance(child, ast.Return) for child in ast.walk(node))


# ---------------------------------------------------------------------------
# Type-specific validation
# ---------------------------------------------------------------------------

# Base classes that are acceptable parents for DataObject subtypes.
_DATAOBJECT_BASE_NAMES: frozenset[str] = frozenset(
    {
        "DataObject",
        "Array",
        "Image",
        "MSImage",
        "SRSImage",
        "FluorImage",
        "Series",
        "Spectrum",
        "RamanSpectrum",
        "MassSpectrum",
        "DataFrame",
        "PeakTable",
        "MetabPeakTable",
    }
)

# Families that require an ``axes`` ClassVar declaration.
_ARRAY_FAMILY_BASES: frozenset[str] = frozenset({"Array", "Image", "MSImage", "SRSImage", "FluorImage"})


def validate_generated_type(code: str) -> dict[str, Any]:
    """Validate AI-generated ``DataObject`` subtype code.

    Runs a four-stage pipeline:

    1. **Syntax check** via ``ast.parse()``.
    2. **Inheritance check** -- verify the class inherits from a known
       DataObject base (Array, Series, DataFrame, etc.).
    3. **Axes check** -- for Array-family types, verify ``axes`` ClassVar
       is declared.
    4. **Dry run** -- execute the code in a restricted namespace.

    Parameters
    ----------
    code:
        Python source code to validate.

    Returns
    -------
    dict[str, Any]
        Validation report with ``"passed"``, ``"errors"``, ``"warnings"``.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Stage 1: Syntax check.
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {"passed": False, "errors": [f"Syntax error: {exc}"], "warnings": []}

    # Find class definitions.
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    if not classes:
        errors.append("No class definition found in generated code.")
        return {"passed": False, "errors": errors, "warnings": warnings}

    # Collect all class names defined in this module so we can distinguish
    # imported/re-declared base classes from genuinely new user classes.
    defined_names = {cls.name for cls in classes}

    has_any_valid_type = False
    for cls in classes:
        # Skip classes that ARE known DataObject bases (they may be
        # re-declared locally for import convenience or testing).
        if cls.name in _DATAOBJECT_BASE_NAMES:
            has_any_valid_type = True
            continue

        # Stage 2: Verify inheritance from a DataObject base.
        base_names = _extract_base_names(cls)
        known_bases = base_names & _DATAOBJECT_BASE_NAMES
        # Also accept bases defined locally in the same file that are
        # themselves known bases (e.g. the code re-defines DataObject
        # and then creates a subclass of it).
        locally_known = base_names & defined_names & _DATAOBJECT_BASE_NAMES
        all_known = known_bases | locally_known
        if not all_known:
            errors.append(
                f"Class '{cls.name}' does not inherit from a known DataObject "
                f"base class. Expected one of: {sorted(_DATAOBJECT_BASE_NAMES)}."
            )
            continue

        has_any_valid_type = True

        # Stage 3: For Array-family types, check axes ClassVar.
        is_array_family = bool(all_known & _ARRAY_FAMILY_BASES)
        if is_array_family:
            has_axes = _has_class_var(cls, "axes")
            if not has_axes:
                warnings.append(
                    f"Array-family class '{cls.name}' does not declare an "
                    f"'axes' ClassVar. Array subtypes should define their axis labels."
                )

    if not has_any_valid_type:
        errors.append("No DataObject subtype class found in generated code.")

    # Stage 4: Dry run.
    dry_result = dry_run_generated_code(code)
    errors.extend(dry_result["errors"])
    warnings.extend(dry_result["warnings"])

    return {"passed": len(errors) == 0, "errors": errors, "warnings": warnings}


def _extract_base_names(cls: ast.ClassDef) -> set[str]:
    """Extract simple base class names from a ClassDef node."""
    names: set[str] = set()
    for base in cls.bases:
        if isinstance(base, ast.Name):
            names.add(base.id)
        elif isinstance(base, ast.Attribute):
            names.add(base.attr)
    return names


def _has_class_var(cls: ast.ClassDef, var_name: str) -> bool:
    """Return True if *cls* has a class-level assignment or annotation for *var_name*."""
    for item in cls.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == var_name:
            return True
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    return True
    return False
