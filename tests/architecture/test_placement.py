"""Architecture enforcement: file placement and documentation rules.

Validates that:

* No stray ``.py`` files exist in the package root.
* Every ``.py`` file has a module-level docstring.
* Format adapters (``FormatAdapter`` implementations) are only in
  ``blocks/io/adapters/``.
* Code runners (``CodeRunner`` implementations) are only in
  ``blocks/code/runners/``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "scieasy"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_no_stray_files_in_package_root() -> None:
    """Only ``__init__.py`` should exist directly in ``src/scieasy/``."""
    py_files = sorted(f.name for f in SRC_ROOT.iterdir() if f.is_file() and f.suffix == ".py")
    assert py_files == ["__init__.py"], f"Found unexpected files in package root: {py_files}"


def _all_py_files() -> list[Path]:
    """Return all ``.py`` files under SRC_ROOT, sorted for determinism."""
    return sorted(SRC_ROOT.rglob("*.py"))


@pytest.mark.parametrize(
    "filepath",
    _all_py_files(),
    ids=[str(f.relative_to(SRC_ROOT)) for f in _all_py_files()],
)
def test_every_module_has_docstring(filepath: Path) -> None:
    """Every ``.py`` file must have a module-level docstring."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))
    docstring = ast.get_docstring(tree)
    relative = filepath.relative_to(SRC_ROOT)
    assert docstring is not None, f"{relative} is missing a module-level docstring"


def _find_classes_referencing(base_name: str, search_dir: Path) -> list[tuple[Path, str]]:
    """Find classes that reference *base_name* in their bases, outside *search_dir*.

    We use AST analysis rather than runtime imports so that empty stub
    modules (no class defined yet) do not produce false negatives.
    """
    hits: list[tuple[Path, str]] = []
    for filepath in sorted(SRC_ROOT.rglob("*.py")):
        # Skip the canonical directory
        try:
            filepath.relative_to(search_dir)
            continue
        except ValueError:
            pass

        source = filepath.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for base in node.bases:
                name: str | None = None
                if isinstance(base, ast.Name):
                    name = base.id
                elif isinstance(base, ast.Attribute):
                    name = base.attr
                if name == base_name:
                    hits.append((filepath, node.name))
    return hits


def test_adapters_in_correct_directory() -> None:
    """Classes inheriting from ``FormatAdapter`` should only live in ``blocks/io/adapters/``."""
    canonical = SRC_ROOT / "blocks" / "io" / "adapters"
    misplaced = _find_classes_referencing("FormatAdapter", canonical)
    violations = [f"  {fp.relative_to(SRC_ROOT)}: class {cls_name}" for fp, cls_name in misplaced]
    assert not violations, "FormatAdapter subclasses found outside blocks/io/adapters/:\n" + "\n".join(violations)


def test_runners_in_correct_directory() -> None:
    """Classes inheriting from ``CodeRunner`` should only live in ``blocks/code/runners/``."""
    canonical = SRC_ROOT / "blocks" / "code" / "runners"
    misplaced = _find_classes_referencing("CodeRunner", canonical)
    violations = [f"  {fp.relative_to(SRC_ROOT)}: class {cls_name}" for fp, cls_name in misplaced]
    assert not violations, "CodeRunner subclasses found outside blocks/code/runners/:\n" + "\n".join(violations)


def test_no_py_files_outside_known_packages() -> None:
    """All ``.py`` files should be inside known top-level packages."""
    known_packages = {
        "core",
        "blocks",
        "engine",
        "ai",
        "api",
        "workflow",
        "utils",
        "cli",
        "testing",
    }
    stray: list[str] = []
    for filepath in SRC_ROOT.rglob("*.py"):
        relative = filepath.relative_to(SRC_ROOT)
        parts = relative.parts
        if len(parts) == 1:
            # Root-level files (already checked by test_no_stray_files_in_package_root)
            continue
        top_package = parts[0]
        if top_package not in known_packages:
            stray.append(str(relative))
    assert not stray, f"Found .py files outside known packages: {stray}"


def test_process_contrib_directory_removed() -> None:
    """``blocks/process/contrib/`` must not exist (T-TRK-001).

    Phase 11 abandons the ``contrib`` pattern in favour of the plugin
    package pattern. The four 1-line stub modules and their parent
    directory were deleted by T-TRK-001 (Phase 11 master plan §2.5
    sub-1a). The real ``CellposeSegment`` implementation lives in
    ``packages/scieasy-blocks-imaging/`` per T-IMG-019. This regression
    test prevents the directory from being silently re-introduced.
    """
    contrib_dir = SRC_ROOT / "blocks" / "process" / "contrib"
    assert not contrib_dir.exists(), (
        f"{contrib_dir.relative_to(SRC_ROOT)} must not exist — the contrib "
        "pattern was deleted in T-TRK-001 (Phase 11). Add new process "
        "blocks to scieasy/blocks/process/builtins/ or to a plugin "
        "package under packages/scieasy-blocks-*/."
    )
