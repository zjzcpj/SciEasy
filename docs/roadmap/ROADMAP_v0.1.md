# SciEasy — Roadmap v0.1

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
- Reference lineage record: 
  LineageRecord:
      input_hashes:  [hash(input_0), hash(input_1), ...]
      block_id:      "cellpose_segment_v2"
      block_config:  { diameter: 30, model: "cyto2", ... }
      block_version: "0.3.1"
      output_hashes: [hash(output_0)]
      timestamp:     "2026-04-02T14:32:00Z"
      duration_ms:   4521
      environment:   { python: "3.11.8", key_packages: { cellpose: "3.0.1", ... } }
      batch_info:    { total: 50, succeeded: 48, failed: 2, strategy: "skip" }

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