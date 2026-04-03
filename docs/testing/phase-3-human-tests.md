# Phase 3: Core Data Layer — Human Test Plan

> **Status**: Phase 3 is COMPLETE.
> This document provides step-by-step manual verification procedures for humans
> to confirm the core data layer works correctly: types, storage, proxy, lineage,
> and broadcast.

---

## 1. Prerequisites

| Requirement | Version | How to Check |
|-------------|---------|--------------|
| Python | 3.11+ | `python --version` |
| SciEasy installed | dev | `python -c "import scieasy"` |
| numpy | any | `python -c "import numpy"` |
| pyarrow | 15.0+ | `python -c "import pyarrow; print(pyarrow.__version__)"` |
| zarr | 3.0+ | `python -c "import zarr; print(zarr.__version__)"` |

---

## 2. Environment Setup

```bash
cd SciEasy
git checkout main
git pull origin main
pip install -e ".[dev]"
```

**Expected**: No errors. Package installs with all dependencies.

---

## 3. Manual Test Procedures

### Test 1: Run All Phase 3 Automated Tests

**Steps**:
```bash
pytest tests/core/ -v --cov=scieasy.core --cov-report=term-missing
```

**Expected output**:
- All tests pass (86+ tests)
- Coverage for `scieasy.core` modules is visible
- No `FAILED` or `ERROR` lines

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 2: Create and Inspect DataObject Types (Python REPL)

**Steps**:
```bash
python
```
Then enter:
```python
from scieasy.core.types.array import Array, Image, MSImage
from scieasy.core.types.series import Series, Spectrum
from scieasy.core.types.dataframe import DataFrame, PeakTable
from scieasy.core.types.text import Text
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.composite import CompositeData, AnnData

# Create instances
img = Image(axes=["y", "x"])
print(f"Image axes: {img.axes}")
# Expected: Image axes: ['y', 'x']

spec = Spectrum()
print(f"Spectrum type: {type(spec).__name__}")
# Expected: Spectrum type: Spectrum

pt = PeakTable(columns=["mz", "intensity"], row_count=0)
print(f"PeakTable columns: {pt.columns}")
# Expected: PeakTable columns: ['mz', 'intensity']

txt = Text(content="hello world", format="plain")
print(f"Text content: {txt.content}")
# Expected: Text content: hello world

art = Artifact(file_path="/tmp/report.pdf", mime_type="application/pdf")
print(f"Artifact mime: {art.mime_type}")
# Expected: Artifact mime: application/pdf

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 3: TypeSignature and Inheritance Matching

**Steps**:
```bash
python
```
Then enter:
```python
from scieasy.core.types.base import TypeSignature
from scieasy.core.types.array import Image, Array
from scieasy.core.types.series import Spectrum, Series

# Generate TypeSignature
sig = TypeSignature.from_type(Image)
print(f"Image chain: {sig.chain}")
# Expected: ['Image', 'Array', 'DataObject'] (or similar)

# Test matching
print(f"Image matches Array: {sig.matches(TypeSignature.from_type(Array))}")
# Expected: True

print(f"Array matches Image: {TypeSignature.from_type(Array).matches(sig)}")
# Expected: False

print(f"Image matches Spectrum: {sig.matches(TypeSignature.from_type(Spectrum))}")
# Expected: False

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 4: Zarr Storage Backend Round-Trip

**Steps**:
```bash
python
```
Then enter:
```python
import numpy as np
import tempfile, os
from scieasy.core.storage.zarr_backend import ZarrBackend

# Create test data
data = np.random.rand(512, 512).astype(np.float32)
print(f"Original shape: {data.shape}, dtype: {data.dtype}")
# Expected: Original shape: (512, 512), dtype: float32

# Write to Zarr
backend = ZarrBackend()
tmp_dir = tempfile.mkdtemp()
zarr_path = os.path.join(tmp_dir, "test.zarr")
ref = backend.write(data, zarr_path)
print(f"Storage ref: {ref}")
# Expected: StorageReference with path to test.zarr

# Read back
loaded = backend.read(ref)
print(f"Loaded shape: {loaded.shape}, dtype: {loaded.dtype}")
# Expected: Loaded shape: (512, 512), dtype: float32

# Verify data matches
print(f"Data matches: {np.allclose(data, loaded)}")
# Expected: Data matches: True

# Slice a region
chunk = backend.slice(ref, {"0": slice(0, 100), "1": slice(0, 100)})
print(f"Slice shape: {chunk.shape}")
# Expected: Slice shape: (100, 100)

print(f"Slice matches: {np.allclose(data[:100, :100], chunk)}")
# Expected: Slice matches: True

# Get metadata
meta = backend.get_metadata(ref)
print(f"Metadata: {meta}")
# Expected: dict with shape, dtype, chunks keys

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 5: Arrow/Parquet Storage Backend Round-Trip

**Steps**:
```bash
python
```
Then enter:
```python
import pyarrow as pa
import tempfile, os
from scieasy.core.storage.arrow_backend import ArrowBackend

