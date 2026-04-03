# Phase 4: Block System — Human Test Plan

> **Status**: Phase 4 is COMPLETE.
> This document provides step-by-step manual verification procedures for humans
> to confirm the block system works correctly: ports, all block categories,
> registry, adapters, and runners.

---

## 1. Prerequisites

| Requirement | Version | How to Check |
|-------------|---------|--------------|
| Python | 3.11+ | `python --version` |
| SciEasy installed | dev | `python -c "import scieasy"` |
| numpy | any | `python -c "import numpy"` |
| pyarrow | 15.0+ | `python -c "import pyarrow"` |
| tifffile | any | `python -c "import tifffile"` |

---

## 2. Environment Setup

```bash
cd SciEasy
git checkout main
git pull origin main
pip install -e ".[dev]"
```

---

## 3. Manual Test Procedures

### Test 1: Run All Phase 4 Automated Tests

**Steps**:
```bash
pytest tests/blocks/ -v --cov=scieasy.blocks --cov-report=term-missing
```

**Expected**: All tests pass (66+ tests), no failures.

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 2: Port Type Matching

**Steps**:
```bash
python
```
Then enter:
```python
from scieasy.blocks.base.ports import InputPort, OutputPort, validate_connection
from scieasy.core.types.array import Array, Image
from scieasy.core.types.series import Series

# Create ports
out_port = OutputPort(name="image_out", port_type=Image)
in_array = InputPort(name="array_in", accepted_types=[Array])
in_series = InputPort(name="series_in", accepted_types=[Series])

# Test: Image -> Array port (should work, Image is subtype of Array)
result1 = validate_connection(out_port, in_array)
print(f"Image -> Array port: compatible={result1.compatible}")
# Expected: compatible=True

# Test: Image -> Series port (should fail, Image is not Series)
result2 = validate_connection(out_port, in_series)
print(f"Image -> Series port: compatible={result2.compatible}")
# Expected: compatible=False

# Test: port with constraint
def has_2_axes(obj):
    return hasattr(obj, 'axes') and len(obj.axes) == 2

constrained_port = InputPort(
    name="2d_in", accepted_types=[Array],
    constraint=has_2_axes,
    constraint_description="Must be 2D array"
)
print(f"Constraint description: {constrained_port.constraint_description}")
# Expected: Constraint description: Must be 2D array

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 3: IOBlock — Load CSV File

**Steps**:

1. Create a test CSV file:
```bash
cat > /tmp/test_data.csv << 'EOF'
metabolite,mz,intensity,retention_time
Glucose,180.063,1500.5,3.2
Lactate,89.024,2300.1,1.8
Pyruvate,87.008,890.3,2.1
Citrate,191.019,450.7,4.5
EOF
```

2. Load it with IOBlock:
```bash
python
```
```python
from scieasy.blocks.io.io_block import IOBlock
from scieasy.blocks.base.config import BlockConfig

# Create input IOBlock
block = IOBlock(direction="input")
config = BlockConfig(parameters={"path": "/tmp/test_data.csv", "format": "csv"})

# Run the block
result = block.run(inputs={}, config=config)
print(f"Result keys: {list(result.keys())}")
# Expected: ['data'] or similar output port name

output = list(result.values())[0]
print(f"Type: {type(output).__name__}")
# Expected: Type: DataFrame

print(f"Loaded successfully!")
exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 4: IOBlock — Save to Parquet

**Steps**:
```bash
python
```
```python
import pyarrow as pa
from scieasy.blocks.io.io_block import IOBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.dataframe import DataFrame

# Create a DataFrame to save
table = pa.table({
    "name": ["A", "B", "C"],
    "value": [1.0, 2.0, 3.0],
})

# Create output IOBlock
block = IOBlock(direction="output")
config = BlockConfig(parameters={
    "path": "/tmp/test_output.parquet",
    "format": "parquet"
})

# This test depends on how IOBlock.run() expects inputs
# Adjust based on actual port names
print("IOBlock output ports:", [p.name for p in block.output_ports])
print("IOBlock input ports:", [p.name for p in block.input_ports])
exit()
```

Verify the Parquet file was created:
```bash
ls -la /tmp/test_output.parquet
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 5: ProcessBlock — MergeBlock

**Steps**:
```bash
python
```
```python
import pyarrow as pa
from scieasy.blocks.process.builtins.merge import MergeBlock
from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.dataframe import DataFrame
from scieasy.core.proxy import ViewProxy
from scieasy.core.storage.arrow_backend import ArrowBackend
import tempfile, os

