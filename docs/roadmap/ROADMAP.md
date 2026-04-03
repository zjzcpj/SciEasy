# SciEasy — Roadmap

> **Guiding rule**: each milestone produces something testable. No milestone is
> "write a bunch of code and hope it works at the end." Every phase ends with
> a green CI.

---

## Phase 0 — Repository bootstrap

**Goal**: a clean repo that anyone can clone, install, and run an empty test suite against.

### 0.1 Project scaffolding

- [ ] Create `pyproject.toml` with package metadata, dependencies, and `[project.scripts]` entry
- [ ] Create `src/scieasy/__init__.py` with version string
- [ ] Create every directory and `__init__.py` listed in `docs/PROJECT_TREE.md` — no classes, just empty files with module docstrings explaining purpose
- [ ] Create `frontend/package.json` with React + ReactFlow + TypeScript + Tailwind dependencies (no components yet)
- [ ] Create `tests/conftest.py` with a placeholder fixture
- [ ] Copy `docs/ARCHITECTURE.md`, `docs/ADR.md`, `docs/PROJECT_TREE.md` into repo

### 0.2 Tooling configuration

- [ ] Configure `ruff` in `pyproject.toml` (linting + formatting rules)
- [ ] Configure `mypy` in `pyproject.toml` (strict mode on `src/scieasy/`)
- [ ] Configure `pytest` in `pyproject.toml` (test paths, markers)
- [ ] Create `.pre-commit-config.yaml` (ruff + mypy on staged files)
- [ ] Create `Makefile` with shortcuts: `make lint`, `make typecheck`, `make test`, `make serve`

### 0.3 CI pipeline

- [ ] Create `.github/workflows/ci.yml`:
  - ruff check
  - mypy check
  - pytest (empty suite should pass)
- [ ] Verify: push to GitHub → CI green ✅

### Deliverable

```
git clone → pip install -e ".[dev]" → make lint → make typecheck → make test
All green. Zero implementation, zero failures.
```

---

## Phase 1 — Interface skeleton

**Goal**: every ABC, Protocol, Enum, and Pydantic model exists with complete type hints and docstrings. All method bodies are `raise NotImplementedError`. The codebase is a **compilable, type-checkable spec** that Claude can inherit from without reading docs.

### 1.1 Core type hierarchy

- [ ] `core/types/base.py` — `DataObject` ABC, `TypeSignature`, `StorageReference`
- [ ] `core/types/array.py` — `Array(DataObject)` with `axes`, `shape`, `ndim`, `dtype`, `chunk_shape`
- [ ] `core/types/series.py` — `Series(DataObject)` with `index_name`, `value_name`, `length`
- [ ] `core/types/dataframe.py` — `DataFrame(DataObject)` with `columns`, `row_count`, `schema`
- [ ] `core/types/text.py` — `Text(DataObject)`with content, format, encoding
- [ ] `core/types/artifact.py` — `Artifact(DataObject)`with file_path, mime_type, description
- [ ] `core/types/composite.py` — `CompositeData(DataObject)` with `slots`, `get()`, `set()`, `slot_types()`
- [ ] `core/types/registry.py` — `TypeRegistry` class with `register()`, `resolve()`, `all_types()` signatures
- [ ] Domain types as one-liner subclasses: `Image(Array)`, `Spectrum(Series)`, `PeakTable(DataFrame)`, `MSImage(Array)`, `AnnData(CompositeData)`, etc.

### 1.2 Storage and proxy interfaces

- [ ] `core/storage/base.py` — `StorageBackend` Protocol (read, write, slice, iter_chunks, metadata)
- [ ] `core/storage/ref.py` — `StorageReference` dataclass
- [ ] `core/storage/zarr_backend.py` — class signature only, all methods `NotImplementedError`
- [ ] `core/storage/arrow_backend.py` — class signature only
- [ ] `core/storage/filesystem.py` — class signature only
- [ ] `core/storage/composite_store.py` — class signature only
- [ ] `core/proxy.py` — `ViewProxy` with `slice()`, `iter_chunks()`, `to_memory()`, `shape`, `axes`

