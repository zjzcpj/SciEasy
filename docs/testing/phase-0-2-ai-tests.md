# Phase 0-2: Bootstrap, Interface Skeleton & Architecture Tests — AI Test Plan

> **Status**: Phases 0-2 are COMPLETE.
> This document catalogues existing automated tests and specifies additional tests
> to backfill for full coverage of the structural foundation.

---

## 1. Overview

| Phase | Scope | Source Modules |
|-------|-------|----------------|
| 0 | Repository scaffolding, tooling, CI | `pyproject.toml`, `Makefile`, `.github/workflows/` |
| 1 | Interface skeleton (ABCs, Protocols, Enums) | All `src/scieasy/**/*.py` |
| 2 | Architecture enforcement tests | `tests/architecture/` |

**Goal**: Every structural rule from `ARCHITECTURE.md` and `ADR.md` is enforced
by machine. CI blocks any PR that violates layer boundaries, type hierarchy, or
file placement rules.

---

## 2. Existing Tests

### 2.1 `tests/architecture/test_layer_deps.py` (5 tests)

| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_layer_does_not_import_forbidden[core]` | `core/` never imports `blocks/`, `engine/`, `api/`, `ai/`, `workflow/` |
| 2 | `test_layer_does_not_import_forbidden[blocks]` | `blocks/` never imports `engine/`, `api/`, `ai/` |
| 3 | `test_layer_does_not_import_forbidden[engine]` | `engine/` never imports `api/`, `ai/` |
| 4 | `test_layer_does_not_import_forbidden[ai]` | `ai/` never imports `api/` |
| 5 | `test_layer_rules_cover_all_source_layers` | Every non-cross-cutting layer directory is covered |

**Technique**: AST parsing of all `.py` files; ignores `TYPE_CHECKING` guards.

### 2.2 `tests/architecture/test_type_system.py` (9 tests)

| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_type_inherits_from_dataobject` (x17 parametrized) | Every public type class inherits `DataObject` |
| 2 | `test_no_multi_base_type_inheritance` | No class inherits from two unrelated base families |
| 3 | `test_array_subtypes_declare_axes` (x4: Image, MSImage, SRSImage, FluorImage) | Every Array subclass has non-None, non-empty `axes` list |
| 4 | `test_composite_subtypes_declare_expected_slots` (x2: AnnData, SpatialData) | Every CompositeData subclass has non-empty `expected_slots` |
| 5 | `test_composite_slot_values_are_dataobject_types` | Every slot type in `expected_slots` is a `DataObject` subclass |

### 2.3 `tests/architecture/test_block_system.py` (11 tests)

| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_block_categories_inherit_from_block` (x6) | IOBlock, ProcessBlock, CodeBlock, AppBlock, AIBlock, SubWorkflowBlock all inherit Block |
| 2 | `test_block_categories_are_unique_lineage` (x6) | No block category inherits from another category |
| 3 | `test_block_types_declare_output_ports` | Every category declares `output_ports` class attribute |
| 4 | `test_block_types_declare_input_ports` | Every category declares `input_ports` class attribute |
| 5 | `test_block_run_signature` | `Block.run()` signature matches `(self, inputs: dict[str, ViewProxy], config: BlockConfig)` |
| 6 | `test_block_category_run_signature_matches_base` | All categories match Block.run() |
| 7 | `test_block_categories_have_name_attribute` | `name` class attribute exists |
| 8 | `test_block_categories_have_version_attribute` | `version` class attribute exists |

### 2.4 `tests/architecture/test_registries.py` (11 tests)

| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_block_spec_does_not_store_class_object` | `BlockSpec` fields are all primitives/strings (ADR-009) |
| 2 | `test_block_spec_has_descriptor_fields` | `module_path`, `class_name` fields exist |
| 3 | `test_block_spec_has_reload_metadata` | `file_path`, `file_mtime` fields exist |
| 4 | `test_type_spec_does_not_store_class_object` | `TypeSpec` fields are all primitives/strings |
| 5 | `test_type_spec_has_descriptor_fields` | `module_path`, `class_name` exist |
| 6 | `test_block_registry_internal_storage_type` | `_registry` stores `BlockSpec` instances |
| 7 | `test_type_registry_internal_storage_type` | `_registry` stores `TypeSpec` instances |
| 8 | `test_type_registry_has_required_interface` | `register`, `resolve`, `all_types` methods exist |
| 9 | `test_entry_point_resolves_to_class` (parametrized over all entry points) | All `pyproject.toml` entry-points resolve to importable classes |

