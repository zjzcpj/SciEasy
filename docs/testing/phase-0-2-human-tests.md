# Phase 0-2: Bootstrap, Interface Skeleton & Architecture Tests — Human Test Plan

> **Status**: Phases 0-2 are COMPLETE.
> This document provides step-by-step manual verification procedures for humans
> to confirm the project foundation is correctly set up.

---

## 1. Prerequisites

| Requirement | Version | How to Check |
|-------------|---------|--------------|
| Python | 3.11, 3.12, or 3.13 | `python --version` |
| pip | Latest | `pip --version` |
| Git | 2.30+ | `git --version` |
| Make | Any | `make --version` |
| GitHub CLI (optional) | 2.0+ | `gh --version` |

---

## 2. Environment Setup

### 2.1 Clone the Repository

```bash
git clone https://github.com/zjzcpj/SciEasy.git
cd SciEasy
```

**Expected**: Directory created, all files present.

### 2.2 Install the Package

```bash
pip install -e ".[dev]"
```

**Expected**: No errors. Output ends with `Successfully installed scieasy-0.1.0.dev0` (or similar).

### 2.3 Verify Installation

```bash
python -c "import scieasy; print(scieasy.__version__)"
```

**Expected**: Prints version string like `0.1.0.dev0`.

```bash
scieasy --help
```

**Expected**: Shows CLI help with subcommands: `serve`, `run`, `validate`, `init`, `blocks`.

---

## 3. Manual Test Procedures

### Test 1: Linting

**Steps**:
```bash
make lint
```

**Expected output**: No errors. Ruff check and format both pass. Output similar to:
```
All checks passed!
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 2: Type Checking

**Steps**:
```bash
make typecheck
```

**Expected output**: mypy passes with no errors. Output similar to:
```
Success: no issues found in N source files
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 3: Run All Tests

**Steps**:
```bash
make test
```

**Expected output**:
- All tests pass (no `FAILED` lines)
- Coverage is >= 65%
- Output includes `XX passed` with no failures

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 4: Architecture Tests Specifically

**Steps**:
```bash
pytest tests/architecture/ -v --no-cov
```

**Expected output**: All architecture tests pass. You should see test names like:
- `test_layer_does_not_import_forbidden[core]` PASSED
- `test_type_inherits_from_dataobject[Image]` PASSED
- `test_block_categories_inherit_from_block[IOBlock]` PASSED
- etc.

**Count**: Approximately 42 tests should pass.

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 5: Import Contracts

**Steps**:
```bash
lint-imports
```

**Expected output**: All import contracts pass. No violations reported.

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 6: Entry-Point Resolution

**Steps**:
```bash
python -c "
from importlib.metadata import entry_points
for group in ['scieasy.blocks', 'scieasy.adapters', 'scieasy.types', 'scieasy.runners']:
    eps = entry_points(group=group)
    for ep in eps:
        try:
            cls = ep.load()
            print(f'  OK: {group}:{ep.name} -> {cls.__name__}')
        except Exception as e:
            print(f'  FAIL: {group}:{ep.name} -> {e}')
"
```