### 1.3 Lineage interfaces

- [ ] `core/lineage/record.py` — `LineageRecord` dataclass, `EnvironmentSnapshot` dataclass
- [ ] `core/lineage/environment.py` — `EnvironmentSnapshot` with `capture()` classmethod
- [ ] `core/lineage/store.py` — `LineageStore` with `write()`, `query()`, `ancestors()` signatures
- [ ] `core/lineage/graph.py` — `ProvenanceGraph` signatures

### 1.4 Block system interfaces

- [ ] `blocks/base/state.py` — `BlockState`, `ExecutionMode`, `BatchMode`, `InputDelivery`, `BatchErrorStrategy` enums
- [ ] `blocks/base/ports.py` — `Port`, `InputPort`, `OutputPort` dataclasses with `accepted_types`, `constraint`
- [ ] `blocks/base/config.py` — `BlockConfig` Pydantic model
- [ ] `blocks/base/result.py` — `BlockResult`, `BatchResult` dataclasses
- [ ] `blocks/base/block.py` — `Block` ABC with `validate()`, `run()`, `postprocess()`, class-level declarations
- [ ] `blocks/io/io_block.py` — `IOBlock(Block)` with `direction` field
- [ ] `blocks/process/process_block.py` — `ProcessBlock(Block)`
- [ ] `blocks/code/code_block.py` — `CodeBlock(Block)` with `InputDelivery` handling signatures
- [ ] `blocks/app/app_block.py` — `AppBlock(Block)` with bridge protocol signatures
- [ ] `blocks/ai/ai_block.py` — `AIBlock(Block)`
- [ ] `blocks/subworkflow/subworkflow_block.py` — `SubWorkflowBlock(Block)`
- [ ] `blocks/registry.py` — `BlockSpec` dataclass, `BlockRegistry` with `scan()`, `instantiate()`, `hot_reload()`, `all_specs()`

### 1.5 Format adapter and code runner interfaces

- [ ] `blocks/io/adapters/base.py` — `FormatAdapter` Protocol (read → DataObject, write → file)
- [ ] `blocks/io/adapter_registry.py` — `AdapterRegistry` with `register()`, `get_for_extension()`
- [ ] `blocks/code/runners/base.py` — `CodeRunner` Protocol (execute_inline, execute_script)
- [ ] `blocks/code/runners/runner_registry.py` — `RunnerRegistry`
- [ ] `blocks/code/introspect.py` — `introspect_script()` signature
- [ ] `blocks/app/bridge.py` — `ExternalAppBridge` Protocol
- [ ] `blocks/app/watcher.py` — `FileWatcher` signature

### 1.6 Engine interfaces

- [ ] `engine/dag.py` — `build_dag()`, `topological_sort()` signatures
- [ ] `engine/scheduler.py` — `DAGScheduler` with `execute()`, `pause()`, `resume()` signatures
- [ ] `engine/batch.py` — `BatchExecutor` with serial/parallel/adaptive dispatch signatures
- [ ] `engine/resources.py` — `ResourceRequest` dataclass, `ResourceManager` with `acquire()`, `release()`
- [ ] `engine/runners/base.py` — `BlockRunner` Protocol (run, check_status, cancel)
- [ ] `engine/runners/local.py` — `LocalRunner(BlockRunner)` signature only
- [ ] `engine/checkpoint.py` — `WorkflowCheckpoint` dataclass, `save()`, `load()` signatures
- [ ] `engine/events.py` — `EngineEvent` dataclass, `EventBus` with `emit()`, `subscribe()` signatures

### 1.7 Workflow definition interfaces

- [ ] `workflow/definition.py` — `WorkflowDefinition`, `NodeDef`, `EdgeDef` dataclasses
- [ ] `workflow/serializer.py` — `load_yaml()`, `save_yaml()` signatures
- [ ] `workflow/validator.py` — `validate_workflow()` signature
- [ ] `workflow/layout.py` — `LayoutInfo` dataclass

