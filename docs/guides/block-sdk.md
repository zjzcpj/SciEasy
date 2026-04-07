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
```

Two entry-point groups are available (ADR-028 §D4 supersedes the old
`scieasy.adapters` group from ADR-025 §6 — plugin-owned IO loaders and
savers are now registered as ordinary `IOBlock` subclasses through
`scieasy.blocks`):

| Group | Purpose | Return type |
|-------|---------|-------------|
| `scieasy.blocks` | Block class discovery (including plugin-owned `IOBlock` subclasses such as `LoadSRSImage`) | `(PackageInfo, list[type[Block]])` or `list[type[Block]]` |
| `scieasy.types` | Custom DataObject subtype registration | `list[type[DataObject]]` |

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
from scieasy.utils.constraints import has_axes

# Plugin-provided type — not in core (ADR-027 D2).
# Requires `pip install scieasy-blocks-imaging`.
from scieasy_blocks_imaging.types import Image


class GaussianBlurBlock(ProcessBlock):
    name: ClassVar[str] = "Gaussian Blur"
    description: ClassVar[str] = "Apply Gaussian blur to images"
    algorithm: ClassVar[str] = "gaussian_blur"

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="images",
            accepted_types=[Image],
            constraint=has_axes("y", "x"),
            description="Input images (must have spatial y, x axes)",
        ),
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

    def process_item(self, item: Image, config: BlockConfig, state=None) -> Image:
        from scipy.ndimage import gaussian_filter
        from scieasy.utils.axis_iter import iterate_over_axes

        sigma = config.get("sigma", 1.0)

        # iterate_over_axes handles 5D/6D inputs by looping over extra
        # dimensions and calling the func on each (y, x) slice. Metadata
        # and axes are preserved automatically (ADR-027 D3, D4).
        def _blur_slice(slice_2d, coord):
            return gaussian_filter(slice_2d, sigma=sigma)

        return iterate_over_axes(item, operates_on={"y", "x"}, func=_blur_slice)
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

**Purpose**: Data ingress (loading files) and egress (saving files). `IOBlock`
is an **abstract base class** (ADR-028 §D2). Concrete IO blocks subclass it and
implement either `load()` (input-only) or `save()` (output-only). The previous
"single block type with a `direction` flag plus a `FormatAdapter` registry"
pattern is gone — there is no `scieasy.blocks.io.adapters` package and no
`scieasy.adapters` entry-point group.

**Module**: `scieasy.blocks.io.io_block`

**Abstract methods** (subclasses must implement at least one):

| Method | Signature | When to implement |
|--------|-----------|-------------------|
| `load` | `load(self, config: BlockConfig) -> DataObject` | Input-only blocks (`direction = "input"`) |
| `save` | `save(self, obj: DataObject, config: BlockConfig) -> None` | Output-only blocks (`direction = "output"`) |

**Special ClassVars**:

| ClassVar | Type | Default | Purpose |
|----------|------|---------|---------|
| `direction` | `ClassVar[str]` | `"input"` | `"input"` to load, `"output"` to save. Drives the default `run()` dispatch. |

**How it works**: The default `run()` method on `IOBlock` reads `direction` and
dispatches to either `load()` or `save()`. Concrete subclasses do not need to
override `run()` themselves. For one-class-many-types loaders that want a single
block with type-narrowing output ports based on user config, see
[Writing a dynamic-port block](#writing-a-dynamic-port-block) below.

**Example: Minimal custom IOBlock subclass (single concrete output type)**

```python
from typing import ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import OutputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.array import Array


class TiffLoaderBlock(IOBlock):
    name: ClassVar[str] = "TIFF Loader"
    description: ClassVar[str] = "Load a TIFF image file as an Array"
    direction: ClassVar[str] = "input"
    category: ClassVar[str] = "io"

    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="data", accepted_types=[Array]),
    ]

    def load(self, config: BlockConfig) -> Array:
        import tifffile
        path = config["path"]
        data = tifffile.imread(path)
        return Array(data=data, axes=("y", "x"))