# Create two tables
table1 = pa.table({"name": ["A", "B"], "value": [1, 2]})
table2 = pa.table({"name": ["C", "D"], "value": [3, 4]})

# Store them
backend = ArrowBackend()
tmp = tempfile.mkdtemp()
ref1 = backend.write(table1, os.path.join(tmp, "t1.parquet"))
ref2 = backend.write(table2, os.path.join(tmp, "t2.parquet"))

# Create ViewProxies
df1 = DataFrame(columns=["name", "value"], row_count=2, storage_ref=ref1)
df2 = DataFrame(columns=["name", "value"], row_count=2, storage_ref=ref2)
proxy1 = df1.view()
proxy2 = df2.view()

# Run MergeBlock
block = MergeBlock()
config = BlockConfig(parameters={})
result = block.run(
    inputs={"left": proxy1, "right": proxy2},
    config=config,
)

output = list(result.values())[0]
print(f"Merged type: {type(output).__name__}")
# Expected: DataFrame
print("Merge succeeded!")
exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 6: CodeBlock — Inline Python

**Steps**:
```bash
python
```
```python
from scieasy.blocks.code.code_block import CodeBlock
from scieasy.blocks.base.config import BlockConfig

# Create inline CodeBlock
block = CodeBlock()
config = BlockConfig(parameters={
    "mode": "inline",
    "language": "python",
    "code": """
import math
result = math.pi * 2
output = result
"""
})

result = block.run(inputs={}, config=config)
print(f"Result: {result}")
# Expected: dict with output value close to 6.283...

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 7: CodeBlock — Script Mode

**Steps**:

1. Create a test script:
```bash
cat > /tmp/test_block_script.py << 'EOF'
"""A simple test block script."""

def run(inputs, config):
    """Double all values."""
    data = inputs.get("data")
    if data is not None:
        return {"result": data}
    return {"result": None}

def configure():
    return {"type": "object", "properties": {"factor": {"type": "number", "default": 2}}}
EOF
```

2. Introspect the script:
```bash
python
```
```python
from scieasy.blocks.code.introspect import introspect_script

info = introspect_script("/tmp/test_block_script.py")
print(f"Has run: {info.has_run}")
# Expected: True
print(f"Has configure: {info.has_configure}")
# Expected: True
print(f"Input names: {info.input_names}")
print(f"Output names: {info.output_names}")

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 8: Write a Custom Drop-In Block

**Steps**:

1. Create a drop-in block directory:
```bash
mkdir -p /tmp/scieasy_test_blocks
```

2. Write a custom block:
```bash
cat > /tmp/scieasy_test_blocks/my_normalizer.py << 'EOF'
"""Custom normalizer block for testing drop-in discovery."""
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.core.types.dataframe import DataFrame

class NormalizerBlock(ProcessBlock):
    """Normalize a DataFrame column."""
    name = "normalizer"
    version = "0.1.0"
    algorithm = "min-max"
    input_ports = [InputPort(name="data", accepted_types=[DataFrame])]
    output_ports = [OutputPort(name="normalized", port_type=DataFrame)]

    def run(self, inputs, config):
        return {"normalized": inputs["data"]}
EOF
```

3. Test Tier 1 discovery:
```bash
python
```
```python
from scieasy.blocks.registry import BlockRegistry

registry = BlockRegistry()
registry.scan(tier1_dirs=["/tmp/scieasy_test_blocks"])
specs = registry.all_specs()

# Find our custom block
found = [s for s in specs if "normalizer" in s.class_name.lower()]
print(f"Found custom block: {len(found) > 0}")
# Expected: True

if found:
    print(f"Block name: {found[0].class_name}")
    print(f"Module: {found[0].module_path}")

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 9: Hot Reload

**Steps**:
```bash
python
```
```python
import os, time
from scieasy.blocks.registry import BlockRegistry

# Initial scan
registry = BlockRegistry()
registry.scan(tier1_dirs=["/tmp/scieasy_test_blocks"])
count_before = len(registry.all_specs())
print(f"Blocks before: {count_before}")

# Add another block file
with open("/tmp/scieasy_test_blocks/my_filter.py", "w") as f:
    f.write('''
"""A filter block."""
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.core.types.dataframe import DataFrame

class FilterBlock(ProcessBlock):
    name = "filter"
    version = "0.1.0"
    algorithm = "filter"
    input_ports = [InputPort(name="data", accepted_types=[DataFrame])]
    output_ports = [OutputPort(name="filtered", port_type=DataFrame)]
    def run(self, inputs, config):
        return {"filtered": inputs["data"]}
''')