### 1.8 API interface stubs

- [ ] `api/app.py` — FastAPI app factory (empty, but importable)
- [ ] `api/schemas.py` — Pydantic request/response models for all endpoints
- [ ] `api/routes/workflows.py` — route signatures with `raise NotImplementedError`
- [ ] `api/routes/blocks.py` — route signatures
- [ ] `api/routes/data.py` — route signatures
- [ ] `api/routes/ai.py` — route signatures
- [ ] `api/routes/projects.py` — route signatures
- [ ] `api/ws.py` — WebSocket handler signature
- [ ] `api/sse.py` — SSE handler signature
- [ ] `api/deps.py` — dependency injection stubs

### 1.9 AI service stubs

- [ ] `ai/generation/block_generator.py` — signature only
- [ ] `ai/generation/type_generator.py` — signature only
- [ ] `ai/generation/validator.py` — validation pipeline signature
- [ ] `ai/generation/templates.py` — empty template dict
- [ ] `ai/synthesis/workflow_planner.py` — signature only
- [ ] `ai/optimization/param_optimizer.py` — signature only

### 1.10 Utility stubs

- [ ] `utils/hashing.py` — `content_hash()` signature
- [ ] `utils/wrapping.py` — `wrap_as_dataobject()` signature
- [ ] `utils/broadcast.py` — `broadcast_apply()` signature with full type hints
- [ ] `utils/logging.py` — logging config

### 1.11 CLI stubs

- [ ] `cli/main.py` — Typer app with subcommands: `serve`, `run`, `validate`, `init`, `blocks`. All print "Not implemented yet."

### Verification gate

- [ ] `make typecheck` passes — mypy accepts all type hints, cross-module imports resolve correctly
- [ ] `make lint` passes — ruff clean
- [ ] `make test` passes — empty suite, no import errors
- [ ] `pip install -e .` works — package installs, `scieasy --help` shows CLI stub
- [ ] CI green ✅

### Deliverable

```
Every interface in ARCHITECTURE.md now exists as type-checked Python code.
No business logic. All methods raise NotImplementedError.
Claude can `from scieasy.blocks.base import Block` and get full type hints + autocomplete.
```

---

## Phase 2 — Architecture tests + CI hardening

**Goal**: structural rules from ARCHITECTURE.md and ADR.md become executable tests. From this point forward, any code that violates the architecture gets caught automatically.

### 2.1 Layer dependency tests

- [ ] `tests/architecture/test_layer_deps.py`:
  - `core/` does not import from `blocks/`, `engine/`, `api/`, `ai/`, `workflow/`
  - `blocks/` does not import from `engine/`, `api/`, `ai/`
  - `engine/` does not import from `api/`, `ai/`
  - `api/` does not import from `ai/` (ai is called by api, but api should import ai, not the other way)
  - No circular imports within any layer

### 2.2 Type system structural tests

- [ ] `tests/architecture/test_type_system.py`:
  - Every class in `core/types/` inherits from `DataObject`
  - No class inherits from more than one base type (no multi-inheritance of Array + DataFrame)
  - Every `Array` subclass declares `axes` (not None)
  - Every `CompositeData` subclass declares `expected_slots`
  - `TypeSignature` correctly encodes inheritance chain for all registered types

### 2.3 Block system structural tests

- [ ] `tests/architecture/test_block_system.py`:
  - Every class in `blocks/*/` inherits from exactly one of: IOBlock, ProcessBlock, CodeBlock, AppBlock, AIBlock, SubWorkflowBlock
  - Every block declares at least one output port
  - Every block's `run()` signature matches `(self, inputs: dict[str, ViewProxy], config: BlockConfig) -> dict[str, DataObject]`
  - No block at module level calls `to_memory()` (import-time side effect check)

### 2.4 Registry structural tests