**Expected output**: All entry-points resolve. No `FAIL` lines. You should see:
```
  OK: scieasy.blocks:io_block -> IOBlock
  OK: scieasy.blocks:process_merge -> MergeBlock
  OK: scieasy.blocks:code_block -> CodeBlock
  OK: scieasy.adapters:csv -> CSVAdapter
  OK: scieasy.types:image -> Image
  OK: scieasy.runners:python -> PythonRunner
  ...
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 7: Intentional Architecture Violation (Negative Test)

**Purpose**: Confirm the architecture tests catch violations.

**Steps**:
1. Open `src/scieasy/core/types/base.py` in a text editor
2. Add this line at the top (after existing imports):
   ```python
   from scieasy.blocks.base.block import Block  # intentional violation
   ```
3. Run:
   ```bash
   pytest tests/architecture/test_layer_deps.py -v --no-cov
   ```
4. **Expected**: `test_layer_does_not_import_forbidden[core]` FAILS
5. **Revert** the change:
   ```bash
   git checkout src/scieasy/core/types/base.py
   ```

**Verdict**: [ ] PASS (test correctly caught violation) / [ ] FAIL (violation not detected)

---

### Test 8: Verify Project Directory Structure

**Steps**:
```bash
# Check key directories exist
ls src/scieasy/core/types/
ls src/scieasy/core/storage/
ls src/scieasy/core/lineage/
ls src/scieasy/blocks/base/
ls src/scieasy/blocks/io/adapters/
ls src/scieasy/blocks/code/runners/
ls src/scieasy/blocks/process/builtins/
ls src/scieasy/blocks/app/
ls src/scieasy/blocks/ai/
ls src/scieasy/blocks/subworkflow/
ls src/scieasy/engine/runners/
ls src/scieasy/api/routes/
ls src/scieasy/ai/generation/
ls src/scieasy/ai/synthesis/
ls src/scieasy/ai/optimization/
ls src/scieasy/workflow/
ls src/scieasy/utils/
ls src/scieasy/cli/
```

**Expected**: Each directory lists `.py` files including `__init__.py`.

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 9: Pre-Commit Hooks

**Steps**:
```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks on staged files
pre-commit run --all-files
```

**Expected output**: All hooks pass (trailing whitespace, end-of-file, ruff, mypy, etc.)

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 10: CI Pipeline (GitHub)

**Steps**:
1. Go to the repository on GitHub: `https://github.com/zjzcpj/SciEasy`
2. Click on the **Actions** tab
3. Find the latest CI run on the `main` branch
4. Verify all jobs passed:
   - [ ] Lint & Format
   - [ ] Type Check
   - [ ] Architecture Tests
   - [ ] Test (Python 3.11)
   - [ ] Test (Python 3.12)
   - [ ] Test (Python 3.13)
   - [ ] Import Contracts

**Verdict**: [ ] PASS / [ ] FAIL

---

## 4. Exploratory Test Scenarios

### Scenario A: Fresh Environment
Try installing SciEasy in a brand-new virtual environment:
```bash
python -m venv /tmp/scieasy-test
source /tmp/scieasy-test/bin/activate  # Linux/Mac
# or: /tmp/scieasy-test/Scripts/activate  # Windows
pip install -e ".[dev]"
make test
deactivate
```
Does everything work from scratch?

### Scenario B: Different Python Version
If you have multiple Python versions, test with each:
```bash
python3.11 -m venv /tmp/test311 && source /tmp/test311/bin/activate && pip install -e ".[dev]" && make test
python3.12 -m venv /tmp/test312 && source /tmp/test312/bin/activate && pip install -e ".[dev]" && make test
python3.13 -m venv /tmp/test313 && source /tmp/test313/bin/activate && pip install -e ".[dev]" && make test
```

---

## 5. Verification Checklist

| # | Check | Result |
|---|-------|--------|
| 1 | `pip install -e ".[dev]"` succeeds | [ ] |
| 2 | `import scieasy` works | [ ] |
| 3 | `scieasy --help` shows CLI | [ ] |
| 4 | `make lint` passes | [ ] |
| 5 | `make typecheck` passes | [ ] |
| 6 | `make test` passes with >= 65% coverage | [ ] |
| 7 | Architecture tests all pass | [ ] |
| 8 | Import contracts pass | [ ] |
| 9 | All entry-points resolve | [ ] |
| 10 | Architecture violation is detected | [ ] |
| 11 | Directory structure is complete | [ ] |
| 12 | Pre-commit hooks pass | [ ] |
| 13 | GitHub CI is green | [ ] |

---

## 6. Cleanup

```bash
# Remove test virtual environments
rm -rf /tmp/scieasy-test /tmp/test311 /tmp/test312 /tmp/test313

# Revert any intentional violations
git checkout .
```