```

This example uses a fixed `Array` output type. For dynamic-port blocks (one
class, multiple effective output types based on config), see
[Writing a dynamic-port block](#writing-a-dynamic-port-block).

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

#### 3.4.1 Writing a manual review step using AppBlock to open Fiji

SciEasy treats human review as a first-class workflow step (see
`CLAUDE.md` §2.5). There is **no dedicated manual-review block class** —
the same `AppBlock` machinery that bridges automated GUI tools also
covers the human-in-the-loop case. The trick is that the user *is* the
external process: the block writes inputs to an exchange directory,
launches the GUI, then sits in `PAUSED` until the user saves a result
file matching `output_patterns`.

The lifecycle is identical to any other `AppBlock`:

1. **PREPARE** — `FileExchangeBridge.prepare()` writes input
   `DataObject`s to `exchange_dir/inputs/` in the app's native format.
2. **LAUNCH** — the configured `app_command` starts the GUI tool with
   the input directory as an argument.
3. **PAUSED** — the engine transitions to `PAUSED`. The frontend shows
   "Waiting for manual review…". The user opens the file, edits or
   annotates, and saves into `exchange_dir/outputs/`.
4. **WATCH** — `FileWatcher` polls `exchange_dir/outputs/` for files
   matching `output_patterns` (with `stability_period` so partial writes
   are not picked up).
5. **RESUME** — once outputs appear, the bridge collects them, wraps
   them as `Artifact` instances inside a `Collection`, and the block
   transitions to `DONE`.

A minimal manual-review block that opens Fiji for cell annotation:

```python
"""manual_fiji_review.py — pause the workflow for human annotation in Fiji."""

from typing import ClassVar

from scieasy.blocks.app.app_block import AppBlock
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.blocks.base.state import ExecutionMode
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.base import DataObject


class ManualFijiReview(AppBlock):
    """Open an Image in Fiji and wait for the user to save an annotated copy."""

    name: ClassVar[str] = "Manual Fiji Review"
    description: ClassVar[str] = (
        "Pauses the workflow, opens the input image in Fiji, "
        "and resumes once the user saves an annotated TIFF."
    )
    version: ClassVar[str] = "0.1.0"

    # Canonical AppBlock ClassVars (see scieasy.blocks.app.app_block.AppBlock).
    app_command: ClassVar[str] = "fiji"
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.EXTERNAL
    output_patterns: ClassVar[list[str]] = ["*_reviewed.tif", "*_reviewed.tiff"]
    watch_timeout: ClassVar[int] = 1800  # 30 minutes — humans take coffee breaks

    input_ports: ClassVar[list[InputPort]] = [
        InputPort(
            name="image",
            accepted_types=[DataObject],
            required=True,
            description="Image to review in Fiji",
        ),
    ]
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(
            name="reviewed",
            accepted_types=[Artifact],
            description="Annotated image saved by the user",
        ),
    ]

    # No run() override needed — AppBlock.run() handles the
    # PREPARE → LAUNCH → PAUSED → WATCH → RESUME lifecycle for us.