- [ ] `tests/architecture/test_registries.py`:
  - `BlockRegistry` stores `BlockSpec`, never raw class references
  - `TypeRegistry` stores `TypeSpec`, never raw class references
  - All `pyproject.toml` entry_points point to importable classes
  - All entry_point classes pass `issubclass` check against their expected base

### 2.5 Naming and placement tests

- [ ] `tests/architecture/test_placement.py`:
  - No `.py` files in `src/scieasy/` root other than `__init__.py`
  - Every module has a docstring
  - No test files outside of `tests/`
  - Format adapters are in `blocks/io/adapters/` (not scattered elsewhere)
  - Code runners are in `blocks/code/runners/` (not scattered elsewhere)

### 2.6 CI enhancement

- [ ] Add `pytest tests/architecture/` as a dedicated CI step (runs before unit tests)
- [ ] Add badge to README: CI status
- [ ] Confirm: intentionally violating a rule (e.g. `core/` importing `blocks/`) → CI red ❌

### Deliverable

```
Architecture rules are now enforced by machine.
Push code that violates layer boundaries → CI blocks the PR.
Push a Block that doesn't inherit from the five categories → CI blocks the PR.
Push a DataObject subclass without axes → CI blocks the PR.
```

---

## Phase 3 — Core data layer implementation

**Goal**: data types can be created, stored, loaded lazily, and tracked by lineage. No blocks, no engine, no API yet — just the foundation.

### 3.1 DataObject + base types

- [ ] Implement `DataObject` metadata handling, `TypeSignature` auto-generation from class hierarchy
- [ ] Implement `Array`, `Series`, `DataFrame`, `Text`, `Artifact` with their field logic
- [ ] Implement `CompositeData` slot management (get, set, slot_types, validation of expected_slots)
- [ ] Implement `TypeRegistry` — scan, register, isinstance-style matching with inheritance

### 3.2 Storage backends

- [ ] Implement `ZarrBackend` — write Array to Zarr store, read back, slice by chunk
- [ ] Implement `ArrowBackend` — write DataFrame to Parquet, read back, column selection
- [ ] Implement `FilesystemBackend` — write/read Text and Artifact
- [ ] Implement `CompositeStore` — directory of slot backends, manifest JSON

### 3.3 ViewProxy

- [ ] Implement `ViewProxy.slice()` — Zarr chunk-aware partial read
- [ ] Implement `ViewProxy.iter_chunks()` — yield fixed-size chunks
- [ ] Implement `ViewProxy.to_memory()` — full load with size warning
- [ ] Implement `ViewProxy.shape`, `ViewProxy.axes` — metadata without loading

### 3.4 Lineage

- [ ] Implement `LineageStore` — SQLite schema, write record, query by hash
- [ ] Implement `EnvironmentSnapshot.capture()` — read Python version + key packages
- [ ] Implement `ProvenanceGraph.ancestors()` — trace data back through block executions

### 3.5 Broadcast utility

- [ ] Implement `broadcast_apply()` — axis name validation, iter over target axes, call func per slice
- [ ] Implement `iter_axis_slices()` — named-axis-aware slice generator for Array

### 3.6 Tests

- [ ] `tests/core/test_types.py` — create each type, verify TypeSignature, inheritance matching
- [ ] `tests/core/test_composite.py` — slot access, nested composites (SpatialData containing AnnData)
- [ ] `tests/core/test_storage.py` — round-trip write/read for each backend
- [ ] `tests/core/test_proxy.py` — lazy loading verified (no data in memory until .slice() or .to_memory())
- [ ] `tests/core/test_lineage.py` — write record, query, ancestor trace
- [ ] `tests/core/test_broadcast.py` — 2D mask × 3D cube, axis mismatch error

### Deliverable

```python
# This works end-to-end:
img = Image(axes=["y", "x"], storage_ref=zarr_ref)
proxy = img.view()
assert proxy.shape == (1024, 1024)       # no data loaded
chunk = proxy.slice({"y": slice(0, 100)}) # loads 100 rows only
full = proxy.to_memory()                  # loads everything (with warning if >2GB)
```

