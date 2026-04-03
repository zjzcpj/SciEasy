"""Architecture enforcement: layer dependency rules.

Ensures that lower layers never import from higher layers.  The hierarchy is:

    Layer 1  core/
    Layer 2  blocks/
    Layer 3  engine/
    Layer 4  ai/           (the scieasy.ai services package, NOT blocks/ai/)
    Layer 5  api/

Cross-cutting packages (workflow/, utils/, cli/) are exempt from layer ordering
but core/ still must not import workflow/.

Imports guarded by ``if TYPE_CHECKING:`` are excluded because they have no
runtime effect.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "scieasy"


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------


def _is_type_checking_guard(node: ast.If) -> bool:
    """Return ``True`` when *node* is ``if TYPE_CHECKING:`` or ``if typing.TYPE_CHECKING:``."""
    test = node.test
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"


def _collect_imports(
    nodes: list[ast.stmt],
    imports: list[str],
) -> None:
    """Walk a list of AST statements and collect runtime import strings.

    Imports inside ``if TYPE_CHECKING:`` blocks are skipped entirely.
    """
    for node in nodes:
        # Recurse into if/else but skip TYPE_CHECKING bodies
        if isinstance(node, ast.If):
            if _is_type_checking_guard(node):
                # Skip the body (type-only imports); still check ``else``
                _collect_imports(node.orelse, imports)
                continue
            # Normal if — recurse into both branches
            _collect_imports(node.body, imports)
            _collect_imports(node.orelse, imports)
            continue

        # Recurse into try/except/finally
        if isinstance(node, ast.Try):
            _collect_imports(node.body, imports)
            for handler in node.handlers:
                _collect_imports(handler.body, imports)
            _collect_imports(node.orelse, imports)
            _collect_imports(node.finalbody, imports)
            continue

        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)


def _get_imports_from_file(filepath: Path) -> list[str]:
    """Parse *filepath* and return all runtime-imported module strings."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))
    imports: list[str] = []
    _collect_imports(tree.body, imports)
    return imports


def _collect_py_files(subdir: str) -> list[Path]:
    """Collect all ``.py`` files under ``SRC_ROOT / subdir``."""
    target = SRC_ROOT / subdir
    if not target.exists():
        return []
    return sorted(target.rglob("*.py"))


# ---------------------------------------------------------------------------
# Forbidden-import checker
# ---------------------------------------------------------------------------


def _is_forbidden(imp: str, forbidden_prefix: str) -> bool:
    """Return ``True`` when *imp* matches *forbidden_prefix*.

    Special handling for ``scieasy.ai`` to avoid false positives on
    ``scieasy.blocks.ai`` (which is in the blocks layer, not the AI
    services layer).
    """
    # Exact match (e.g. ``import scieasy.api``)
    if imp == forbidden_prefix:
        return True

    # Prefix match (e.g. ``from scieasy.api.routes import ...``)
    prefix_dot = forbidden_prefix if forbidden_prefix.endswith(".") else forbidden_prefix + "."
    if imp.startswith(prefix_dot):
        # Exclude false positives: ``scieasy.blocks.ai.*`` is NOT the AI
        # services layer ``scieasy.ai.*``.
        return not (forbidden_prefix == "scieasy.ai" and imp.startswith("scieasy.blocks.ai"))

    return False


# ---------------------------------------------------------------------------
# Layer rules
# ---------------------------------------------------------------------------

LAYER_RULES: list[tuple[str, list[str]]] = [
    (
        "core",
        [
            "scieasy.blocks",
            "scieasy.engine",
            "scieasy.api",
            "scieasy.ai",
            "scieasy.workflow",
        ],
    ),
    (
        "blocks",
        [
            "scieasy.engine",
            "scieasy.api",
            "scieasy.ai",
        ],
    ),
    (
        "engine",
        [
            "scieasy.api",
            "scieasy.ai",
        ],
    ),
    (
        "ai",
        [
            "scieasy.api",
        ],
    ),
]


@pytest.mark.parametrize(
    ("layer", "forbidden"),
    LAYER_RULES,
    ids=[rule[0] for rule in LAYER_RULES],
)
def test_layer_does_not_import_forbidden(layer: str, forbidden: list[str]) -> None:
    """Verify that *layer* contains no runtime imports from *forbidden* modules."""
    files = _collect_py_files(layer)
    assert files, f"No .py files found under {SRC_ROOT / layer}"

    violations: list[str] = []
    for filepath in files:
        imports = _get_imports_from_file(filepath)
        for imp in imports:
            for forbidden_prefix in forbidden:
                if _is_forbidden(imp, forbidden_prefix):
                    relative = filepath.relative_to(SRC_ROOT)
                    violations.append(f"  {relative}: imports {imp}")

    assert not violations, f"Layer '{layer}/' has forbidden imports:\n" + "\n".join(violations)


def test_layer_rules_cover_all_source_layers() -> None:
    """Sanity check: every non-cross-cutting source directory appears in at least one rule."""
    checked_layers = {rule[0] for rule in LAYER_RULES}
    expected = {"core", "blocks", "engine", "ai"}
    assert expected.issubset(checked_layers), f"Missing layer rules for: {expected - checked_layers}"
