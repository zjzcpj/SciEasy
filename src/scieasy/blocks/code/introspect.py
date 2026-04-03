"""Script introspection — parse run() signature, extract configure() schema."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def introspect_script(script_path: str | Path) -> dict[str, Any]:
    """Parse a user script and extract its interface metadata.

    Analyses the script's AST to discover:
    - ``run()`` function signature (parameter names, annotations, defaults).
    - ``configure()`` return value (if present) — treated as a parameter schema.
    - Top-level docstring.

    Returns a dictionary with keys:
        ``has_run``: bool
        ``run_params``: list of dicts with name, annotation, default
        ``has_configure``: bool
        ``configure_schema``: dict or None
        ``docstring``: str or None
    """
    path = Path(script_path)
    if not path.exists():
        raise FileNotFoundError(f"Script not found: {path}")

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    result: dict[str, Any] = {
        "has_run": False,
        "run_params": [],
        "has_configure": False,
        "configure_schema": None,
        "docstring": ast.get_docstring(tree),
    }

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == "run":
                result["has_run"] = True
                result["run_params"] = _extract_params(node)
            elif node.name == "configure":
                result["has_configure"] = True
                result["configure_schema"] = _extract_configure_return(node, source)

    return result


def _extract_params(func_node: ast.FunctionDef) -> list[dict[str, Any]]:
    """Extract parameter info from a function definition."""
    params: list[dict[str, Any]] = []
    args = func_node.args

    # Combine all positional, keyword args.
    all_args = list(args.args) + list(args.kwonlyargs)
    # Defaults alignment: defaults fill from the right.
    defaults = [None] * (len(args.args) - len(args.defaults)) + list(args.defaults)
    kw_defaults = list(args.kw_defaults)

    for i, arg in enumerate(all_args):
        param: dict[str, Any] = {"name": arg.arg, "annotation": None, "default": None}
        if arg.annotation is not None:
            param["annotation"] = ast.dump(arg.annotation)
        if i < len(args.args):
            if i < len(defaults) and defaults[i] is not None:
                param["default"] = ast.dump(defaults[i])
        else:
            kw_idx = i - len(args.args)
            if kw_idx < len(kw_defaults) and kw_defaults[kw_idx] is not None:
                param["default"] = ast.dump(kw_defaults[kw_idx])
        params.append(param)

    return params


def _extract_configure_return(func_node: ast.FunctionDef, source: str) -> dict[str, Any] | None:
    """Try to extract a static return value from a ``configure()`` function.

    If the function body is a single ``return {literal_dict}``, parse it.
    Otherwise return None (dynamic configure not statically analysable).
    """
    body = func_node.body
    # Skip docstring if present.
    stmts = [s for s in body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    if len(stmts) == 1 and isinstance(stmts[0], ast.Return):
        ret_value = stmts[0].value
        if isinstance(ret_value, ast.Dict):
            try:
                return ast.literal_eval(ret_value)
            except (ValueError, TypeError):
                return None
    return None