---

## Phase 4 — Block system implementation

**Goal**: blocks can be instantiated, validated, and executed in isolation (no DAG, no scheduler). Port type checking works. Registry discovers blocks.

### 4.1 Port system

- [ ] Implement port type matching (isinstance-based, inheritance-aware)
- [ ] Implement port constraint validation (call constraint function, report constraint_description on failure)
- [ ] Implement connection validation endpoint (source port → target port compatibility check)

### 4.2 Block lifecycle

- [ ] Implement `Block.__init__`, `BlockConfig` validation, `BlockState` transitions
- [ ] Implement `IOBlock` — load via FormatAdapter, save via FormatAdapter
- [ ] Implement `ProcessBlock` base — pass-through validate/postprocess, subclass implements run
- [ ] Implement 2-3 built-in ProcessBlocks (merge, split) as proof-of-concept

### 4.3 CodeBlock

- [ ] Implement inline mode (MEMORY delivery only)
- [ ] Implement script mode with MEMORY delivery
- [ ] Implement PROXY delivery mode
- [ ] Implement CHUNKED delivery mode with iteration + result concatenation
- [ ] Implement `PythonRunner` (exec for inline, importlib for script)
- [ ] Implement `introspect.py` — parse run() signature, read configure() return value
- [ ] Stub `RRunner` and `JuliaRunner` (just raise NotImplementedError with helpful message)

### 4.4 AppBlock

- [ ] Implement file-exchange bridge — serialise to exchange dir, launch subprocess
- [ ] Implement `FileWatcher` — watchdog-based output detection
- [ ] Implement pause/resume protocol (block state RUNNING → PAUSED → DONE)

### 4.5 SubWorkflowBlock

- [ ] Implement child workflow loading
- [ ] Implement input injection + output extraction mapping
- [ ] (Depends on Phase 5 engine — mark as blocked, use a simple sequential executor stub for now)

### 4.6 Registry

- [ ] Implement `BlockRegistry.scan()` — Tier 1 (directory scan) + Tier 2 (entry_points)
- [ ] Implement `BlockRegistry.instantiate()` — fresh import with mtime-based module name
- [ ] Implement `BlockRegistry.hot_reload()` — re-scan Tier 1 dirs, diff specs
- [ ] Implement `TypeRegistry` with same two-tier scan
- [ ] Implement `AdapterRegistry` — extension → adapter mapping

### 4.7 Format adapters

- [ ] Implement CSV adapter
- [ ] Implement TIFF adapter
- [ ] Implement Parquet adapter
- [ ] Implement generic (binary → Artifact) adapter
- [ ] Stub remaining adapters (mzXML, h5ad, fcs) with NotImplementedError

### 4.8 Tests

- [ ] `tests/blocks/test_ports.py` — type matching, constraint pass/fail, CompositeData slot constraints
- [ ] `tests/blocks/test_io_block.py` — load CSV → DataFrame, save DataFrame → Parquet
- [ ] `tests/blocks/test_process_block.py` — merge two DataFrames
- [ ] `tests/blocks/test_code_block.py` — inline Python, script Python, PROXY mode, CHUNKED mode
- [ ] `tests/blocks/test_app_block.py` — mock subprocess + file watcher (write output file → block resumes)
- [ ] `tests/blocks/test_registry.py` — Tier 1 scan discovers drop-in .py, hot reload picks up changes
- [ ] `tests/blocks/test_subworkflow.py` — stub test with sequential executor

### Deliverable

```python
# This works end-to-end (single block, no DAG):
registry = BlockRegistry()
registry.scan()

block = registry.instantiate("Raman denoise", config={"window": 11})
result = block.run(
    inputs={"spectrum": some_spectrum.view()},
    config=block.config,
)
assert isinstance(result["smoothed"], Spectrum)
```

---

## Phase 5 — Execution engine