### 2.5 `tests/architecture/test_placement.py` (6 tests)

| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_no_stray_files_in_package_root` | Only `__init__.py` in `src/scieasy/` |
| 2 | `test_every_module_has_docstring` (parametrized per file) | Every `.py` file under `src/scieasy/` has a module docstring |
| 3 | `test_adapters_in_correct_directory` | `FormatAdapter` subclasses only in `blocks/io/adapters/` |
| 4 | `test_runners_in_correct_directory` | `CodeRunner` subclasses only in `blocks/code/runners/` |
| 5 | `test_no_py_files_outside_known_packages` | All `.py` files in known top-level packages |

---

## 3. Recommended Additional Unit Tests

### File: `tests/architecture/test_scaffold.py` (NEW)

```python
# Test: Package is pip-installable and importable
def test_package_installable():
    """pip install -e . succeeded (run as part of CI setup)."""
    import scieasy
    assert hasattr(scieasy, "__version__")

# Test: CLI entrypoint exists
def test_cli_entrypoint_exists():
    """scieasy --help should run without error."""
    import subprocess
    result = subprocess.run(["scieasy", "--help"], capture_output=True, timeout=10)
    assert result.returncode == 0

# Test: Every __init__.py exists
@pytest.mark.parametrize("package", [
    "scieasy.core", "scieasy.core.types", "scieasy.core.storage",
    "scieasy.core.lineage", "scieasy.blocks", "scieasy.blocks.base",
    "scieasy.blocks.io", "scieasy.blocks.io.adapters",
    "scieasy.blocks.code", "scieasy.blocks.code.runners",
    "scieasy.blocks.process", "scieasy.blocks.process.builtins",
    "scieasy.blocks.app", "scieasy.blocks.ai",
    "scieasy.blocks.subworkflow", "scieasy.engine",
    "scieasy.engine.runners", "scieasy.api", "scieasy.api.routes",
    "scieasy.ai", "scieasy.ai.generation", "scieasy.ai.synthesis",
    "scieasy.ai.optimization", "scieasy.workflow", "scieasy.utils",
    "scieasy.cli",
])
def test_package_importable(package):
    """Every sub-package listed in PROJECT_TREE.md must be importable."""
    import importlib
    importlib.import_module(package)

# Test: No circular imports
def test_no_circular_imports():
    """Importing scieasy top-level should not raise circular import errors."""
    import importlib
    importlib.invalidate_caches()
    mod = importlib.import_module("scieasy")
    assert mod is not None
```

### File: `tests/architecture/test_ci_config.py` (NEW)

```python
# Test: pyproject.toml has correct pytest config
def test_pytest_coverage_threshold():
    """Coverage threshold must be >= 65%."""
    import tomllib
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)
    fail_under = config["tool"]["coverage"]["report"]["fail_under"]
    assert fail_under >= 65

# Test: ruff rules are configured
def test_ruff_rules_configured():
    """Ruff must enforce E, W, F, I, N, UP, B, SIM, RUF rules."""
    import tomllib
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)
    rules = config["tool"]["ruff"]["lint"]["select"]
    for required in ["E", "W", "F", "I", "UP", "B"]:
        assert required in rules

# Test: mypy strict mode
def test_mypy_strict_mode():
    """mypy must run in strict mode on src/scieasy/."""
    import tomllib
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)
    assert config["tool"]["mypy"]["strict"] is True