# Create test table
table = pa.table({
    "name": ["Glucose", "Lactate", "Pyruvate"],
    "mz": [180.063, 89.024, 87.008],
    "intensity": [1000.0, 500.0, 250.0],
})
print(f"Original: {table.num_rows} rows, {table.num_columns} cols")
# Expected: Original: 3 rows, 3 cols

# Write to Parquet
backend = ArrowBackend()
tmp_dir = tempfile.mkdtemp()
parquet_path = os.path.join(tmp_dir, "peaks.parquet")
ref = backend.write(table, parquet_path)

# Read back
loaded = backend.read(ref)
print(f"Loaded: {loaded.num_rows} rows, {loaded.num_columns} cols")
# Expected: Loaded: 3 rows, 3 cols
print(f"Column names: {loaded.column_names}")
# Expected: Column names: ['name', 'mz', 'intensity']

# Verify values
print(f"First name: {loaded.column('name')[0].as_py()}")
# Expected: First name: Glucose

# Column selection
subset = backend.slice(ref, {"columns": ["name", "mz"]})
print(f"Subset columns: {subset.column_names}")
# Expected: Subset columns: ['name', 'mz']

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 6: ViewProxy Lazy Loading

**Steps**:
```bash
python
```
Then enter:
```python
import numpy as np
import tempfile, os
from scieasy.core.types.array import Image
from scieasy.core.storage.zarr_backend import ZarrBackend

# Create and store image data
data = np.random.rand(1024, 1024).astype(np.float32)
backend = ZarrBackend()
tmp_dir = tempfile.mkdtemp()
ref = backend.write(data, os.path.join(tmp_dir, "big_image.zarr"))

# Create Image with storage reference
img = Image(axes=["y", "x"], storage_ref=ref)

# Get ViewProxy — should NOT load data
proxy = img.view()
print(f"Shape (no data loaded): {proxy.shape}")
# Expected: Shape (no data loaded): (1024, 1024)

print(f"Axes: {proxy.axes}")
# Expected: Axes: ['y', 'x']

# Slice — should only load requested region
chunk = proxy.slice({"y": slice(0, 100)})
print(f"Slice shape: {chunk.shape}")
# Expected: Slice shape: (100, 1024)

# Iterate chunks
chunk_count = 0
for c in proxy.iter_chunks(chunk_size=256):
    chunk_count += 1
print(f"Number of chunks: {chunk_count}")
# Expected: Number of chunks: 4 (or similar, depends on chunking)

# Full load
full = proxy.to_memory()
print(f"Full shape: {full.shape}")
# Expected: Full shape: (1024, 1024)
print(f"Full matches original: {np.allclose(data, full)}")
# Expected: Full matches original: True

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 7: CompositeData / AnnData Slot Management

**Steps**:
```bash
python
```
Then enter:
```python
from scieasy.core.types.composite import AnnData
from scieasy.core.types.array import Array, Image
from scieasy.core.types.dataframe import DataFrame
from scieasy.core.types.text import Text

# Create AnnData
ad = AnnData()
print(f"Expected slots: {ad.expected_slots}")
# Expected: dict with X, obs, var, obsm keys

# Set valid slots
x_data = Array(axes=["obs", "var"])
obs_data = DataFrame(columns=["cell_type"], row_count=100)
ad.set("X", x_data)
ad.set("obs", obs_data)
print(f"Slot names: {ad.slot_names()}")
# Expected: ['X', 'obs'] (or similar)

# Set subtype — should work (Image is subtype of Array)
img = Image(axes=["y", "x"])
ad.set("X", img)
print("Set Image in X slot: OK")
# Expected: no error

# Set invalid type — should raise
try:
    ad.set("X", Text(content="bad"))
    print("ERROR: should have raised TypeError")
except TypeError as e:
    print(f"Correctly rejected: {e}")
# Expected: Correctly rejected: ... (error message about type mismatch)

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 8: Lineage Store and Provenance