**Goal**: multi-block workflows execute as DAGs. Batch, parallel/serial, pause/resume, checkpointing all work.

### 5.1 DAG construction + scheduling

- [ ] Implement `build_dag()` from `WorkflowDefinition`
- [ ] Implement `topological_sort()` with cycle detection
- [ ] Implement `DAGScheduler.execute()` — walk topo-order, check readiness, dispatch

### 5.2 Batch execution

- [ ] Implement parallel dispatch via `ProcessPoolExecutor` / `ThreadPoolExecutor`
- [ ] Implement serial dispatch (one item through full sub-pipeline)
- [ ] Implement adaptive look-ahead (scan downstream for SERIAL/INTERACTIVE → switch mode)
- [ ] Implement `BatchErrorStrategy` (stop, skip, retry, pause)
- [ ] Implement `BatchResult` accumulation

### 5.3 Resource management

- [ ] Implement `ResourceManager.acquire()` / `release()` with GPU slot counting
- [ ] Integrate with scheduler — parallel dispatch respects resource limits

### 5.4 Checkpoint + pause/resume

- [ ] Implement `WorkflowCheckpoint` serialisation (block states + intermediate refs)
- [ ] Implement `DAGScheduler.pause()` — serialise state, return checkpoint
- [ ] Implement `DAGScheduler.resume()` — load checkpoint, skip completed blocks
- [ ] Test crash recovery: kill mid-execution → resume from checkpoint

### 5.5 Event bus

- [ ] Implement `EventBus.emit()` / `subscribe()` — in-process pub/sub
- [ ] Scheduler emits: block_state_changed, batch_progress, workflow_complete, workflow_error

### 5.6 SubWorkflowBlock completion

- [ ] Now that the engine exists, implement SubWorkflowBlock with real DAGScheduler (remove stub)

### 5.7 Tests

- [ ] `tests/engine/test_dag.py` — build DAG, topo sort, cycle detection
- [ ] `tests/engine/test_scheduler.py` — 3-block linear pipeline, branching DAG, diamond DAG
- [ ] `tests/engine/test_batch.py` — 10 items parallel, 10 items serial, adaptive switch
- [ ] `tests/engine/test_resources.py` — GPU slot exhaustion → serial fallback
- [ ] `tests/engine/test_checkpoint.py` — pause → serialise → resume → correct result
- [ ] `tests/integration/test_multimodal_workflow.py` — the Appendix A scenario (simplified: load → process → merge → export)

### Deliverable

```python
# This works end-to-end:
workflow = load_yaml("examples/workflows/raman_preprocessing.yaml")
scheduler = DAGScheduler(workflow)
await scheduler.execute()
# All blocks executed in correct order, results stored, lineage recorded
```

---

## Phase 6 — Workflow definition + CLI

**Goal**: workflows are defined in YAML, validated, and executable from the command line without a frontend.

### 6.1 Workflow serialisation

- [ ] Implement YAML load/save with schema validation (Pydantic)
- [ ] Implement layout persistence (optional node positions)
- [ ] Implement `validate_workflow()` — type compatibility on all edges, missing connections, dangling ports

### 6.2 CLI

- [ ] Implement `scieasy init` — create project workspace directory structure
- [ ] Implement `scieasy validate workflow.yaml` — load + validate + report
- [ ] Implement `scieasy run workflow.yaml` — load + validate + execute (headless)
- [ ] Implement `scieasy blocks` — list installed blocks from registry
- [ ] Implement `scieasy serve` — start FastAPI server (stub for now, full in Phase 7)

### 6.3 Tests

- [ ] `tests/workflow/test_serializer.py` — YAML round-trip
- [ ] `tests/workflow/test_validator.py` — catch type mismatch, dangling port, cycle
- [ ] CLI smoke tests — `scieasy --help`, `scieasy blocks`, `scieasy validate examples/...`

### Deliverable