```

A few notes on tuning this for real manual-review use:

- **`watch_timeout`** should be generous (minutes to hours). Manual
  review is slow; a 5-minute timeout will fail every real workflow.
- **`output_patterns`** must be specific enough to ignore Fiji's
  scratch files (`*.tmp`, `Thumbs.db`, etc.). Prefer a suffix
  convention such as `*_reviewed.tif` so the user's intent to "submit"
  is explicit.
- **`done_marker`** (passed via `BlockConfig`) is supported when the
  pattern alone is ambiguous: the user creates an empty `.done` file
  to signal "I am finished", and the watcher only collects outputs
  once the marker exists.
- **Cancellation**: if the user closes Fiji without saving any output
  matching `output_patterns`, `AppBlock.run()` catches
  `ProcessExitedWithoutOutputError` and transitions to `CANCELLED`
  rather than hanging forever.

The real-world implementation lives in the imaging plugin under
ticket **T-IMG-034 (`FijiBlock`)** in
`docs/specs/phase11-implementation-standards.md` — that block adds
ROI/overlay handling and a configurable Fiji macro launch path on top
of the same `AppBlock` foundation shown here.

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

### 3.6 Writing a dynamic-port block

Most blocks declare their input and output ports as static `ClassVar` lists at
class definition time. A `ProcessBlock` that "takes a `DataFrame` and returns a
`DataFrame`" looks the same to the validator and to the GUI palette no matter
what the user types into its config panel.

**Dynamic-port blocks break that assumption.** A dynamic-port block has *one*
class but exposes *different effective port types* depending on a user-selected
config enum. The canonical example is core's `LoadData` (ADR-028 Addendum 1
§C5 / §C9): one block class loads any of the six core `DataObject` types
(`Array`, `DataFrame`, `Series`, `Text`, `Artifact`, `CompositeData`), and the
output port colour in the GUI palette tracks the user's `core_type` selection
live. If the user picks `"DataFrame"`, the output port advertises
`accepted_types=[DataFrame]` and only connects to downstream blocks that accept
`DataFrame`; if they switch to `"Array"`, the same port instantly narrows to
`accepted_types=[Array]`.

**Why dynamic ports exist**. Without this hook, an author of a "load any core
type" block has two bad options:

1. Declare `accepted_types=[DataObject]` on the static port. The validator
   accepts every downstream connection, even ones that will fail at runtime.
2. Ship six separate classes (`LoadArray`, `LoadDataFrame`, …). The palette
   becomes cluttered and the dispatch logic is duplicated six times.

The dynamic-port mechanism gives a third option: **one class, one static port
declaration with the broad `[DataObject]` upper bound, plus a per-instance
override that reports the *narrowed* type for the configured enum value.** The
runtime validator, the worker subprocess, and the frontend `BlockNode` all
consume `get_effective_*_ports()` rather than the static class-level lists, so
type narrowing flows through the entire stack consistently.

#### The two-part contract

A dynamic-port block declares two things:

1. **`dynamic_ports: ClassVar[dict[str, Any] | None]`** — a static descriptor
   that the API and the frontend consume to render the enum-driven port-colour
   UI. The format is intentionally narrow (no expressions, no mini-DSL):

   ```python
   dynamic_ports: ClassVar[dict[str, Any] | None] = {
       "source_config_key": "core_type",
       "output_port_mapping": {
           "data": {
               "Array": ["Array"],
               "DataFrame": ["DataFrame"],
               # ... one entry per enum value
           },
       },
       # Optional: same shape as output_port_mapping, for input narrowing
       # "input_port_mapping": { ... },
   }
   ```

   `source_config_key` names the config field whose enum value drives the
   narrowing. `output_port_mapping[port_name][enum_value]` is a list of *type
   names* (strings) that the frontend resolves through `TypeRegistry`.

2. **`get_effective_input_ports()` / `get_effective_output_ports()`** — a
   per-instance override that reads `self.config[source_config_key]` and
   returns a fresh list of `InputPort` / `OutputPort` instances with
   `accepted_types` narrowed to the resolved Python type. The runtime validator
   calls this method, not the static `output_ports` ClassVar.

The static class-level `output_ports` (or `input_ports`) declaration uses the
broad upper bound (`[DataObject]`) so registration still succeeds for clients
that don't know about the dynamic hook.

#### Worked example: the `LoadData` core block

The class body below is the canonical implementation that ships in core at
`src/scieasy/blocks/io/loaders/load_data.py`. Read it top-to-bottom — every
piece of the dynamic-port pattern is present.

```python
from typing import Any, ClassVar

from scieasy.blocks.base.config import BlockConfig
from scieasy.blocks.base.ports import OutputPort
from scieasy.blocks.io.io_block import IOBlock
from scieasy.core.types.array import Array
from scieasy.core.types.artifact import Artifact
from scieasy.core.types.base import DataObject
from scieasy.core.types.composite import CompositeData
from scieasy.core.types.dataframe import DataFrame
from scieasy.core.types.series import Series
from scieasy.core.types.text import Text


# Module-level enum-to-type table. Hardcoded per ADR-028 Addendum 1 §C5
# (no entry-point lookup, no runtime registration — the six core types
# are stable and the table is small enough to read at a glance).
_CORE_TYPE_MAP: dict[str, type[DataObject]] = {
    "Array": Array,
    "DataFrame": DataFrame,
    "Series": Series,
    "Text": Text,
    "Artifact": Artifact,
    "CompositeData": CompositeData,
}