**Steps**:
```bash
python
```
Then enter:
```python
import tempfile, os
from scieasy.core.lineage.store import LineageStore
from scieasy.core.lineage.record import LineageRecord
from scieasy.core.lineage.environment import EnvironmentSnapshot

# Capture environment
env = EnvironmentSnapshot.capture()
print(f"Python version: {env.python_version}")
print(f"Platform: {env.platform}")
# Expected: current Python version and OS platform

# Create lineage store
tmp_dir = tempfile.mkdtemp()
store = LineageStore(os.path.join(tmp_dir, "lineage.db"))

# Write a lineage record
record = LineageRecord(
    input_hashes=["hash_input_1"],
    block_id="my_process_block",
    block_config={"window_size": 11},
    block_version="1.0.0",
    output_hashes=["hash_output_1"],
    environment=env,
)
store.write(record)
print("Wrote lineage record: OK")

# Query by output hash
results = store.query("hash_output_1")
print(f"Query results: {len(results)} record(s)")
# Expected: Query results: 1 record(s)
print(f"Block ID: {results[0].block_id}")
# Expected: Block ID: my_process_block

# Write a chain: A -> B -> C
record2 = LineageRecord(
    input_hashes=["hash_output_1"],
    block_id="second_block",
    block_config={},
    block_version="1.0.0",
    output_hashes=["hash_output_2"],
)
store.write(record2)

# Trace ancestors
ancestors = store.ancestors("hash_output_2")
print(f"Ancestors of output_2: {len(ancestors)} record(s)")
# Expected: Ancestors of output_2: 2 record(s)

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 9: Broadcast Apply

**Steps**:
```bash
python
```
Then enter:
```python
import numpy as np
from scieasy.utils.broadcast import broadcast_apply, iter_axis_slices
from scieasy.core.types.array import Array

# Create 3D cube and 2D mask
cube_data = np.ones((10, 100, 100), dtype=np.float32)
mask_data = np.zeros((100, 100), dtype=np.float32)
mask_data[25:75, 25:75] = 1.0  # center square

cube = Array(axes=["z", "y", "x"])
mask = Array(axes=["y", "x"])

# Iterate axis slices
slice_count = 0
for s in iter_axis_slices(cube_data, axes=["z", "y", "x"], over="z"):
    slice_count += 1
print(f"Slices along z: {slice_count}")
# Expected: Slices along z: 10

# Apply broadcast
result = broadcast_apply(
    func=lambda target_slice, source: target_slice * source,
    target_data=cube_data,
    target_axes=["z", "y", "x"],
    source_data=mask_data,
    source_axes=["y", "x"],
    over_axes=["z"],
)
print(f"Result shape: {result.shape}")
# Expected: Result shape: (10, 100, 100)
print(f"Center value: {result[0, 50, 50]}")
# Expected: Center value: 1.0
print(f"Corner value: {result[0, 0, 0]}")
# Expected: Corner value: 0.0

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 10: Content Hashing

**Steps**:
```bash
python
```
Then enter:
```python
from scieasy.utils.hashing import content_hash

# Hash some data
h1 = content_hash(b"hello world")
h2 = content_hash(b"hello world")
h3 = content_hash(b"different data")

print(f"Hash 1: {h1}")
print(f"Hash 2: {h2}")
print(f"Hash 3: {h3}")
print(f"Same data = same hash: {h1 == h2}")
# Expected: True
print(f"Different data = different hash: {h1 != h3}")
# Expected: True

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## 4. Exploratory Test Scenarios

### Scenario A: Large Data Handling
Create a very large array (e.g., 10000x10000) and verify lazy loading doesn't consume memory:
```python
import numpy as np, tempfile, os, psutil
from scieasy.core.storage.zarr_backend import ZarrBackend

data = np.random.rand(10000, 10000).astype(np.float32)  # ~400 MB
backend = ZarrBackend()
ref = backend.write(data, os.path.join(tempfile.mkdtemp(), "huge.zarr"))

# Check memory before and after creating proxy
process = psutil.Process()
mem_before = process.memory_info().rss / 1024 / 1024
# ... create proxy, check shape, then check memory again
```

### Scenario B: Filesystem Backend with Binary Files
Test storing and retrieving actual binary files (e.g., a PDF):
```python
from scieasy.core.storage.filesystem import FilesystemBackend
# Write binary data, read it back, verify byte-for-byte match
```

### Scenario C: Nested CompositeData
Create a SpatialData containing an AnnData in its table slot:
```python
from scieasy.core.types.composite import SpatialData, AnnData
# Verify nested slot access works correctly
```

---

## 5. Verification Checklist

| # | Check | Result |
|---|-------|--------|
| 1 | `pytest tests/core/` all pass | [ ] |
| 2 | All 6 DataObject types can be created | [ ] |
| 3 | TypeSignature inheritance matching works | [ ] |
| 4 | Zarr round-trip write/read works | [ ] |
| 5 | Arrow/Parquet round-trip works | [ ] |
| 6 | Filesystem text/binary round-trip works | [ ] |
| 7 | ViewProxy lazy loading works (no eager load) | [ ] |
| 8 | ViewProxy slice loads partial data | [ ] |
| 9 | CompositeData slot type validation works | [ ] |
| 10 | LineageStore write/query/ancestors works | [ ] |
| 11 | EnvironmentSnapshot captures Python version | [ ] |
| 12 | broadcast_apply produces correct results | [ ] |
| 13 | content_hash is deterministic | [ ] |

---

## 6. Cleanup

```bash
# Remove any temporary files created during testing
rm -rf /tmp/tmp*  # Be careful with this on shared systems

# Or more targeted:
python -c "import tempfile; print(tempfile.gettempdir())"
# Manually review and clean temp directories
```