```bash
scieasy init my_project
cd my_project
scieasy validate workflows/raman_preprocessing.yaml   # "Valid ✓"
scieasy run workflows/raman_preprocessing.yaml         # Executes, prints results
scieasy blocks                                          # Lists all installed blocks
```

---

## Phase 7 — API layer

**Goal**: full REST + WebSocket + SSE backend. Frontend can connect.

### 7.1 REST endpoints

- [ ] Workflow CRUD (create, get, update, delete, execute, pause, resume)
- [ ] Block registry endpoints (list, get schema, validate connection)
- [ ] Data endpoints (upload, metadata, preview)
- [ ] Project management endpoints

### 7.2 Real-time communication

- [ ] WebSocket handler — broadcast block state changes, interactive block prompts
- [ ] SSE handler — stream execution logs

### 7.3 Tests

- [ ] `tests/api/` — FastAPI TestClient for all routes
- [ ] WebSocket integration test — connect, start workflow, receive state updates

---

## Phase 8 — Frontend

**Goal**: visual workflow editor connected to backend.

### 8.1 ReactFlow canvas

- [ ] Block node component (ports, state badge, progress)
- [ ] Typed edge component (color by data type)
- [ ] Drag-drop from palette onto canvas
- [ ] Connection validation (query backend on wire draw)
- [ ] SubWorkflow drill-down node

### 8.2 Block palette

- [ ] Fetch block list from backend registry endpoint
- [ ] Search + category filter
- [ ] "Reload blocks" button

### 8.3 Config panel

- [ ] Auto-generated form from JSON Schema
- [ ] CodeBlock: Monaco editor for inline mode, file picker for script mode
- [ ] InputDelivery per-port selector (shown only for CodeBlock in script mode)
- [ ] Port inspector (types, constraints, connection status)

### 8.4 Execution UI

- [ ] Run / pause / resume controls
- [ ] Live block state badges via WebSocket
- [ ] Log stream viewer via SSE
- [ ] Batch progress indicator

---

## Phase 9 — AI services

**Goal**: AI can generate blocks, propose workflows, and suggest parameters.

### 9.1 Block and type generation

- [ ] Implement prompt templates for all five block categories + data types
- [ ] Implement validation pipeline (static analysis → dry run → port contract check)
- [ ] End-to-end: natural-language description → validated block in registry

### 9.2 Workflow synthesis

- [ ] Implement: data description + goal → proposed DAG (YAML)

### 9.3 Parameter optimization

- [ ] Implement: observe intermediate results → suggest parameter changes

---

## Phase 10 — Integration + polish

**Goal**: the Appendix A scenario (LC-MS + Raman + IF + SRS) runs end-to-end through the full stack.

- [ ] Implement mzXML adapter, h5ad adapter
- [ ] Build example blocks: CellposeSegment, RamanBaseline, SpectralPCA
- [ ] Build the full multimodal workflow from ARCHITECTURE.md Appendix A
- [ ] Run it: data loaded → ElMAVEN (mock) → R script → Cellpose → napari (mock) → merge → export
- [ ] Confirm lineage, checkpoints, batch modes all work in the integrated scenario
- [ ] Write `docs/getting-started.md` tutorial based on this scenario

---

## Milestone summary

| Phase | Deliverable | Bootstrap gate exemption? |
|---|---|---|
| 0 | Empty repo, CI green | Yes |
| 1 | Interface skeleton, mypy passes | Yes |
| 2 | Architecture tests enforce boundaries | Yes |
| 3 | Core data layer works standalone | No — full gate from here |
| 4 | Blocks work in isolation | No |
| 5 | Multi-block DAG workflows execute | No |
| 6 | CLI headless execution | No |
| 7 | API backend complete | No |
| 8 | Frontend visual editor | No |
| 9 | AI services | No |
| 10 | Full multimodal demo | No |

Phases 0–2 are the foundation — no business logic, pure structure and guardrails. The bootstrap gate exemption (Appendix A of CLAUDE.md) covers these phases. Once Phase 3 begins, full workflow gate discipline applies.