class LoadData(IOBlock):
    """One IOBlock subclass that loads any of the six core DataObject types.

    The output port `data` advertises `[DataObject]` statically (for
    backward-compatible registration) but its effective `accepted_types`
    are narrowed per-instance via `get_effective_output_ports()`.
    """

    direction: ClassVar[str] = "input"
    name: ClassVar[str] = "Load Data"
    category: ClassVar[str] = "io"

    # Static (broad) port declaration — what the registry sees at class
    # definition time. The narrowed per-instance list comes from
    # get_effective_output_ports() below.
    output_ports: ClassVar[list[OutputPort]] = [
        OutputPort(name="data", accepted_types=[DataObject]),
    ]

    # The dynamic-ports descriptor. The frontend `BlockNode` and the
    # backend validator both consume this declaratively to render the
    # enum-driven port colour and to validate connections live as the
    # user edits the config panel.
    dynamic_ports: ClassVar[dict[str, Any] | None] = {
        "source_config_key": "core_type",
        "output_port_mapping": {
            "data": {
                "Array": ["Array"],
                "DataFrame": ["DataFrame"],
                "Series": ["Series"],
                "Text": ["Text"],
                "Artifact": ["Artifact"],
                "CompositeData": ["CompositeData"],
            },
        },
    }

    config_schema: ClassVar[dict[str, Any]] = {
        "type": "object",
        "properties": {
            "core_type": {
                "type": "string",
                "enum": list(_CORE_TYPE_MAP.keys()),
                "default": "DataFrame",
                "ui_priority": 0,
            },
            "path": {"type": "string", "ui_priority": 1},
        },
        "required": ["core_type", "path"],
    }

    def get_effective_output_ports(self) -> list[OutputPort]:
        """Return the per-instance output port for the configured core_type.

        Reads ``self.config["core_type"]`` (defaulting to ``"DataFrame"``)
        and returns a single ``OutputPort`` whose ``accepted_types`` is the
        resolved Python class. Unknown enum values fall back to ``DataFrame``
        so the validator never sees a malformed port; the run-time
        ``load()`` call still raises ``ValueError`` on unknown values, so
        the frontend can show the error path.
        """
        type_name = self.config.get("core_type", "DataFrame")
        cls = _CORE_TYPE_MAP.get(type_name, DataFrame)
        return [OutputPort(name="data", accepted_types=[cls])]

    def load(self, config: BlockConfig) -> DataObject:
        """Dispatch to one of the six private _load_* functions.

        Per ADR-028 Addendum 1 §C9 the dispatch table is hardcoded and the
        helper functions are module-level private functions, not helper
        classes. Unknown enum values raise ValueError rather than silently
        picking a default.
        """
        type_name = config.get("core_type", "DataFrame")
        if type_name not in _CORE_TYPE_MAP:
            raise ValueError(f"Unknown core_type: {type_name}")
        # _load_array / _load_dataframe / etc. are module-level private
        # functions in load_data.py — see the source for the full list.
        return _DISPATCH[type_name](config)
```

Read the live source at `src/scieasy/blocks/io/loaders/load_data.py` for the
six private `_load_*` functions, the pickle-opt-in `allow_pickle` flag, and the
matching `SaveData` mirror at `src/scieasy/blocks/io/savers/save_data.py`.

#### What dynamic ports do *not* cover

The dynamic-port mechanism narrows the **type** of an existing static port. It
does **not** add or remove ports based on config — `LoadData` always has
exactly one output port named `data`. For variadic *port count* (e.g., a
"merge N inputs" block where the number of input ports is itself a config
field), see **ADR-029** (currently draft, deferred from Phase 11). Until
ADR-029 lands, blocks that need variadic counts should declare a fixed
upper bound and accept `Optional` for the unused slots.

#### Pointers

- **ADR-028 Addendum 1 §C5** — the `dynamic_ports` descriptor format and the
  enum-only design rationale (why no expressions, no mini-DSL).
- **ADR-028 Addendum 1 §C9** — the "private module-level dispatch functions
  instead of helper classes" rule that `LoadData.load()` follows.
- **ADR-028 Addendum 1 §B** — the GUI consequences (live port-colour updates
  in `BlockNode.tsx` via `computeEffectivePorts`).
- **`docs/specs/phase11-implementation-standards.md` T-TRK-007** — the LoadData
  ticket that produced the canonical implementation.
- **ADR-029** (draft, deferred) — variadic port count mechanism for the merge /
  fan-in case.

---

## 4. Data Transport with Collection

### What is a Collection?

`Collection` is the standard transport wrapper for data flowing between blocks.
It is a **homogeneous, ordered list of `DataObject` instances** with a declared
`item_type`.

```python
from scieasy.core.types.collection import Collection
# Plugin-provided type (ADR-027 D2 — Image is not in core):
from scieasy_blocks_imaging.types import Image

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
from scieasy_blocks_imaging.types import Image

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
from scieasy_blocks_imaging.types import Image