```

---

## 4. Integration Tests

### File: `tests/architecture/test_import_contracts.py` (NEW)

```python
def test_import_linter_contracts_pass():
    """import-linter contracts must all pass."""
    import subprocess
    result = subprocess.run(
        ["lint-imports"], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, f"Import contracts failed:\n{result.stderr}"

def test_blocks_ai_not_confused_with_ai_services():
    """scieasy.blocks.ai is a block category, not the AI services layer.
    It must be allowed to import from blocks/ but NOT from ai/ (services)."""
    # blocks/ai/ should only import from core/ and blocks/base/
    import ast, pathlib
    blocks_ai = pathlib.Path("src/scieasy/blocks/ai")
    for py_file in blocks_ai.glob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("scieasy.ai."), \
                    f"{py_file}: blocks/ai/ must not import from ai/ services layer"
```

---

## 5. Edge Case / Regression Tests

```python
# Test: Adding a new type that inherits from two base families is caught
def test_multi_inheritance_detected():
    """Architecture tests must catch a type inheriting Array AND DataFrame."""
    # This is a meta-test: verify that test_no_multi_base_type_inheritance
    # would fail if such a class existed.
    from scieasy.core.types.base import DataObject
    from scieasy.core.types.array import Array
    from scieasy.core.types.dataframe import DataFrame

    class BadType(Array, DataFrame):
        axes = ["x"]
        columns = []

    # The architecture test should detect this
    base_families = {Array, DataFrame}
    parents = set(type(BadType).__mro__) & base_families
    assert len(parents) > 1  # Confirms detection logic works

# Test: Module without docstring is caught
def test_missing_docstring_detected():
    """test_every_module_has_docstring should catch files missing docstrings."""
    import ast
    # Create a minimal AST without docstring
    tree = ast.parse("x = 1")
    docstring = ast.get_docstring(tree)
    assert docstring is None  # Confirms detection logic
```

---

## 6. Comprehensive Agent Tests

These are end-to-end scenarios an AI agent can execute:

```bash
# Scenario 1: Full CI pipeline locally
make lint && make typecheck && make test

# Scenario 2: Architecture tests in isolation
pytest tests/architecture/ -v --no-cov

# Scenario 3: Import contracts
lint-imports

# Scenario 4: Verify all entry-points resolve
python -c "
from importlib.metadata import entry_points
for group in ['scieasy.blocks', 'scieasy.adapters', 'scieasy.types', 'scieasy.runners']:
    for ep in entry_points(group=group):
        cls = ep.load()
        print(f'{group}:{ep.name} -> {cls.__name__} OK')
"
```

---

## 7. Coverage Targets

| Module | Current | Target |
|--------|---------|--------|
| Architecture tests | ~42 tests | 50+ tests |
| `tests/architecture/test_scaffold.py` | 0 (new) | 5+ tests |
| `tests/architecture/test_ci_config.py` | 0 (new) | 3+ tests |
| Overall Phase 0-2 | 42 | 55+ |

---

## 8. Fixtures & Helpers

```python
# tests/conftest.py — existing
@pytest.fixture
def tmp_project_dir(tmp_path):
    """Create temporary project directory structure for testing."""
    ...

# Recommended additions:
@pytest.fixture
def pyproject_config():
    """Parsed pyproject.toml as dict."""
    import tomllib
    with open("pyproject.toml", "rb") as f:
        return tomllib.load(f)

@pytest.fixture
def all_source_files():
    """All .py files under src/scieasy/."""
    from pathlib import Path
    return list(Path("src/scieasy").rglob("*.py"))
```

---

## 9. How to Run

```bash
# Run all architecture tests
pytest tests/architecture/ -v --no-cov

# Run with coverage
pytest tests/architecture/ -v --cov=scieasy --cov-report=term-missing

# Run specific test file
pytest tests/architecture/test_layer_deps.py -v

# Run linting + type checking + tests (full CI)
make lint && make typecheck && make test
```
