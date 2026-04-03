# Phase 4: Block System — AI Test Plan

> **Status**: Phase 4 is COMPLETE.
> This document catalogues existing automated tests and specifies additional tests
> for the block system: ports, block categories, registry, adapters, and runners.

---

## 1. Overview

| Component | Source Module | Test File |
|-----------|-------------|-----------|
| Ports | `src/scieasy/blocks/base/ports.py` | `tests/blocks/test_ports.py` |
| IOBlock + Adapters | `src/scieasy/blocks/io/` | `tests/blocks/test_io_block.py` |
| ProcessBlock (Merge/Split) | `src/scieasy/blocks/process/` | `tests/blocks/test_process_block.py` |
| CodeBlock + Runners | `src/scieasy/blocks/code/` | `tests/blocks/test_code_block.py` |
| AppBlock + Watcher | `src/scieasy/blocks/app/` | `tests/blocks/test_app_block.py` |
| SubWorkflowBlock | `src/scieasy/blocks/subworkflow/` | `tests/blocks/test_subworkflow.py` |
| BlockRegistry | `src/scieasy/blocks/registry.py` | `tests/blocks/test_registry.py` |

---

## 2. Existing Tests

### 2.1 `tests/blocks/test_ports.py` (20 tests)

**TestPortAcceptsType** (6 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_exact_match` | Port accepting `Array` accepts `Array` instance |
| 2 | `test_subtype_accepted` | Port accepting `Array` accepts `Image` instance |
| 3 | `test_unrelated_rejected` | Port accepting `Array` rejects `Series` |
| 4 | `test_empty_accepts_anything` | Port with no `accepted_types` accepts all |
| 5 | `test_multiple_accepted_types` | Port accepting `[Array, Series]` accepts both |
| 6 | `test_dataobject_accepts_all` | Port accepting `DataObject` accepts all subtypes |

**TestPortAcceptsSignature** (5 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_exact_signature` | Exact TypeSignature match |
| 2 | `test_subtype_signature` | Subtype signature accepted |
| 3 | `test_incompatible_signature` | Unrelated signature rejected |
| 4 | `test_empty_accepts_all_signatures` | Empty port accepts all signatures |
| 5 | `test_composite_slot_constraint` | Slot constraint validation on CompositeData |

**TestValidatePortConstraint** (4 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_no_constraint_passes` | Port with no constraint always passes |
| 2 | `test_constraint_passes` | Constraint function returning True passes |
| 3 | `test_constraint_fails` | Constraint function returning False fails |
| 4 | `test_constraint_exception` | Constraint raising exception treated as failure |

**TestValidateConnection** (5 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_compatible` | Compatible source→target connection |
| 2 | `test_incompatible` | Incompatible types rejected |
| 3 | `test_empty_source_always_compatible` | Empty source port always connects |
| 4 | `test_empty_target_always_compatible` | Empty target port always connects |
| 5 | `test_subtype_in_multi_type_port` | Subtype connects to multi-type port |

### 2.2 `tests/blocks/test_io_block.py` (6 tests)

**TestIOBlockInput** (3 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_load_csv` | Load CSV file → produces DataFrame |
| 2 | `test_load_parquet` | Load Parquet file → produces DataFrame |
| 3 | `test_missing_path_raises` | Missing file raises FileNotFoundError |

**TestIOBlockOutput** (3 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_save_as_csv` | Save DataFrame → produces CSV file |
| 2 | `test_save_as_parquet` | Save DataFrame → produces Parquet file |

### 2.3 `tests/blocks/test_process_block.py` (8 tests)

**TestMergeBlock** (2 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_concat_two_tables` | Merge two DataFrames → concatenated result |
| 2 | `test_state_transitions` | Block goes IDLE → READY → RUNNING → DONE |

**TestSplitBlock** (6 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_head_mode` | Split head N rows |
| 2 | `test_ratio_mode` | Split by ratio (e.g., 80/20 train/test) |
| 3 | `test_filter_mode` | Split by filter expression |
| 4 | `test_unknown_mode_raises` | Unknown split mode raises ValueError |

### 2.4 `tests/blocks/test_code_block.py` (9 tests)

**TestPythonRunnerInline** (3 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_simple_script` | Execute inline Python, produces output |
| 2 | `test_script_with_inputs` | Inline code receives input variables |
| 3 | `test_private_keys_stripped` | Private keys (starting with `_`) not in namespace |

**TestPythonRunnerScript** (3 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_script_file` | Execute external `.py` file with `run()` function |
| 2 | `test_missing_script` | Missing script raises FileNotFoundError |
| 3 | `test_missing_function` | Script without `run()` raises AttributeError |

**TestCodeBlockInline** (2 tests):
- `test_inline_execution` — Full CodeBlock inline mode
- `test_inline_with_input` — CodeBlock inline with input data

**TestCodeBlockScript** (1 test):
- `test_script_execution` — Full CodeBlock script mode

**TestCodeBlockProxyMode** (1 test):
- `test_proxy_passthrough` — PROXY delivery passes ViewProxy directly

**TestCodeBlockChunkedMode** (1 test):
- `test_chunked_delivery` — CHUNKED delivery iterates chunks

**TestIntrospectScript** (4 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_simple_run_function` | Extracts `run()` signature |
| 2 | `test_configure_function` | Extracts `configure()` return schema |
| 3 | `test_no_run_function` | Script without `run()` raises |
| 4 | `test_missing_file` | Missing file raises FileNotFoundError |

### 2.5 `tests/blocks/test_app_block.py` (7 tests)

**TestFileWatcher** (4 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_detects_new_file` | Watcher detects new file in exchange dir |
| 2 | `test_timeout` | Watcher raises TimeoutError after timeout |
| 3 | `test_pattern_filtering` | Watcher only detects files matching glob |
| 4 | `test_not_started_raises` | Watcher raises if not started |

**TestFileExchangeBridge** (3 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_prepare_creates_manifest` | Bridge creates JSON manifest for inputs |
| 2 | `test_prepare_handles_bytes` | Bridge handles binary data |
| 3 | `test_collect_creates_artifacts` | Bridge collects output files as Artifacts |

### 2.6 `tests/blocks/test_registry.py` (10 tests)

**TestBlockRegistryTier2** (3 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_scan_discovers_entry_points` | Registry finds blocks from `pyproject.toml` entry-points |
| 2 | `test_instantiate_by_name` | `registry.instantiate("io_block")` returns IOBlock |
| 3 | `test_instantiate_unknown_raises` | Unknown block name raises KeyError |

**TestBlockRegistryTier1** (3 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_scan_discovers_dropin` | Registry finds `.py` files in drop-in dirs |
| 2 | `test_hot_reload_picks_up_new_file` | New `.py` file appears after hot_reload |
| 3 | `test_hot_reload_removes_deleted_file` | Deleted `.py` file disappears after hot_reload |

**TestAdapterRegistry** (4 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_register_defaults` | Default adapters registered (csv, parquet, tiff) |
| 2 | `test_get_for_extension` | `.csv` → CSVAdapter, `.parquet` → ParquetAdapter |
| 3 | `test_normalisation` | `.CSV` and `.csv` resolve to same adapter |
| 4 | `test_unknown_extension_raises` | Unknown extension raises KeyError |

### 2.7 `tests/blocks/test_subworkflow.py` (6 tests)

**TestSequentialExecute** (3 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_single_block` | Single block executes correctly |
| 2 | `test_chain_two_blocks` | Output of block A feeds into block B |
| 3 | `test_empty_chain` | Empty chain returns inputs unchanged |

**TestSubWorkflowBlock** (3 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_with_child_blocks` | SubWorkflowBlock executes child blocks |
| 2 | `test_unmapped_passthrough` | Unmapped ports pass through |
| 3 | `test_state_transitions` | Correct state transitions |

---

## 3. Recommended Additional Unit Tests

### File: `tests/blocks/test_ports_extended.py` (NEW)

```python
# Port with deeply nested type hierarchy
def test_deep_subtype_port_matching():
    """RamanSpectrum should match port accepting Series."""
    from scieasy.blocks.base.ports import InputPort
    from scieasy.core.types.series import RamanSpectrum, Series
    port = InputPort(name="input", accepted_types=[Series])
    assert port.accepts_type(RamanSpectrum)

# Connection with constraint function
def test_connection_with_constraint():
    """Connection should validate both type and constraint."""
    from scieasy.blocks.base.ports import InputPort, OutputPort, validate_connection
    from scieasy.core.types.array import Array, Image

    def requires_2d(obj):
        return len(obj.axes) == 2

    out_port = OutputPort(name="out", port_type=Image)
    in_port = InputPort(
        name="in", accepted_types=[Array],
        constraint=requires_2d, constraint_description="Must be 2D"
    )
    result = validate_connection(out_port, in_port)
    assert result.compatible  # Type check passes; constraint checked at runtime

# Port with no types but with constraint
def test_port_constraint_only():
    """Port with constraint but no type restriction."""
    from scieasy.blocks.base.ports import InputPort
    from scieasy.core.types.base import DataObject

    port = InputPort(
        name="any_input", accepted_types=[],
        constraint=lambda obj: hasattr(obj, 'axes'),
        constraint_description="Must have axes"
    )
    # Empty accepted_types means accept anything
    assert port.accepts_type(DataObject)
```

### File: `tests/blocks/test_adapters.py` (NEW)

```python
# TIFF adapter round-trip
def test_tiff_adapter_roundtrip(tmp_path):
    """Write TIFF, read back, verify data matches."""
    import numpy as np
    from scieasy.blocks.io.adapters.tiff_adapter import TIFFAdapter
    adapter = TIFFAdapter()
    data = np.random.randint(0, 255, (256, 256), dtype=np.uint8)
    out_path = tmp_path / "test.tiff"
    adapter.write(data, out_path)
    loaded = adapter.read(out_path)
    # Verify loaded data matches original
    assert loaded is not None

# Stub adapters raise NotImplementedError
@pytest.mark.parametrize("adapter_cls,ext", [
    ("MzXMLAdapter", ".mzxml"),
    ("H5ADAdapter", ".h5ad"),
    ("FCSAdapter", ".fcs"),
])
def test_stub_adapter_raises(adapter_cls, ext):
    """Stub adapters should raise NotImplementedError."""
    import importlib
    mod = importlib.import_module(f"scieasy.blocks.io.adapters.{ext[1:]}_adapter")
    cls = getattr(mod, adapter_cls)
    adapter = cls()
    with pytest.raises(NotImplementedError):
        adapter.read("/fake/path" + ext)

# Generic adapter wraps binary
def test_generic_adapter_creates_artifact(tmp_path):
    """Generic adapter should wrap unknown binary as Artifact."""
    from scieasy.blocks.io.adapters.generic_adapter import GenericAdapter
    adapter = GenericAdapter()
    bin_path = tmp_path / "data.bin"
    bin_path.write_bytes(b"\\x00\\x01\\x02\\x03")
    result = adapter.read(str(bin_path))
    from scieasy.core.types.artifact import Artifact
    assert isinstance(result, Artifact)
```

### File: `tests/blocks/test_code_runners.py` (NEW)

```python
# R runner raises NotImplementedError with helpful message
def test_r_runner_not_implemented():
    from scieasy.blocks.code.runners.r_runner import RRunner
    runner = RRunner()
    with pytest.raises(NotImplementedError, match="R"):
        runner.execute_inline("print('hello')", {})

# Julia runner raises NotImplementedError with helpful message
def test_julia_runner_not_implemented():
    from scieasy.blocks.code.runners.julia_runner import JuliaRunner
    runner = JuliaRunner()
    with pytest.raises(NotImplementedError, match="Julia"):
        runner.execute_inline("println('hello')", {})

# RunnerRegistry discovers runners
def test_runner_registry_defaults():
    from scieasy.blocks.code.runner_registry import RunnerRegistry
    registry = RunnerRegistry()
    registry.register_defaults()
    assert "python" in registry._runners
    assert "r" in registry._runners
    assert "julia" in registry._runners

# PythonRunner with syntax error
def test_python_runner_syntax_error():
    from scieasy.blocks.code.runners.python_runner import PythonRunner
    runner = PythonRunner()
    with pytest.raises(SyntaxError):
        runner.execute_inline("def broken(:", {})

# PythonRunner with runtime error
def test_python_runner_runtime_error():
    from scieasy.blocks.code.runners.python_runner import PythonRunner
    runner = PythonRunner()
    with pytest.raises(Exception):
        runner.execute_inline("x = 1 / 0", {})
```

---

## 4. Integration Tests

### File: `tests/blocks/test_block_pipeline.py` (NEW)

```python
def test_io_to_process_pipeline(tmp_path):
    """IOBlock loads CSV -> MergeBlock merges two DataFrames."""
    # 1. Create two CSV files
    # 2. Load with IOBlock (direction=input)
    # 3. Merge with MergeBlock
    # 4. Verify merged result has rows from both

def test_io_to_code_to_io_pipeline(tmp_path):
    """IOBlock loads CSV -> CodeBlock transforms -> IOBlock saves."""
    # 1. Create CSV
    # 2. Load with IOBlock
    # 3. Transform with CodeBlock inline (e.g., add column)
    # 4. Save with IOBlock (direction=output)
    # 5. Verify saved file

def test_code_block_with_proxy_mode(tmp_path):
    """CodeBlock in PROXY mode receives ViewProxy, not loaded data."""
    # 1. Create Array, store via ZarrBackend
    # 2. Pass ViewProxy to CodeBlock with PROXY delivery
    # 3. Verify CodeBlock received ViewProxy instance

def test_subworkflow_with_real_blocks(tmp_path):
    """SubWorkflowBlock contains IOBlock -> ProcessBlock."""
    # 1. Define child workflow with IOBlock + MergeBlock
    # 2. Execute SubWorkflowBlock
    # 3. Verify output matches expected

def test_registry_to_block_execution():
    """Registry discovers block -> instantiate -> run."""
    from scieasy.blocks.registry import BlockRegistry
    registry = BlockRegistry()
    registry.scan()
    specs = registry.all_specs()
    assert len(specs) > 0

    # Instantiate a known block
    # block = registry.instantiate("process_merge", config={...})
    # result = block.run(inputs={...}, config=block.config)
```

---

## 5. Edge Case / Regression Tests

```python
# Block state transitions — invalid transitions rejected
def test_invalid_state_transition():
    """Block cannot go from IDLE directly to DONE."""
    from scieasy.blocks.base.state import BlockState
    # Verify that the state machine rejects invalid transitions

# IOBlock with empty CSV
def test_io_block_empty_csv(tmp_path):
    """IOBlock should handle empty CSV file gracefully."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("col1,col2\n")
    # Load with IOBlock — should produce DataFrame with 0 rows

# CodeBlock with no outputs
def test_code_block_no_output():
    """CodeBlock inline code that doesn't produce output."""
    # Code: "x = 42" (no assignment to output variables)
    # Should produce empty result or raise

# SplitBlock with ratio > 1.0
def test_split_block_invalid_ratio():
    """SplitBlock ratio > 1.0 should raise ValueError."""
    # config = {"mode": "ratio", "ratio": 1.5}
    # Should raise ValueError

# Hot reload with invalid Python file
def test_hot_reload_invalid_python(tmp_path):
    """Registry hot_reload should skip .py files with syntax errors."""
    # Write invalid .py file to drop-in dir
    # hot_reload should not crash, should skip the file
```

---

## 6. Comprehensive Agent Tests

```bash
# Run all Phase 4 tests
pytest tests/blocks/ -v --cov=scieasy.blocks --cov-report=term-missing

# Run port tests only
pytest tests/blocks/test_ports.py -v

# Run IO block tests only
pytest tests/blocks/test_io_block.py -v

# Run code block tests only
pytest tests/blocks/test_code_block.py -v

# Run registry tests only
pytest tests/blocks/test_registry.py -v

# Run all block tests with architecture tests
pytest tests/blocks/ tests/architecture/ -v --cov=scieasy --cov-report=term-missing

# Full pipeline: lint + typecheck + all tests
make lint && make typecheck && pytest tests/ -v --cov=scieasy --cov-report=term-missing
```

---

## 7. Coverage Targets

| Module | Current Tests | Target |
|--------|--------------|--------|
| `blocks/base/ports.py` | 20 | 25+ |
| `blocks/io/` | 6 | 12+ |
| `blocks/process/` | 8 | 12+ |
| `blocks/code/` | 9 | 15+ |
| `blocks/app/` | 7 | 10+ |
| `blocks/subworkflow/` | 6 | 8+ |
| `blocks/registry.py` | 10 | 12+ |
| **Total Phase 4** | **66** | **95+** |

---

## 8. Fixtures & Helpers

```python
# tests/blocks/conftest.py
import pytest
import pyarrow as pa

@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,value\nA,1\nB,2\nC,3\n")
    return csv_path

@pytest.fixture
def sample_parquet(tmp_path):
    """Create a sample Parquet file for testing."""
    table = pa.table({"name": ["A", "B", "C"], "value": [1, 2, 3]})
    path = tmp_path / "sample.parquet"
    import pyarrow.parquet as pq
    pq.write_table(table, str(path))
    return path

@pytest.fixture
def sample_script(tmp_path):
    """Create a sample Python script with run() function."""
    script = tmp_path / "my_block.py"
    script.write_text('''
def run(inputs, config):
    """Simple pass-through block."""
    return inputs

def configure():
    return {"type": "object", "properties": {}}
''')
    return script

@pytest.fixture
def dropin_dir(tmp_path):
    """Create a drop-in blocks directory with a sample block."""
    blocks_dir = tmp_path / "blocks"
    blocks_dir.mkdir()
    block_file = blocks_dir / "my_custom_block.py"
    block_file.write_text('''
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.core.types.dataframe import DataFrame

class MyCustomBlock(ProcessBlock):
    """A custom drop-in block."""
    name = "my_custom"
    version = "0.1.0"
    algorithm = "custom"
    input_ports = [InputPort(name="data", accepted_types=[DataFrame])]
    output_ports = [OutputPort(name="result", port_type=DataFrame)]

    def run(self, inputs, config):
        return {"result": inputs["data"]}
''')
    return blocks_dir

@pytest.fixture
def block_registry():
    """Pre-scanned BlockRegistry."""
    from scieasy.blocks.registry import BlockRegistry
    registry = BlockRegistry()
    registry.scan()
    return registry
```

---

## 9. How to Run

```bash
# All Phase 4 tests with coverage
pytest tests/blocks/ -v --cov=scieasy.blocks --cov-report=term-missing

# Quick smoke test
pytest tests/blocks/ -x -q

# With verbose output for debugging
pytest tests/blocks/ -v -s --tb=long

# Run specific block type
pytest tests/blocks/test_code_block.py -v -s
```