results = [
    Image(axes=["y", "x"], shape=arr1.shape, dtype=arr1.dtype),
    Image(axes=["y", "x"], shape=arr2.shape, dtype=arr2.dtype),
]
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
# Assumes `from scieasy_blocks_imaging.types import Image` at the top.

def blur(image: Image) -> Image:
    from scipy.ndimage import gaussian_filter
    data = image.view().to_memory()
    result = gaussian_filter(data, sigma=1.0)
    return Image(
        axes=image.axes, shape=result.shape, dtype=result.dtype,
        meta=image.meta,   # inherit domain metadata (ADR-027 D5)
    )

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
from scieasy_blocks_imaging.types import Image

def process_item(self, item: Image, config: BlockConfig, state=None) -> Image:
    data = item.view().to_memory()
    result = my_transform(data)
    return Image(
        axes=item.axes, shape=result.shape, dtype=result.dtype,
        meta=item.meta,   # domain metadata inheritance
    )
```

The `ProcessBlock.run()` default implementation does the following automatically:

1. Calls `self.setup(config)` once (see next subsection).
2. Takes the first (primary) input Collection.
3. Iterates each item.
4. Calls `self.process_item(item, config, state)` for each.
5. Auto-flushes each result to storage.
6. Packs all results into an output Collection on the first output port.
7. Calls `self.teardown(state)` in a `finally` block.

### Setup and teardown hooks (ADR-027 D7)

For blocks with expensive one-time initialisation — loading an ML model, opening
a database connection, compiling a regex cache — override `setup(config)` and
`teardown(state)`. The returned `state` is passed to every `process_item` call
during this `run()`, and `teardown` runs in a `finally` block so cleanup always
happens.

```python
from scieasy.blocks.process.process_block import ProcessBlock
from scieasy.blocks.base.ports import InputPort, OutputPort
from scieasy.engine.resources import ResourceRequest
from scieasy.utils.constraints import has_axes
from scieasy_blocks_imaging.types import Image


class CellposeSegment(ProcessBlock):
    name = "Cellpose Segment"
    input_ports  = [InputPort(name="images", accepted_types=[Image],
                              constraint=has_axes("y", "x"))]
    output_ports = [OutputPort(name="masks", accepted_types=[Image])]
    resource_request = ResourceRequest(
        requires_gpu=True, gpu_memory_gb=4.0, cpu_cores=2,
    )

    def setup(self, config):
        """Load the cellpose model once per run."""
        from cellpose import models
        return models.Cellpose(
            model_type=config.get("model", "cyto2"),
            gpu=True,
        )

    def process_item(self, item: Image, config, state):
        """Segment one image; reuse the loaded model."""
        img_2d = item.to_memory()
        masks, _, _, _ = state.eval(img_2d, diameter=config.get("diameter", 30))
        return Image(
            axes=item.axes, shape=masks.shape, dtype=masks.dtype,
            meta=item.meta,
        )

    def teardown(self, state):
        """Release GPU resources."""
        import torch
        torch.cuda.empty_cache()