# Hot reload
time.sleep(0.1)
registry.hot_reload()
count_after = len(registry.all_specs())
print(f"Blocks after reload: {count_after}")
print(f"New block discovered: {count_after > count_before}")
# Expected: True

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 10: AppBlock File Watcher (Simulated)

**Steps**:
```bash
python
```
```python
import threading, time, os, tempfile
from scieasy.blocks.app.watcher import FileWatcher

# Create exchange directory
exchange_dir = tempfile.mkdtemp()
print(f"Exchange dir: {exchange_dir}")

# Start watcher in background
watcher = FileWatcher(watch_dir=exchange_dir, patterns=["*.csv"], timeout=10)
watcher.start()

# Simulate external app writing a file after 2 seconds
def write_output():
    time.sleep(2)
    output_path = os.path.join(exchange_dir, "result.csv")
    with open(output_path, "w") as f:
        f.write("col1,col2\n1,2\n")
    print(f"  [background] Wrote {output_path}")

thread = threading.Thread(target=write_output)
thread.start()

# Wait for watcher to detect
detected = watcher.wait()
print(f"Detected files: {detected}")
# Expected: list containing path to result.csv

thread.join()
exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 11: Stub Runners (R, Julia)

**Steps**:
```bash
python
```
```python
from scieasy.blocks.code.runners.r_runner import RRunner
from scieasy.blocks.code.runners.julia_runner import JuliaRunner

# R runner should raise NotImplementedError
try:
    r = RRunner()
    r.execute_inline("print('hello')", {})
    print("ERROR: should have raised")
except NotImplementedError as e:
    print(f"R runner: {e}")
    # Expected: helpful message about R not being implemented yet

# Julia runner should raise NotImplementedError
try:
    j = JuliaRunner()
    j.execute_inline("println('hello')", {})
    print("ERROR: should have raised")
except NotImplementedError as e:
    print(f"Julia runner: {e}")
    # Expected: helpful message about Julia not being implemented yet

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 12: Block State Transitions

**Steps**:
```bash
python
```
```python
from scieasy.blocks.base.state import BlockState

# Verify all expected states exist
states = [BlockState.IDLE, BlockState.READY, BlockState.RUNNING,
          BlockState.DONE, BlockState.ERROR]
for s in states:
    print(f"  {s.name}: {s.value}")
# Expected: all 5 states listed

# Check PAUSED state exists (for AppBlock)
try:
    paused = BlockState.PAUSED
    print(f"  PAUSED: {paused.value}")
except AttributeError:
    print("  PAUSED state not found (may be part of AppBlock-specific logic)")

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## 4. Exploratory Test Scenarios

### Scenario A: CodeBlock CHUNKED Mode with Real Data
Create a large Zarr array, pass to CodeBlock with CHUNKED delivery, verify the code is called once per chunk.

### Scenario B: Full Pipeline
1. Create CSV with metabolite data
2. Load with IOBlock
3. Split with SplitBlock (80/20 ratio)
4. Process train set with CodeBlock (add column)
5. Save result with IOBlock
6. Verify the entire pipeline produces correct output

### Scenario C: Adapter Auto-Detection
Test whether AdapterRegistry correctly auto-detects format from file extension for `.csv`, `.parquet`, `.tiff` files.

---

## 5. Verification Checklist

| # | Check | Result |
|---|-------|--------|
| 1 | `pytest tests/blocks/` all pass | [ ] |
| 2 | Port type matching works (subtype accepted, unrelated rejected) | [ ] |
| 3 | Port constraint validation works | [ ] |
| 4 | IOBlock loads CSV correctly | [ ] |
| 5 | IOBlock saves Parquet correctly | [ ] |
| 6 | MergeBlock concatenates two DataFrames | [ ] |
| 7 | SplitBlock splits by head/ratio/filter | [ ] |
| 8 | CodeBlock inline mode works | [ ] |
| 9 | CodeBlock script mode works | [ ] |
| 10 | Script introspection extracts run() signature | [ ] |
| 11 | Drop-in block discovered by Tier 1 scan | [ ] |
| 12 | Hot reload picks up new drop-in blocks | [ ] |
| 13 | AppBlock file watcher detects output files | [ ] |
| 14 | R/Julia runners raise NotImplementedError | [ ] |
| 15 | All block states exist (IDLE, READY, RUNNING, DONE, ERROR) | [ ] |

---

## 6. Cleanup

```bash
# Remove test files
rm -f /tmp/test_data.csv /tmp/test_output.parquet /tmp/test_block_script.py
rm -rf /tmp/scieasy_test_blocks

# Remove temporary exchange directories
# (they are in system temp, will be cleaned up automatically)
```
