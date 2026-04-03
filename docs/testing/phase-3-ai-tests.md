# Phase 3: Core Data Layer — AI Test Plan

> **Status**: Phase 3 is COMPLETE.
> This document catalogues existing automated tests and specifies additional tests
> for the data foundation layer: types, storage, proxy, lineage, and broadcast.

---

## 1. Overview

| Component | Source Module | Test File |
|-----------|-------------|-----------|
| DataObject + base types | `src/scieasy/core/types/` | `tests/core/test_types.py` |
| CompositeData | `src/scieasy/core/types/composite.py` | `tests/core/test_composite.py` |
| Storage backends | `src/scieasy/core/storage/` | `tests/core/test_storage.py` |
| ViewProxy | `src/scieasy/core/proxy.py` | `tests/core/test_proxy.py` |
| Lineage | `src/scieasy/core/lineage/` | `tests/core/test_lineage.py` |
| Broadcast | `src/scieasy/utils/broadcast.py` | `tests/core/test_broadcast.py` |
| Hashing | `src/scieasy/utils/hashing.py` | (inline in lineage tests) |

---

## 2. Existing Tests

### 2.1 `tests/core/test_types.py` (25 tests)

**TestTypeSignatureFromType** (18 parametrized):
- Tests TypeSignature auto-generation from MRO for all 18 types:
  DataObject, Array, Image, MSImage, SRSImage, FluorImage, Series, Spectrum,
  RamanSpectrum, MassSpectrum, DataFrame, PeakTable, MetabPeakTable, Text,
  Artifact, CompositeData, AnnData, SpatialData