```

Rules:

- `setup` receives **only** `config`. It does not see the input Collection. Data-
  driven initialisation (e.g. "pick the model based on the first image's modality")
  belongs inside `process_item` with lazy caching on the `state` object.
- `setup` runs **inside the worker subprocess** (ADR-017), after `TypeRegistry.scan()`
  has loaded plugin types. It is safe to `import cellpose`, `torch`, etc.
- `teardown` runs in a `finally` block even when `process_item` raises. Put GPU
  cleanup, file closes, DB disconnects here.
- Blocks that do not need expensive setup ignore the hooks entirely — the defaults
  are no-ops. Existing 2-arg `process_item(self, item, config)` overrides continue
  to work because the new `state` parameter defaults to `None`.

### Working with `item.meta` — domain metadata (ADR-027 D5)

Every `DataObject` carries stratified metadata in three slots:

- `framework: FrameworkMeta` — framework-managed (created_at, object_id, source,
  derived_from parent). Read-only from block authors.
- `meta: BaseModel` — **typed Pydantic model** declared per subtype. This is where
  domain metadata lives: pixel size, channel list, acquisition date, objective,
  instrument. The exact fields depend on the subtype.
- `user: dict[str, Any]` — free-form escape hatch. Framework never interprets
  these fields.

Reading is a simple typed attribute access:

```python
from scieasy.core.units import PhysicalQuantity as Q

def process_item(self, item: FluorImage, config, state=None) -> FluorImage:
    # Typed access — IDE autocomplete, Pydantic validation already done.
    if item.meta.pixel_size < Q(0.2, "um"):
        # super-resolution path
        ...

    for channel in item.meta.channels:
        print(channel.name, channel.excitation_nm, channel.emission_nm)
    ...
```

Writing uses the immutable `with_meta` helper. The returned object is a new
instance; the original is unchanged:

```python
# Change pixel size after resampling.
resampled = item.with_meta(pixel_size=Q(0.216, "um"))

# Drop channels not selected by the user.
selected_names = config.get("channels", [])
filtered = item.with_meta(
    channels=[c for c in item.meta.channels if c.name in selected_names],
)
```

**Automatic inheritance**: most blocks do not need to touch `meta` at all. The
`iterate_over_axes` utility and the default `ProcessBlock.run()` loop preserve
`meta` across iterations by reference. If a block's output has the same metadata
as its input, just pass `meta=item.meta` into the new instance constructor.

**Backward compatibility shim**: the old `DataObject.metadata` dict is still
accessible as a property that returns `self.user` with a `DeprecationWarning`.
It is removed after Phase 11. Migrate to `item.meta.<field>` and `item.with_meta()`.

### Parallelising over a Collection — L2 fan-out pattern (ADR-027 D9, D13)

SciEasy's recommended way to parallelise a block across N workers is **not** to
spawn threads or process pools inside the block. Instead, use the workflow graph
to fan out the Collection across N separate block instances via the built-in
`SplitCollection` and `MergeCollection` blocks. Each branch is a separate
subprocess under `ProcessRegistry` supervision, acquires its own GPU slot from
`ResourceManager`, and participates in DAG-level cancellation (ADR-018).

```
[LoadImages]
    └─ Collection[Image] length=100
[SplitCollection n_parts=4]
    ├─ out_0 → [Cellpose A] ─┐
    ├─ out_1 → [Cellpose B] ─┤
    ├─ out_2 → [Cellpose C] ─┤
    └─ out_3 → [Cellpose D] ─┤
                             ↓
                    [MergeCollection]
```

Workflow YAML:

```yaml
nodes:
  - id: split
    block_type: SplitCollection
    config: {n_parts: 4}
  - id: seg_0
    block_type: CellposeSegment
    config: {model: cyto2, diameter: 30}
  - id: seg_1
    block_type: CellposeSegment
    config: {model: cyto2, diameter: 30}
  - id: seg_2
    block_type: CellposeSegment
    config: {model: cyto2, diameter: 30}
  - id: seg_3
    block_type: CellposeSegment
    config: {model: cyto2, diameter: 30}
  - id: merge
    block_type: MergeCollection
    config: {}
