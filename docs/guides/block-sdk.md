# SciEasy Block SDK -- Developer Guide

This guide covers everything you need to build, test, and distribute custom
blocks for the SciEasy workflow runtime.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Block Authoring Guide](#2-block-authoring-guide)
3. [Block Types Reference](#3-block-types-reference)
4. [Data Transport with Collection](#4-data-transport-with-collection)
5. [Testing](#5-testing)
6. [Port System](#6-port-system)
7. [Configuration](#7-configuration)

---

## 1. Introduction

### What is the SciEasy block system?

SciEasy organizes scientific data processing into **blocks** -- self-contained
units of computation with typed inputs, typed outputs, and validated
configuration. Blocks are the building blocks (Layer 2 in the architecture) that
users wire together on a visual canvas to form workflows.

Each block declares:

- **Input ports**: what data it consumes and what types are accepted.
- **Output ports**: what data it produces.
- **Configuration schema**: parameters the user can set (thresholds, column
  names, file paths, etc.).
- **A `run()` method**: the actual computation.

### Architecture overview

```
Layer 6: Frontend (ReactFlow canvas, block palette)
Layer 5: API + SPA serving (FastAPI REST, WebSocket)
Layer 4: AI services (block generation, workflow synthesis)
Layer 3: Execution engine (DAG scheduler, subprocess lifecycle)
Layer 2: Block system  <-- you are here
Layer 1: Data foundation (type hierarchy, storage backends, lazy loading)
```

Blocks live at Layer 2. They receive data from the engine as `Collection`
objects (Layer 1) and return `Collection` objects. The engine (Layer 3) handles
scheduling, subprocess isolation, and state management.

### How blocks fit into workflows

A workflow is a directed acyclic graph (DAG) of blocks connected by edges. Each
edge connects an output port of one block to an input port of another. The
engine executes blocks in topological order, passing data between them via
`Collection` objects.

When a block runs, the engine:

1. Validates inputs against the block's port declarations.
2. Calls `block.run(inputs, config)` in an isolated subprocess.
3. Validates outputs and passes them to downstream blocks.

### Two distribution tiers

| Tier | Description | Discovery mechanism |
|------|-------------|---------------------|
| **Tier 1** | Drop-in `.py` files | File-system scan of project and user directories |
| **Tier 2** | Pip-installable packages | Python `entry_points` protocol |

Tier 1 is for quick prototyping and project-local blocks. Tier 2 is for
distributing reusable block packages via PyPI.

---

## 2. Block Authoring Guide

### Tier 1: Drop-in blocks

The fastest way to create a block is to write a single `.py` file and drop it
into a scan directory.

#### Minimal example: a ProcessBlock with `process_item()`

```python
"""my_doubler.py -- doubles every value in an Array."""

from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.array import Array


class DoublerBlock(ProcessBlock):
    name: ClassVar[str] = "Array Doubler"
    description: ClassVar[str] = "Multiply every element by 2"
    version: ClassVar[str] = "0.1.0"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="data", accepted_types=[Array], description="Input array"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="result", accepted_types=[Array], description="Doubled array"),
    ]

    def process_item(self, item: Any, config: BlockConfig) -> Any:
        """Process a single Array item."""
        data = item.view().to_memory()  # load numpy array into memory
        doubled = data * 2
        return Array(data=doubled)
```

That is a complete, working block. The `ProcessBlock` base class provides a
default `run()` that iterates the input Collection and calls `process_item()`
for each item. You only need to implement the per-item logic.

#### Where to place drop-in files

The block registry scans these directories for `.py` files:

| Location | Scope |
|----------|-------|
| `<project>/blocks/` | Project-local blocks. Created by `scieasy init`. |
| `~/.scieasy/blocks/` | User-global blocks. Available to all projects. |

Files starting with `_` (e.g., `_helpers.py`) are ignored during scanning.

#### Auto-discovery mechanism

When the registry scans a directory, it:

1. Loads each `.py` file as a Python module.
2. Inspects all top-level attributes for classes that are concrete subclasses of
   `Block`.
3. Creates a `BlockSpec` descriptor for each discovered block (name, ports,
   config schema, file mtime).
4. Registers the spec by display name and type name.

File modification times are tracked for hot-reload support: if you edit a
drop-in file, the registry detects the change and re-imports the module.

### Tier 2: Pip-installable packages

For distributing blocks as installable Python packages, use the entry-points
protocol.

#### Entry-points protocol

External packages register blocks using Python's standard `entry_points`
mechanism with the group `scieasy.blocks`. The entry point must resolve to a
**callable** that returns either:

- `(PackageInfo, list[type[Block]])` -- package metadata plus block classes
  (recommended)
- `list[type[Block]]` -- plain list of block classes (backward compatible; the
  entry-point name is used as the display name)

#### The `PackageInfo` dataclass

```python
from scieasy.blocks.base.package_info import PackageInfo

PACKAGE_INFO = PackageInfo(
    name="SRS Imaging",                    # display name in the GUI palette
    description="SRS microscopy analysis", # short description
    author="Dr. Wang Lab",                 # author or organization
    version="0.1.0",                       # package version
)
```

`PackageInfo` is a frozen dataclass with these fields:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `name` | `str` | (required) | Display name in the block palette |
| `description` | `str` | `""` | Short package description |
| `author` | `str` | `""` | Author or organization |
| `version` | `str` | `"0.1.0"` | Package version |

#### Callable protocol

Your package's `__init__.py` (or any module) must expose a callable that the
registry invokes at scan time:

```python
# src/scieasy_blocks_srs/__init__.py

from scieasy.blocks.base.package_info import PackageInfo

PACKAGE_INFO = PackageInfo(
    name="SRS Imaging",
    description="Stimulated Raman Scattering microscopy analysis toolkit",
    author="Dr. Wang Lab",
    version="0.1.0",
)

def get_blocks():
    """Entry-point callable for scieasy.blocks discovery."""
    from .processing.unmixing import SpectralUnmixingBlock
    from .processing.baseline import BaselineCorrectionBlock
    from .stat.pca import PCABlock
    from .io.srs_reader import SRSReaderBlock

    return PACKAGE_INFO, [
        SRSReaderBlock,
        SpectralUnmixingBlock,
        BaselineCorrectionBlock,
        PCABlock,
    ]
```

Use lazy imports inside the callable (not at module top level) to avoid import
errors when the package's optional dependencies are not installed.

#### `pyproject.toml` configuration

```toml
[project]
name = "scieasy-blocks-srs"
version = "0.1.0"
dependencies = ["scieasy>=0.1", "tifffile"]

[project.entry-points."scieasy.blocks"]
srs = "scieasy_blocks_srs:get_blocks"

# Optional: register custom DataObject subtypes
[project.entry-points."scieasy.types"]
srs = "scieasy_blocks_srs.types:get_types"

# Optional: register custom file-format adapters
[project.entry-points."scieasy.adapters"]
srs = "scieasy_blocks_srs.io:get_adapters"
```

Three entry-point groups are available:

| Group | Purpose | Return type |
|-------|---------|-------------|
| `scieasy.blocks` | Block class discovery | `(PackageInfo, list[type[Block]])` or `list[type[Block]]` |
| `scieasy.types` | Custom DataObject subtype registration | `list[type[DataObject]]` |
| `scieasy.adapters` | Custom IO adapter registration | `list[type[FormatAdapter]]` |

#### Two-level categorization in the GUI

Blocks appear in the GUI palette grouped by **package** (top level) and
**category** (second level). Category is inferred from the block's parent class:

| Parent class | Category |
|-------------|----------|
| `ProcessBlock` | `process` |
| `IOBlock` | `io` |
| `CodeBlock` | `code` |
| `AppBlock` | `app` |
| `AIBlock` | `ai` |

Example palette layout:

```
Block Palette:
+-- Core (built-in)
|   +-- IO Block
|   +-- Transform Block
|   +-- Code Block
+-- SRS Imaging (your package)
|   +-- SRS Reader         (category: io)
|   +-- Spectral Unmixing  (category: process)
|   +-- Baseline Correction (category: process)
|   +-- PCA                (category: process)
```

#### Using `scieasy init-block-package` to scaffold

SciEasy provides a CLI command to generate a complete block package skeleton:

```bash
scieasy init-block-package scieasy-blocks-srs \
  --display-name "SRS Imaging" \
  --author "Dr. Wang Lab" \
  --categories "processing,stat,io"
```

This generates:

```
scieasy-blocks-srs/
  src/scieasy_blocks_srs/
    __init__.py                    # PackageInfo + get_blocks()
    processing/example_block.py    # Example block per category
    stat/example_block.py
    io/example_block.py
  tests/
    test_example_block.py          # Example test using BlockTestHarness
  pyproject.toml                   # Pre-configured entry-points
  README.md
```

The generated example blocks are minimal working implementations with inline
comments explaining the contract. Edit them to implement your actual logic.

---

## 3. Block Types Reference

SciEasy provides five block base classes. Each serves a different use case.
All share the same core contract: they declare `input_ports`, `output_ports`,
and implement `run()`.

### Common contract

Every block has these class-level variables (ClassVars):

| ClassVar | Type | Default | Purpose |
|----------|------|---------|---------|
| `name` | `str` | `"Unnamed Block"` | Human-readable display name |
| `description` | `str` | `""` | Short description for the palette |
| `version` | `str` | `"0.1.0"` | Block version |
| `input_ports` | `list[InputPort]` | `[]` | Input port declarations |
| `output_ports` | `list[OutputPort]` | `[]` | Output port declarations |
| `execution_mode` | `ExecutionMode` | `AUTO` | How the engine runs this block |
| `terminate_grace_sec` | `float` | `5.0` | Seconds before SIGKILL on cancel |
| `key_dependencies` | `list[str]` | `[]` | Package names for lineage records |
| `config_schema` | `dict` | `{"type": "object", "properties": {}}` | JSON Schema for config UI |

The `run()` signature is the same for all block types:

```python
def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
    ...
```

- **inputs**: a dictionary mapping port name to `Collection`. Each Collection
  wraps one or more `DataObject` instances.
- **config**: a `BlockConfig` instance containing user-set parameters.
- **returns**: a dictionary mapping output port name to `Collection`.

### 3.1 ProcessBlock

**Purpose**: Deterministic, algorithm-driven data transformations. This is the
most common block type. Use it when your block takes data in, transforms it, and
produces data out.

**Module**: `scieasy.blocks.process.process_block`

**Special ClassVars**:

| ClassVar | Type | Default | Purpose |
|----------|------|---------|---------|
| `algorithm` | `str` | `""` | Human-readable algorithm identifier |

**How it works**: `ProcessBlock` provides a default `run()` that iterates the
primary input Collection and calls `process_item()` for each item. This means
80% of blocks only need to override `process_item()`.

**Tier 1 pattern** (recommended for most blocks):

```python
from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.array import Image


class GaussianBlurBlock(ProcessBlock):
    name: ClassVar[str] = "Gaussian Blur"
    description: ClassVar[str] = "Apply Gaussian blur to images"
    algorithm: ClassVar[str] = "gaussian_blur"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="images", accepted_types=[Image], description="Input images"),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="blurred", accepted_types=[Image], description="Blurred images"),
    ]
    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "sigma": {"type": "number", "default": 1.0, "title": "Sigma"},
        },
    }

    def process_item(self, item: Any, config: BlockConfig) -> Any:
        import numpy as np
        from scipy.ndimage import gaussian_filter

        sigma = config.get("sigma", 1.0)
        data = item.view().to_memory()
        blurred = gaussian_filter(data, sigma=sigma)
        return Image(data=blurred)
```

**Tier 2/3 pattern** (override `run()` directly when you need cross-item logic):

```python
def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
    from scieasy.core.types.collection import Collection

    images = inputs["images"]

    # Use map_items for sequential processing with auto-flush
    result = self.map_items(lambda img: self._process(img, config), images)

    return {"output": result}
```

### 3.2 IOBlock

**Purpose**: Data ingress (loading files) and egress (saving files). Handles
reading from and writing to the file system using pluggable format adapters.

**Module**: `scieasy.blocks.io.io_block`

**Special ClassVars**:

| ClassVar | Type | Default | Purpose |
|----------|------|---------|---------|
| `direction` | `str` | `"input"` | `"input"` to load, `"output"` to save |
| `format` | `str` | `""` | File format hint |

**Pre-declared ports**:

- Input port: `data` (accepted types: `[DataObject]`, required: `False`)
- Output port: `data` (accepted types: `[DataObject]`)

**Config schema** includes `path` (required) and `direction`.

**How it works**: In input mode, the block scans the given path (file or
directory), selects the appropriate format adapter by file extension, creates
lazy `StorageReference` objects, and wraps them in a Collection. In output mode,
it iterates the input Collection and writes each item through the adapter.

**Example: Custom IOBlock subclass**

```python
from typing import ClassVar

from scieasy.blocks.io.io_block import IOBlock


class TiffLoaderBlock(IOBlock):
    name: ClassVar[str] = "TIFF Loader"
    description: ClassVar[str] = "Load TIFF image files"
    direction: ClassVar[str] = "input"
    format: ClassVar[str] = "tiff"
```

### 3.3 CodeBlock

**Purpose**: Execute user-provided scripts in Python, R, or Julia. Supports
inline code snippets and external script files. Aimed at researchers who want to
embed custom code without creating a formal block class.

**Module**: `scieasy.blocks.code.code_block`

**Special ClassVars**:

| ClassVar | Type | Default | Purpose |
|----------|------|---------|---------|
| `language` | `str` | `"python"` | Language: `"python"`, `"r"`, `"julia"` |
| `mode` | `str` | `"inline"` | `"inline"` or `"script"` |

**Auto-unpack/repack**: CodeBlock automatically converts Collection inputs to
user-friendly formats before running user code, and wraps outputs back into
Collections afterward:

- Collection of length 1 is delivered as a single in-memory object.
- Collection of length > 1 is delivered as a `LazyList` (memory-safe iteration).

**Config schema** includes `language`, `mode`, `code` (for inline), and
`script_path` (for script mode).

**Note**: All CodeBlock execution is delegated to a subprocess-based runner.
User code never runs in the main engine process.

### 3.4 AppBlock

**Purpose**: Delegate work to an external GUI application (e.g., Fiji, napari,
ElMAVEN). Communication happens via a file-exchange directory: the block
serializes inputs, launches the application, watches for output files, and
collects the results.

**Module**: `scieasy.blocks.app.app_block`

**Special ClassVars**:

| ClassVar | Type | Default | Purpose |
|----------|------|---------|---------|
| `app_command` | `str` | `""` | Shell command to launch the application |
| `execution_mode` | `ExecutionMode` | `EXTERNAL` | Always external for AppBlock |
| `output_patterns` | `list[str]` | `["*"]` | Glob patterns for output file detection |
| `watch_timeout` | `int` | `300` | Seconds to wait for output files |

**State machine**: AppBlock has a special lifecycle:
`IDLE -> READY -> RUNNING -> PAUSED -> RUNNING -> DONE`

The block enters `PAUSED` after launching the external application, signaling to
the scheduler that it is waiting for human interaction. Once output files are
detected (via `FileWatcher`), it transitions back to `RUNNING` and then `DONE`.

**Example**:

```python
from typing import ClassVar

from scieasy.blocks.app.app_block import AppBlock


class FijiBlock(AppBlock):
    name: ClassVar[str] = "Fiji"
    description: ClassVar[str] = "Open data in Fiji for manual processing"
    app_command: ClassVar[str] = "fiji"
    output_patterns: ClassVar[list[str]] = ["*.tif", "*.tiff"]
    watch_timeout: ClassVar[int] = 600  # 10 minutes
```

### 3.5 AIBlock

**Purpose**: LLM-driven data processing with prompt templates. This block type
uses a large language model to process or analyze data.

**Module**: `scieasy.blocks.ai.ai_block`

**Special ClassVars**:

| ClassVar | Type | Default | Purpose |
|----------|------|---------|---------|
| `model` | `str` | `""` | LLM backend identifier |
| `prompt_template` | `str` | `""` | Template string for prompts |

**Note**: AIBlock is currently a placeholder. The `run()` method raises
`NotImplementedError`. The infrastructure for AI-powered blocks is planned but
not yet implemented.

---

## 4. Data Transport with Collection

### What is a Collection?

`Collection` is the standard transport wrapper for data flowing between blocks.
It is a **homogeneous, ordered list of `DataObject` instances** with a declared
`item_type`.

```python
from scieasy.core.types.collection import Collection
from scieasy.core.types.array import Image

# Create a Collection of Images
images = Collection(items=[img1, img2, img3], item_type=Image)

# Iterate
for image in images:
    print(image.shape)

# Index
first = images[0]

# Length
count = len(images)
```

**Key invariants**:

- All items must be instances of the same base `DataObject` subclass (or its
  children -- an `SRSImage` is accepted in a `Collection[Image]`).
- `item_type` is set at construction and is immutable.
- Empty Collections require an explicit `item_type` parameter.

### Creating Collections

```python
# From a list of DataObjects (item_type inferred from first item)
col = Collection(items=[array1, array2])

# From a list with explicit item_type
col = Collection(items=[img1, img2], item_type=Image)

# Empty Collection (item_type required)
col = Collection(items=[], item_type=Image)
```

### Collection utilities on Block

The `Block` base class provides static helper methods for working with
Collections. These are available in all block types.

#### `pack(items, item_type=None)`

Pack a list of `DataObject` instances into a Collection, auto-flushing each item
to storage if it does not already have a `StorageReference`.

```python
results = [Image(data=arr1), Image(data=arr2)]
output_collection = self.pack(results, item_type=Image)
```

#### `unpack(collection)`

Unpack a Collection into a plain Python list of `DataObject` instances.

```python
items = self.unpack(inputs["images"])
for item in items:
    data = item.view().to_memory()
    # ... process data ...
```

#### `unpack_single(collection)`

Unpack a length-1 Collection into a single `DataObject`. Raises `ValueError` if
the Collection does not have exactly one item.

```python
single_image = self.unpack_single(inputs["image"])
```

#### `map_items(func, collection)`

Apply a function to each item in a Collection sequentially. Each result is
auto-flushed to storage. Returns a new Collection. Peak memory: one input item
plus one output item per iteration step.

```python
def blur(image):
    from scipy.ndimage import gaussian_filter
    data = image.view().to_memory()
    return Image(data=gaussian_filter(data, sigma=1.0))

blurred = self.map_items(blur, inputs["images"])
```

#### `parallel_map(func, collection, max_workers=4)`

Apply a function to each item in parallel using `ProcessPoolExecutor`.
Each result is auto-flushed to storage. Returns a new Collection.

**Warning**: `parallel_map` loads `max_workers` items into memory concurrently.
For large items (images, MSI datasets), set `max_workers=1` or use `map_items()`
which processes one item at a time.

```python
output = self.parallel_map(process_fn, inputs["data"], max_workers=2)
```

### `process_item()` for Tier 1 simplicity

`ProcessBlock.process_item()` is the simplest authoring pattern. You implement
a function that transforms a single item, and the framework handles iteration,
auto-flushing, and Collection construction.

```python
def process_item(self, item: Any, config: BlockConfig) -> Any:
    data = item.view().to_memory()
    result = my_transform(data)
    return Image(data=result)
```

The `ProcessBlock.run()` default implementation does the following automatically:

1. Takes the first (primary) input Collection.
2. Iterates each item.
3. Calls `self.process_item(item, config)` for each.
4. Auto-flushes each result to storage.
5. Packs all results into an output Collection on the first output port.

### Three-tier memory safety model

| Tier | Method | Who manages iteration? | Memory bound? |
|------|--------|----------------------|---------------|
| 1 | `process_item()` | Framework (ProcessBlock) | Yes (1 item at a time) |
| 2 | `map_items()` / `parallel_map()` | Block (with auto-flush) | Controllable |
| 3 | Manual `Collection` + `pack()` | Block (full control) | Developer responsibility |

**Default recommendation**: Use Tier 1 (`process_item()`). Only opt into Tier
2 or Tier 3 when you need cross-item operations (e.g., PCA across all items,
normalization requiring global statistics).

---

## 5. Testing

### BlockTestHarness

SciEasy provides `BlockTestHarness` in `scieasy.testing` to simplify block
testing. It eliminates boilerplate for creating test inputs, running blocks, and
verifying outputs.

**Note**: `BlockTestHarness` is specified in ADR-026 and is planned for
implementation at `src/scieasy/testing/harness.py`. The API described here
follows the ADR-026 specification.

```python
from scieasy.testing import BlockTestHarness

class TestMyBlock:
    def test_doubles_values(self, tmp_path):
        harness = BlockTestHarness(MyTransformBlock, work_dir=tmp_path)
        result = harness.run(
            inputs={"data": {"x": [1, 2, 3], "y": [4, 5, 6]}},
            params={"column": "x"},
        )
        assert result["output"].column("x").to_pylist() == [2, 4, 6]
```

**What `BlockTestHarness` does**:

- Wraps raw Python data (dicts, lists, numpy arrays) into appropriate
  `DataObject` instances.
- Creates a temporary project structure.
- Constructs `BlockConfig` from the provided `params`.
- Calls the block's `run()` method with properly constructed inputs.
- Validates output types against the block's port declarations.
- Materializes output `DataObject` instances for easy assertion.
- Cleans up temporary files.

### Validation functions

ADR-026 specifies the following validation utilities:

- **`validate_block(block_class)`**: Verify that a block class has valid
  `input_ports`, `output_ports`, a conforming `run()` signature, and consistent
  `config_schema`.

- **`validate_package_info(info)`**: Verify that a `PackageInfo` instance has
  all required fields and valid values.

- **`validate_entry_point_callable(callable_fn)`**: Invoke the callable and
  verify it returns either `(PackageInfo, list[type[Block]])` or
  `list[type[Block]]`.

### Smoke testing with mock inputs

For quick smoke tests, pass minimal mock data to the harness:

```python
def test_block_does_not_crash(self, tmp_path):
    harness = BlockTestHarness(MyBlock, work_dir=tmp_path)
    # Provide minimal valid inputs
    result = harness.run(
        inputs={"data": [1.0, 2.0, 3.0]},
        params={},
    )
    assert "output" in result
```

### Testing without the harness

You can also test blocks directly using `Collection` and `BlockConfig`:

```python
import numpy as np
from scieasy.blocks.base.config import BlockConfig
from scieasy.core.types.array import Image
from scieasy.core.types.collection import Collection

def test_doubler_block():
    block = DoublerBlock()
    data = np.ones((100, 100))
    img = Image(data=data)
    inputs = {"data": Collection([img], item_type=Image)}
    config = BlockConfig(params={"factor": 2})

    outputs = block.run(inputs, config)

    assert "result" in outputs
    result_col = outputs["result"]
    assert len(result_col) == 1
```

---

## 6. Port System

Ports define the typed connection endpoints on blocks. They control what data a
block accepts and produces, enabling type checking at workflow design time.

### InputPort

```python
from scieasy.blocks.base.ports import InputPort

InputPort(
    name="images",                    # port identifier (must be unique per block)
    accepted_types=[Image, Array],    # list of accepted DataObject subclasses
    description="Input images",       # human-readable description
    required=True,                    # whether the port must be connected
    default=None,                     # default value if not connected (optional)
    constraint=None,                  # validation function (optional)
    constraint_description="",        # human-readable constraint description
)
```

**Fields**:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `name` | `str` | (required) | Unique port identifier |
| `accepted_types` | `list[type]` | (required) | Accepted DataObject subclasses |
| `description` | `str` | `""` | Human-readable description |
| `required` | `bool` | `True` | Whether the input must be provided |
| `default` | `Any` | `None` | Default value if input is not connected |
| `constraint` | `Callable` | `None` | Custom validation function |
| `constraint_description` | `str` | `""` | Description of the constraint |

### OutputPort

```python
from scieasy.blocks.base.ports import OutputPort

OutputPort(
    name="result",
    accepted_types=[Image],
    description="Processed images",
)
```

**Fields**:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `name` | `str` | (required) | Unique port identifier |
| `accepted_types` | `list[type]` | (required) | Produced DataObject subclasses |
| `description` | `str` | `""` | Human-readable description |
| `required` | `bool` | `True` | Whether the port always produces output |

### Type checking

Port type checking is `isinstance`-based and inheritance-aware. If a port
accepts `Image`, it will also accept `SRSImage` (which inherits from `Image`).

When a `Collection` is passed to a port, the port system checks the Collection's
`item_type` against the port's `accepted_types` -- the `Collection` wrapper
itself is transparent. An empty `accepted_types` list means the port accepts
anything.

```python
# This port accepts Image and all Image subclasses (SRSImage, FluorImage, etc.)
InputPort(name="data", accepted_types=[Image])

# This port accepts any DataObject
InputPort(name="data", accepted_types=[DataObject])

# This port accepts anything (empty list)
InputPort(name="data", accepted_types=[])
```

### Constraint functions

Input ports can declare a `constraint` function for custom validation beyond
type checking. The constraint receives the **Collection** (not individual items)
and must return `True` for valid input:

```python
InputPort(
    name="images",
    accepted_types=[Image],
    constraint=lambda col: all(
        item.axes is not None and {"y", "x"}.issubset(set(item.axes))
        for item in col
    ),
    constraint_description="All images must have y and x axes",
)
```

The `validate_port_constraint()` function returns `(True, "")` on success or
`(False, description)` on failure.

### Connection validation

The `validate_connection(source_port, target_port)` function checks whether an
edge between two ports is type-compatible. It returns `(True, "")` if at least
one type produced by the source is accepted by the target.

```python
from scieasy.blocks.base.ports import validate_connection

ok, reason = validate_connection(source_output_port, target_input_port)
if not ok:
    print(f"Invalid connection: {reason}")
```

---

## 7. Configuration

### BlockConfig

`BlockConfig` is a Pydantic `BaseModel` that holds block parameters. It uses
`extra="allow"` so subclasses and plugins can attach additional fields.

```python
from scieasy.blocks.base.config import BlockConfig

# Create a config with parameters
config = BlockConfig(params={"sigma": 1.5, "threshold": 0.8})

# Access parameters
sigma = config.get("sigma", 1.0)       # returns 1.5
missing = config.get("missing", None)   # returns None

# Access the raw params dict
all_params = config.params
```

**Fields**:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `params` | `dict[str, Any]` | `{}` | Key-value parameter store |

### JSON Schema for config properties

Blocks declare a `config_schema` ClassVar using JSON Schema format. The frontend
uses this schema to generate configuration UI elements automatically.

```python
config_schema: ClassVar[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "sigma": {
            "type": "number",
            "default": 1.0,
            "title": "Gaussian Sigma",
            "description": "Standard deviation for the Gaussian kernel",
            "ui_priority": 1,     # controls ordering in the config panel
        },
        "threshold": {
            "type": "number",
            "default": 0.5,
            "title": "Detection Threshold",
            "minimum": 0.0,
            "maximum": 1.0,
            "ui_priority": 2,
        },
        "method": {
            "type": "string",
            "enum": ["otsu", "adaptive", "manual"],
            "default": "otsu",
            "title": "Thresholding Method",
            "ui_priority": 3,
        },
    },
    "required": ["sigma"],
}
```

**Supported JSON Schema types for UI generation**:

| JSON type | UI element |
|-----------|------------|
| `"string"` | Text input |
| `"string"` with `"enum"` | Dropdown select |
| `"number"` | Numeric input |
| `"integer"` | Integer input |
| `"boolean"` | Checkbox |

The `ui_priority` field controls the display order of configuration fields in
the frontend panel. Lower values appear first.

---

## Appendix A: Block Lifecycle and State Machine

Blocks go through the following states during execution:

```
IDLE -> READY -> RUNNING -> DONE -> IDLE (re-run)
                    |
                    +-> PAUSED -> RUNNING (resume)
                    |
                    +-> ERROR -> IDLE (retry)
                    |
                    +-> CANCELLED -> IDLE (retry)

IDLE -> SKIPPED -> IDLE (upstream input unavailable)
```

**State definitions**:

| State | Meaning |
|-------|---------|
| `IDLE` | Block is inactive, awaiting scheduling. |
| `READY` | Inputs are available, block is queued for execution. |
| `RUNNING` | Block's `run()` method is currently executing. |
| `PAUSED` | Waiting for external input (AppBlock). |
| `DONE` | Execution completed successfully. |
| `ERROR` | Execution failed with an exception. |
| `CANCELLED` | Execution was terminated by the user or engine. |
| `SKIPPED` | Block cannot execute because required upstream inputs are missing. |

### ExecutionMode

| Mode | Meaning |
|------|---------|
| `AUTO` | Engine schedules and runs the block automatically (default). |
| `INTERACTIVE` | Block requires user interaction (manual review blocks). |
| `EXTERNAL` | Block delegates to an external application (AppBlock). |

---

## Appendix B: Execution Environment

Blocks run in **isolated subprocesses**, not in the main engine process. This
means:

**You CAN**:

- Use any amount of CPU and memory.
- Import any library (numpy, scipy, scikit-learn, etc.).
- Read and write project files.
- Return `DataObject` instances from `run()`.
- Raise exceptions (the engine catches them and marks the block as ERROR).

**You CANNOT**:

- Access global mutable state across calls.
- Share memory with other blocks.
- Hold persistent connections between invocations.
- Spawn background threads that outlive `run()`.

### Cancellation

Blocks do not need to explicitly handle cancellation. The engine terminates the
subprocess. However, if your block writes partial output, use atomic patterns
(write to a temporary file, then rename) so that cancellation mid-write does not
produce corrupt files.

---

## Appendix C: Custom Data Types

External developers may define domain-specific types by subclassing core types:

```python
from typing import ClassVar
from scieasy.core.types.array import Image

class SRSImage(Image):
    """SRS microscopy image with spectral wavenumber axis."""
    axes: ClassVar[list[str] | None] = ["y", "x", "wavenumber"]
```

**Subclassing rules**:

- Inherit from the nearest core type (`Array`, `DataFrame`, `Text`, etc.).
- Storage backend is determined by the base type (`SRSImage` inherits `Array`'s
  Zarr backend) -- no custom storage needed.
- `axes` is a `ClassVar` that labels dimensions semantically, not their
  coordinate values.
- Instance-specific metadata (e.g., wavenumber coordinates, spatial calibration)
  goes in `DataObject._metadata` dict.
- Maximum inheritance depth: 3 levels from `DataObject` (e.g.,
  `DataObject -> Array -> Image -> SRSImage`).

**Port type matching**: Uses `isinstance`, so `SRSImage` auto-matches ports
expecting `Image` or `Array`. A port expecting `SRSImage` will NOT accept a
plain `Image`.

**Registration**: Custom types are registered via the `scieasy.types`
entry-point group:

```python
# In your package's types.py
def get_types():
    from .types import SRSImage, RamanImage
    return [SRSImage, RamanImage]
```

---

## Appendix D: Quick Reference

### Minimal ProcessBlock (Tier 1)

```python
from typing import Any, ClassVar
from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.core.types.array import Array

class MyBlock(ProcessBlock):
    name: ClassVar[str] = "My Block"
    description: ClassVar[str] = "Does something useful"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(name="data", accepted_types=[Array]),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="result", accepted_types=[Array]),
    ]

    def process_item(self, item: Any, config: BlockConfig) -> Any:
        data = item.view().to_memory()
        result = data + 1  # your logic here
        return Array(data=result)
```

### Minimal pyproject.toml (Tier 2)

```toml
[project]
name = "scieasy-blocks-mypackage"
version = "0.1.0"
dependencies = ["scieasy>=0.1"]

[project.entry-points."scieasy.blocks"]
mypackage = "scieasy_blocks_mypackage:get_blocks"
```

### Minimal entry-point callable

```python
from scieasy.blocks.base.package_info import PackageInfo

def get_blocks():
    from .my_block import MyBlock
    return PackageInfo(name="My Package"), [MyBlock]
```