**TestTypeSignatureMatches** (6 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_exact_match` | `Image` sig matches `Image` |
| 2 | `test_subtype_matches_parent` | `Image` sig matches `Array` |
| 3 | `test_parent_does_not_match_subtype` | `Array` sig does NOT match `Image` |
| 4 | `test_unrelated_types_no_match` | `Array` sig does NOT match `Series` |
| 5 | `test_deep_subtype_matches_root` | `RamanSpectrum` sig matches `DataObject` |
| 6 | `test_matches_self` | `DataObject` sig matches `DataObject` |

**TestDataObjectDtypeInfo** (4 tests):
- Validates `dtype_info` auto-generation on instances of Array, Series, DataFrame, CompositeData

**TestDataObjectMetadata** (2 tests):
- Validates metadata dict handling on DataObject instances

**TestDataObjectView** (1 test):
- Validates `view()` requires `storage_ref` to be set

**TestTypeRegistry** (6 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_register_and_resolve` | Register custom type, resolve by name |
| 2 | `test_resolve_missing_raises` | KeyError on unknown type name |
| 3 | `test_all_types` | `all_types()` returns all registered types |
| 4 | `test_scan_builtins` | `scan_builtins()` discovers built-in types |
| 5 | `test_load_class` | `load_class(module_path, class_name)` returns class |
| 6 | `test_is_instance` | `is_instance()` with inheritance |

### 2.2 `tests/core/test_composite.py` (11 tests)

**TestCompositeDataSlotAccess** (6 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_set_and_get` | Set slot, retrieve it |
| 2 | `test_get_missing_raises` | KeyError on missing slot |
| 3 | `test_slot_names_empty` | Empty composite has no slot names |
| 4 | `test_slot_names_populated` | Populated composite lists slot names |
| 5 | `test_slot_types_base_empty` | Base CompositeData has empty `expected_slots` |
| 6 | `test_init_with_slots` | Initialize with slots dict |

**TestAnnDataSlots** (5 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_slot_types` | AnnData has `X`, `obs`, `var`, `obsm` slots |
| 2 | `test_set_valid_slot` | Setting Array in `X` slot succeeds |
| 3 | `test_set_invalid_type_raises` | Setting Text in `X` slot raises TypeError |
| 4 | `test_set_subtype_accepted` | Image (subtype of Array) accepted in `X` slot |
| 5 | `test_dtype_info_slot_schema` | dtype_info includes slot schema |

**TestSpatialDataSlots** (2 tests)

**TestNestedComposites** (2 tests):
- `test_nested_access` — Access slot within nested CompositeData
- `test_nested_dtype_info` — dtype_info for nested composite

### 2.3 `tests/core/test_storage.py` (19 tests)

**TestZarrBackend** (5 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_write_read_roundtrip` | numpy array → Zarr → read back matches |
| 2 | `test_slice` | Read partial region matches expected slice |
| 3 | `test_iter_chunks` | Chunk iteration yields correct pieces |
| 4 | `test_get_metadata` | Metadata includes shape, dtype, chunks |

**TestArrowBackend** (6 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_write_read_roundtrip_from_dict` | dict → Table → Parquet → read back matches |
| 2 | `test_write_read_roundtrip_from_table` | Table → Parquet → read back matches |
| 3 | `test_slice_columns` | Column selection returns correct subset |
| 4 | `test_iter_chunks` | Chunk iteration yields correct pieces |
| 5 | `test_get_metadata` | Metadata includes num_columns, num_rows, schema |
| 6 | `test_write_invalid_type_raises` | Non-Table input raises TypeError |

**TestFilesystemBackend** (6 tests):
- Text round-trip, binary round-trip, byte-range slice, chunk iteration, metadata, invalid type rejection

**TestCompositeStore** (4 tests):
- Composite round-trip, slot slicing, metadata, chunk iteration

### 2.4 `tests/core/test_proxy.py` (9 tests)

**TestViewProxyLazyLoading** (6 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_shape_without_loading` | `proxy.shape` returns shape without loading data |
| 2 | `test_axes_from_metadata` | `proxy.axes` returns axes list |
| 3 | `test_slice_partial_read` | `proxy.slice()` loads only requested region |
| 4 | `test_to_memory_full_load` | `proxy.to_memory()` loads full data |
| 5 | `test_iter_chunks` | `proxy.iter_chunks()` yields correct chunks |
| 6 | `test_dtype_info_preserved` | dtype_info matches original DataObject |

**TestViewProxyFromDataObject** (2 tests):
- `test_image_view` — Create Image, set storage_ref, call `.view()`, verify proxy

### 2.5 `tests/core/test_lineage.py` (12 tests)

**TestEnvironmentSnapshot** (3 tests):
- `test_capture_basic` — Captures Python version and platform
- `test_capture_custom_deps` — Captures specified dependency versions
- `test_capture_missing_package_skipped` — Gracefully skips missing packages

**TestLineageStore** (5 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_write_and_query` | Write LineageRecord, query by output hash |
| 2 | `test_query_all` | Query all records for a block_id |
| 3 | `test_query_nonexistent_block` | Empty result for unknown block |
| 4 | `test_write_with_environment` | Environment snapshot stored correctly |
| 5 | `test_ancestors_linear_chain` | Trace ancestors through A→B→C chain |

**TestProvenanceGraph** (6 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_ancestors` | Find all ancestors of a node |
| 2 | `test_ancestors_partial` | Partial ancestor trace |
| 3 | `test_descendants` | Find all descendants of a node |
| 4 | `test_audit_trail_ordered` | Audit trail in chronological order |
| 5 | `test_diff` | Diff between two provenance paths |

### 2.6 `tests/core/test_broadcast.py` (10 tests)

**TestIterAxisSlices** (3 tests):
- `test_iterate_over_axis` — Iterate over named axis
- `test_iterate_first_axis` — Iterate over first axis
- `test_missing_axis_raises` — Error on non-existent axis

**TestBroadcastApply** (7 tests):
| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_2d_mask_times_3d_cube` | 2D mask broadcast onto 3D cube |
| 2 | `test_result_values` | Result values are correct |
| 3 | `test_axis_mismatch_raises` | Error on incompatible axes |
| 4 | `test_target_without_axes_raises` | Error when target has no axes |
| 5 | `test_over_axis_not_in_target_raises` | Error when broadcast axis missing from target |
| 6 | `test_multiple_over_axes` | Broadcasting over multiple axes |

---

## 3. Recommended Additional Unit Tests

### File: `tests/core/test_types_extended.py` (NEW)

```python
# Domain subtype field validation
def test_image_default_axes():
    """Image should have axes=["y", "x"]."""
    from scieasy.core.types.array import Image
    assert Image.axes == ["y", "x"]

def test_msimage_axes():
    """MSImage should have axes=["y", "x", "mz"]."""
    from scieasy.core.types.array import MSImage
    assert MSImage.axes == ["y", "x", "mz"]

def test_spectrum_inherits_series():
    """Spectrum inherits from Series."""
    from scieasy.core.types.series import Spectrum, Series
    assert issubclass(Spectrum, Series)

def test_peak_table_inherits_dataframe():
    """PeakTable inherits from DataFrame."""
    from scieasy.core.types.dataframe import PeakTable, DataFrame
    assert issubclass(PeakTable, DataFrame)

# TypeSignature edge cases
def test_type_signature_hash_stable():
    """Same type should produce same TypeSignature across calls."""
    from scieasy.core.types.array import Image
    from scieasy.core.types.base import TypeSignature
    sig1 = TypeSignature.from_type(Image)
    sig2 = TypeSignature.from_type(Image)
    assert sig1 == sig2

def test_type_signature_ordering():
    """TypeSignature chain should be ordered from most specific to most general."""
    from scieasy.core.types.array import Image
    from scieasy.core.types.base import TypeSignature
    sig = TypeSignature.from_type(Image)
    # First element should be Image, last should be DataObject
    assert sig.chain[0] == "Image"
    assert sig.chain[-1] == "DataObject"
```

### File: `tests/core/test_storage_extended.py` (NEW)

```python
# Large array handling
def test_zarr_large_array_chunked(tmp_path):
    """Write a large array in chunks, read back slices."""
    import numpy as np
    from scieasy.core.storage.zarr_backend import ZarrBackend
    backend = ZarrBackend()
    data = np.random.rand(1000, 1000).astype(np.float32)
    ref = backend.write(data, tmp_path / "large.zarr", chunks=(100, 100))
    # Read a single chunk
    chunk = backend.slice(ref, {"0": slice(0, 100), "1": slice(0, 100)})
    assert chunk.shape == (100, 100)
    np.testing.assert_array_equal(chunk, data[:100, :100])

# Empty data edge cases
def test_arrow_empty_table(tmp_path):
    """Write and read an empty table."""
    import pyarrow as pa
    from scieasy.core.storage.arrow_backend import ArrowBackend
    backend = ArrowBackend()
    table = pa.table({"col": pa.array([], type=pa.int64())})
    ref = backend.write(table, tmp_path / "empty.parquet")
    result = backend.read(ref)
    assert result.num_rows == 0

def test_filesystem_empty_text(tmp_path):
    """Write and read empty text file."""
    from scieasy.core.storage.filesystem import FilesystemBackend
    backend = FilesystemBackend()
    ref = backend.write("", tmp_path / "empty.txt")
    result = backend.read(ref)
    assert result == ""
```

---

## 4. Integration Tests

### File: `tests/core/test_type_storage_integration.py` (NEW)

```python
def test_image_zarr_roundtrip(tmp_path):
    """Create Image, store via ZarrBackend, load via ViewProxy, verify."""
    import numpy as np
    from scieasy.core.types.array import Image
    from scieasy.core.storage.zarr_backend import ZarrBackend
    from scieasy.core.proxy import ViewProxy

    data = np.random.rand(256, 256).astype(np.float32)
    backend = ZarrBackend()
    ref = backend.write(data, tmp_path / "img.zarr")

    img = Image(axes=["y", "x"], storage_ref=ref)
    proxy = img.view()
    assert proxy.shape == (256, 256)
    assert proxy.axes == ["y", "x"]
    loaded = proxy.to_memory()
    np.testing.assert_array_almost_equal(loaded, data)

def test_dataframe_arrow_roundtrip(tmp_path):
    """Create DataFrame, store via ArrowBackend, load via ViewProxy, verify."""
    import pyarrow as pa
    from scieasy.core.types.dataframe import DataFrame
    from scieasy.core.storage.arrow_backend import ArrowBackend

    table = pa.table({"name": ["A", "B", "C"], "value": [1.0, 2.0, 3.0]})
    backend = ArrowBackend()
    ref = backend.write(table, tmp_path / "df.parquet")

    df = DataFrame(columns=["name", "value"], row_count=3, storage_ref=ref)
    proxy = df.view()
    loaded = proxy.to_memory()
    assert loaded.num_rows == 3

def test_composite_anndata_roundtrip(tmp_path):
    """Create AnnData-like composite, store, load, verify slots."""
    import numpy as np
    import pyarrow as pa
    from scieasy.core.types.array import Array
    from scieasy.core.types.dataframe import DataFrame
    from scieasy.core.types.composite import AnnData
    from scieasy.core.storage.composite_store import CompositeStore

    anndata = AnnData()
    x = Array(axes=["obs", "var"])
    obs = DataFrame(columns=["cell_type"], row_count=100)
    anndata.set("X", x)
    anndata.set("obs", obs)

    store = CompositeStore()
    ref = store.write(anndata, tmp_path / "anndata_dir")
    loaded = store.read(ref)
    assert "X" in loaded.slot_names()
    assert "obs" in loaded.slot_names()

def test_lineage_after_storage(tmp_path):
    """Write data, record lineage, query ancestors."""
    import numpy as np
    from scieasy.core.storage.zarr_backend import ZarrBackend
    from scieasy.core.lineage.store import LineageStore
    from scieasy.core.lineage.record import LineageRecord
    from scieasy.utils.hashing import content_hash

    data = np.random.rand(100, 100)
    backend = ZarrBackend()
    ref = backend.write(data, tmp_path / "data.zarr")

    input_hash = content_hash(data.tobytes())
    output_hash = content_hash(b"output_marker")

    store = LineageStore(tmp_path / "lineage.db")
    record = LineageRecord(
        input_hashes=[input_hash],
        block_id="test_block",
        block_config={"key": "value"},
        block_version="1.0",
        output_hashes=[output_hash],
    )
    store.write(record)
    results = store.query(output_hash)
    assert len(results) == 1
    assert results[0].block_id == "test_block"
```

---

## 5. Edge Case / Regression Tests

```python
# ViewProxy: access without storage_ref
def test_view_without_storage_ref_raises():
    """DataObject.view() must raise when no storage_ref is set."""
    from scieasy.core.types.array import Image
    img = Image(axes=["y", "x"])
    with pytest.raises(ValueError):
        img.view()

# TypeRegistry: duplicate registration
def test_type_registry_duplicate_warns():
    """Re-registering same type name should overwrite or warn."""
    from scieasy.core.types.registry import TypeRegistry
    registry = TypeRegistry()
    from scieasy.core.types.array import Image
    registry.register("Image", Image)
    registry.register("Image", Image)  # should not error
    assert registry.resolve("Image") is Image

# LineageStore: concurrent writes
def test_lineage_store_multiple_records(tmp_path):
    """Multiple records for same block_id."""
    from scieasy.core.lineage.store import LineageStore
    from scieasy.core.lineage.record import LineageRecord
    store = LineageStore(tmp_path / "lineage.db")
    for i in range(10):
        record = LineageRecord(
            input_hashes=[f"in_{i}"],
            block_id="multi_block",
            block_config={},
            block_version="1.0",
            output_hashes=[f"out_{i}"],
        )
        store.write(record)
    results = store.query_all("multi_block")
    assert len(results) == 10

# Broadcast: 1D onto 1D (degenerate case)
def test_broadcast_1d_onto_1d():
    """Broadcasting 1D source onto 1D target with same axis."""
    import numpy as np
    from scieasy.utils.broadcast import broadcast_apply
    from scieasy.core.types.array import Array

    target = Array(axes=["x"])
    source = Array(axes=["x"])
    # This should work as element-wise application
    # (exact behavior depends on implementation)
```

---

## 6. Comprehensive Agent Tests

```bash
# Run all Phase 3 tests
pytest tests/core/ -v --cov=scieasy.core --cov-report=term-missing

# Run type tests only
pytest tests/core/test_types.py tests/core/test_composite.py -v

# Run storage tests only
pytest tests/core/test_storage.py -v

# Run proxy tests only
pytest tests/core/test_proxy.py -v

# Run lineage tests only
pytest tests/core/test_lineage.py -v

# Run broadcast tests only
pytest tests/core/test_broadcast.py -v

# Full pipeline test
pytest tests/core/ tests/architecture/ -v --cov=scieasy --cov-report=term-missing
```

---

## 7. Coverage Targets

| Module | Current Tests | Target |
|--------|--------------|--------|
| `core/types/` | 25 + 11 = 36 | 45+ |
| `core/storage/` | 19 | 25+ |
| `core/proxy.py` | 9 | 12+ |
| `core/lineage/` | 12 | 15+ |
| `utils/broadcast.py` | 10 | 12+ |
| `utils/hashing.py` | (inline) | 3+ |
| **Total Phase 3** | **86** | **110+** |

---

## 8. Fixtures & Helpers

```python
# tests/core/conftest.py
import pytest
import numpy as np
import pyarrow as pa

@pytest.fixture
def sample_image_data():
    """256x256 float32 random image data."""
    return np.random.rand(256, 256).astype(np.float32)

@pytest.fixture
def sample_table():
    """Simple 3-column, 100-row Arrow table."""
    return pa.table({
        "id": range(100),
        "name": [f"item_{i}" for i in range(100)],
        "value": np.random.rand(100),
    })

@pytest.fixture
def zarr_backend():
    from scieasy.core.storage.zarr_backend import ZarrBackend
    return ZarrBackend()

@pytest.fixture
def arrow_backend():
    from scieasy.core.storage.arrow_backend import ArrowBackend
    return ArrowBackend()

@pytest.fixture
def lineage_store(tmp_path):
    from scieasy.core.lineage.store import LineageStore
    return LineageStore(tmp_path / "test_lineage.db")
```

---

## 9. How to Run

```bash
# All Phase 3 tests with coverage
pytest tests/core/ -v --cov=scieasy.core --cov-report=term-missing

# Quick smoke test
pytest tests/core/ -x -q

# With verbose output for debugging
pytest tests/core/ -v -s --tb=long
```