edges:
  - {source: "split:output_0", target: "seg_0:images"}
  - {source: "split:output_1", target: "seg_1:images"}
  - {source: "split:output_2", target: "seg_2:images"}
  - {source: "split:output_3", target: "seg_3:images"}
  - {source: "seg_0:masks",    target: "merge:input_0"}
  - {source: "seg_1:masks",    target: "merge:input_1"}
  - {source: "seg_2:masks",    target: "merge:input_2"}
  - {source: "seg_3:masks",    target: "merge:input_3"}
```

With the scheduler concurrency fix from ADR-018 Addendum 1, the four Cellpose
branches dispatch concurrently. `ResourceManager` gates dispatch by GPU slot
count — if the user has one GPU, branches run sequentially; if they have four
GPUs, all four run in parallel.

**Why not block-internal parallelism?** L2 fan-out scales across multiple GPUs
and (future) multiple machines; block-internal ThreadPool does not. L2 fan-out
respects `ResourceManager` gating; block-internal pools do not. L2 fan-out gives
you DAG-level cancellation for free; block-internal pools require manual cleanup
on cancel. Threads and process pools inside a block are still *allowed* as an
escape hatch (see Thread policy below), but they are not the recommended path.

**Library-native parallelism is fine**: if your library (cellpose, torch,
tensorflow) has its own batched execution API, use it directly in `run()`. For
example, cellpose's `model.eval([img1, img2, ...], batch_size=N)` uses GPU
batching internally and is the best way to saturate a single GPU. Override `run()`
in Tier 2 style and feed the whole Collection to the library's batch method.

### Thread policy inside blocks (ADR-027 D8)

Block authors **may** use `threading.Thread`, `concurrent.futures.ThreadPoolExecutor`,
or any other thread-based concurrency inside their own `run()`. The core runtime
(scheduler, ResourceManager, ProcessRegistry, event bus) does NOT use threads.

**When threads work**:

- The library releases the GIL: numpy, scipy, torch, cellpose, and most C-extension
  scientific libraries. Threads give real parallelism for these workloads.
- The work is I/O-bound: file reads, network calls, subprocess waits.

**When threads do not work**:

- Pure-Python CPU-bound code. The GIL serialises execution; threads add overhead
  without speedup.
- You need sub-second cooperative cancellation. Python threads cannot be interrupted
  mid-function — if your thread is 30 seconds into `cellpose.eval`, nothing short
  of killing the whole subprocess will stop it.

**Cancellation guarantees**:

- A block's worker subprocess is **killable as a unit**. `ProcessHandle.terminate()`
  sends SIGTERM (with grace period) followed by SIGKILL. All threads in the
  subprocess die with it because process death releases all OS resources.
- The framework does NOT provide a cooperative cancel token at the thread level.
  If you need cancellation, rely on subprocess-level kill.

**Declare your internal parallelism**: if a block uses a thread pool with N workers,
set `max_internal_workers` on its `ResourceRequest` so the scheduler accounts
for the actual CPU usage:

```python
class MyBlock(ProcessBlock):
    resource_request = ResourceRequest(
        cpu_cores=2,
        max_internal_workers=4,   # ADR-027 D8: 2 × 4 = 8 CPU slots
    )
```

`ResourceManager` uses `effective_cpu = cpu_cores * max_internal_workers` to gate
dispatch. This prevents accidentally oversubscribing the CPU pool when many blocks
each spawn their own pools.

**In summary**: prefer L2 fan-out for Collection parallelism; use library-native
batched APIs for single-node parallelism; use threads only when the library
releases the GIL and you understand the cancellation trade-offs. Never use
threads in core runtime code.

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
from scieasy.core.types.array import Array
from scieasy.core.types.collection import Collection

def test_doubler_block():
    block = DoublerBlock()
    data = np.ones((100, 100))
    # Use the core Array directly when writing generic tests. If the block
    # is imaging-specific, import the plugin type instead:
    #     from scieasy_blocks_imaging.types import Image
    arr = Array(axes=["y", "x"], shape=data.shape, dtype=data.dtype)
    inputs = {"data": Collection([arr], item_type=Array)}
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

External developers define domain-specific types by subclassing **core** types
(`Array`, `Series`, `DataFrame`, `Text`, `Artifact`, `CompositeData`). **Core
ships no domain subtypes** (ADR-027 D2) — every `Image`, `Spectrum`, `PeakTable`,
`AnnData`, etc. is provided by a plugin package. If you are writing an imaging
block, your custom type goes in your own plugin package alongside your blocks,
not in the core repo.

Two levels of subclassing: intermediate "modality" types that live at the top
of a plugin package, and further specialisations within that package.

```python
# In scieasy-blocks-imaging/src/scieasy_blocks_imaging/types/image.py
from typing import ClassVar
from pydantic import BaseModel
from scieasy.core.types.array import Array
from scieasy.core.units import PhysicalQuantity


class ChannelInfo(BaseModel):
    name: str
    dye: str | None = None
    excitation_nm: float | None = None
    emission_nm: float | None = None


class Image(Array):
    """Generic spatial image. Base for plugin-specific imaging types."""
    required_axes:   ClassVar[frozenset[str]] = frozenset({"y", "x"})
    allowed_axes:    ClassVar[frozenset[str]] = frozenset(
        {"t", "z", "c", "lambda", "y", "x"}
    )
    canonical_order: ClassVar[tuple[str, ...]] = ("t", "z", "c", "lambda", "y", "x")

    class Meta(BaseModel):
        """Domain metadata — override per subtype."""
        pixel_size: PhysicalQuantity | None = None

    meta: "Image.Meta"


class FluorImage(Image):
    """Multichannel fluorescence image — channel axis mandatory."""
    required_axes = frozenset({"y", "x", "c"})

    class Meta(Image.Meta):
        channels: list[ChannelInfo] = []
        objective: str | None = None
        acquisition_date: str | None = None

    meta: "FluorImage.Meta"


class SRSImage(Image):
    """SRS microscopy image with spectral wavenumber axis."""
    required_axes = frozenset({"y", "x", "lambda"})

    class Meta(Image.Meta):
        excitation_wavelength_nm: float | None = None
        wavenumber_range_cm_1: tuple[float, float] | None = None

    meta: "SRSImage.Meta"
```

**Subclassing rules**:

- Inherit from the nearest core type (`Array`, `DataFrame`, `Text`, etc.).
  **Do not inherit from anything in `scieasy.core.types.array` that isn't
  `Array` itself** — there is nothing else there (ADR-027 D2).
- Storage backend is determined by the base type (`SRSImage` inherits `Array`'s
  Zarr backend) — no custom storage needed.
- `axes` is **instance-level** (ADR-027 D1). At class level you declare
  `required_axes`, `allowed_axes`, and `canonical_order` constraints only.
  The base `Array.__init__` validates the passed-in `axes` against these.
- Domain metadata goes in a nested `Meta` Pydantic `BaseModel` on the class
  (ADR-027 D5). Override the parent's `Meta` to add more fields. Block authors
  read via `img.meta.field` and write via `img.with_meta(field=new_value)`.
- Maximum inheritance depth: 3 levels from `DataObject` (e.g.,
  `DataObject → Array → Image → SRSImage`).

**Port type matching**: Uses `isinstance` + `TypeSignature` inheritance walk,
so `SRSImage` auto-matches ports expecting `Image` or `Array`. A port expecting
`SRSImage` will NOT accept a plain `Image`. For axis-level constraints use
`has_axes(...)` from `scieasy.utils.constraints`.

**Registration**: Custom types are registered via the `scieasy.types`
entry-point group (ADR-025 callable protocol):

```python
# In scieasy-blocks-imaging/src/scieasy_blocks_imaging/types/__init__.py
def get_types():
    from .image import Image, FluorImage, SRSImage, HyperspectralImage
    return [Image, FluorImage, SRSImage, HyperspectralImage]
```

```toml
# In scieasy-blocks-imaging/pyproject.toml
[project.entry-points."scieasy.types"]
imaging = "scieasy_blocks_imaging.types:get_types"
```

After `pip install scieasy-blocks-imaging`, the core `TypeRegistry` picks these
types up automatically. The worker subprocess (ADR-027 D11) also scans the same
entry points so `Image`, `FluorImage`, etc. are resolvable when reconstructing
inputs from serialised `type_chain` metadata.

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
