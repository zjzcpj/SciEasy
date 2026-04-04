# SciEasy — Architecture Decision Records (ADR)

> ADRs capture the key design decisions made during SciEasy's architecture phase,
> including context, alternatives considered, and trade-offs accepted.
>
> **Status values**: `accepted` | `proposed` | `superseded` | `deprecated`

---

## ADR-001: Six base data types with inheritance

**Status**: accepted  
**Date**: 2026-04-02

### Context

The framework must represent all scientific data flowing between blocks — images, spectra, tabular data, text reports, opaque files, and complex multi-modal containers (AnnData, SpatialData). We need a type system that is small enough to learn quickly but extensible enough for any domain.

### Decision

Six base types inheriting from `DataObject`:

- `Array` — n-dimensional numeric data (images, hyperspectral cubes, tensors).
- `Series` — 1D indexed data (spectra, time series, chromatograms).
- `DataFrame` — columnar tabular data (peak tables, cell metadata, feature matrices).
- `Text` — plain text, markdown, JSON strings.
- `Artifact` — opaque files (PDFs, reports, binary blobs).
- `CompositeData` — named collection of heterogeneous `DataObject` slots.

Users extend via standard Python inheritance. Port type matching uses `isinstance`-style checks, so a `RamanSpectrum(Spectrum)` auto-matches any port accepting `Spectrum` or `Series`.

### Alternatives considered

- **Fewer types (Array + DataFrame + Blob only)**: too coarse. Series and Spectrum have different semantics from a 2D Array; collapsing them loses axis meaning and forces blocks to do runtime shape checking.
- **Many fine-grained types (separate Image, Volume, TimeSeries, Spectrum, etc. all at base level)**: combinatorial explosion. Hard for new users to know which base to pick. Inheritance solves this — `Image` is an `Array` with spatial conventions.
- **No CompositeData (force AnnData to inherit DataFrame)**: AnnData is fundamentally a container of heterogeneous objects (matrix + obs + var + uns), not a special DataFrame. Single-parent inheritance misrepresents the structure and breaks port semantics.

### Consequences

- Six types is a small learning surface for new users.
- CompositeData adds complexity to port matching (must support slot-level constraints) but accurately models real scientific data containers.
- Community types are always subtypes of one of six bases — no "where does this go?" ambiguity.

---

## ADR-002: Named axes on Array types

**Status**: accepted  
**Date**: 2026-04-02

### Context

Multi-modal workflows frequently need to align arrays of different dimensionality — applying a 2D mask `(y, x)` across every channel of a 3D MSI dataset `(y, x, mz)`. Without named axes, dimension alignment is positional and fragile ("dim 0 is probably y").

### Decision

Add an optional `axes: list[str] | None` field to `Array`. Domain subtypes declare their axis convention:

```
Image:      ["y", "x"]
MSImage:    ["y", "x", "mz"]
SRSImage:   ["y", "x", "wavenumber"]
FluorImage: ["y", "x", "channel"]
```

Named axes are pure metadata — they do not affect storage, ViewProxy, or chunk layout.

### Alternatives considered

- **xarray-style dimension labelling as the core data model**: too opinionated. Forces all Array users into xarray conventions. Many scientific libraries (cellpose, scikit-image, OpenCV) expect plain numpy arrays and would require constant conversion.
- **No named axes (positional only)**: leaves dimension semantics implicit. Every block that operates across modalities must hardcode assumptions like "the third axis is m/z". Error-prone and unreadable.

### Consequences

- Lightweight change: one optional field on Array, no storage impact.
- Port constraints can reference axis names (e.g. "must have y and x axes") instead of ndim checks.
- The broadcast utility (ADR-003) depends on named axes for alignment validation.
- `axes = None` remains valid for plain numeric arrays where axis semantics are irrelevant.

---

## ADR-003: Broadcast as explicit utility, not implicit type-system behaviour

**Status**: accepted  
**Date**: 2026-04-02

### Context

Applying low-dimensional data to high-dimensional data along specific axes is a recurring pattern (mask → MSI channels, baseline → spectrum batch, ROI → time-lapse frames). numpy-style automatic broadcasting is purely shape-based and ignores semantic alignment (e.g. whether two spatial arrays are actually co-registered).

### Decision

Provide `broadcast_apply()` in `scieasy.utils.broadcast` as an explicit, opt-in utility that block authors call when needed. It validates axis name alignment, iterates over the specified `over_axes`, and calls a user-provided function per slice. Broadcasting is never triggered automatically by the port system or DAG scheduler.

### Alternatives considered

- **Automatic broadcasting at the port/engine level**: shape match ≠ semantic match. An IF image and an MSI image may have compatible `(y, x)` shapes but different pixel sizes, FOV offsets, or coordinate systems. Auto-broadcasting without registration would silently produce wrong results.
- **No broadcast utility (leave it to block authors entirely)**: every block that needs this pattern would reimplement axis iteration from scratch. The utility eliminates boilerplate while keeping domain decisions (which axes, what function) in the block.

### Consequences

- Blocks retain full control over broadcasting semantics.
- The utility catches axis misalignment errors early with clear messages.
- Registration/alignment must be an explicit preceding step in the workflow — the framework does not guess.

---

## ADR-004: Five block categories plus SubWorkflowBlock

**Status**: accepted  
**Date**: 2026-04-02

### Context

The framework needs a small, memorable set of block categories that covers all processing scenarios — from pure computation to external GUI software to AI-driven analysis — without requiring users to navigate a complex taxonomy.

### Decision

Five categories covering distinct execution patterns, plus one meta-category:

| Category | When to use |
|---|---|
| `IOBlock` | Load or save data in any format. Single class with direction flag. |
| `ProcessBlock` | Deterministic data transformation (including merge, split, filter). |
| `CodeBlock` | Run user-provided R/Python/Julia scripts (inline or file-based). |
| `AppBlock` | Bridge external GUI software (ElMAVEN, Fiji, napari) via file exchange. |
| `AIBlock` | LLM-driven processing (classification, summarisation, code generation). |
| `SubWorkflowBlock` | Encapsulate an entire workflow as a single reusable block. |

### Alternatives considered

- **More categories (separate MergeBlock, ViewBlock, ExportBlock, CLIBlock)**: every additional category increases cognitive load. Merge is a ProcessBlock with multiple inputs. Export is an IOBlock with `direction="output"`. CLI tools are AppBlocks with non-GUI commands. The five categories are sufficient because they distinguish by execution pattern, not by data operation.
- **Single Block class with mode flags**: loses type safety. A ProcessBlock and an AppBlock have fundamentally different lifecycle requirements (auto-execute vs launch-pause-watch-resume). Separate base classes let the engine dispatch correctly without runtime mode checks.

### Consequences

- New users learn five concepts. Everything else is a subclass of one of them.
- SubWorkflowBlock enables hierarchical composition — a lab's standard preprocessing pipeline becomes a single palette item.
- The boundary between ProcessBlock and CodeBlock is sometimes fuzzy (a Python ProcessBlock vs a CodeBlock in inline mode). Convention: if the logic is reusable and has typed ports, make it a ProcessBlock. If it's a one-off script, use CodeBlock.

---

## ADR-005: CodeBlock supports inline and script execution modes

**Status**: accepted  
**Date**: 2026-04-02

### Context

Users have existing analysis scripts ranging from 5-line snippets to 500-line R pipelines with custom dependencies. A single execution model cannot serve both cases. Requiring users to restructure their scripts into a specific framework API would violate the "inclusive" principle.

### Decision

CodeBlock supports two modes:

- **Inline mode**: user writes code directly in the block's config panel. Variables are injected from input ports and extracted to output ports by name. Best for short, one-off operations.
- **Script mode**: user points the block at an existing `.py` / `.R` / `.jl` file. The framework calls a conventional `run(inputs, config) → dict` function. The script can import any libraries, define helper functions, and span hundreds of lines. An optional `configure()` function provides config schema for the UI form.

The framework introspects script files to auto-generate port declarations and config forms.

### Alternatives considered

- **Inline only**: breaks for complex scripts with imports, helper functions, and multi-file dependencies. Users would have to flatten everything into a single string.
- **Script only (always require a file)**: overkill for `output_0 = input_0[input_0["pvalue"] < 0.05]`. Inline mode reduces friction for quick operations.
- **Notebook-style cells**: adds UI complexity (cell ordering, state management) that duplicates Jupyter's job. SciEasy is a workflow framework, not a notebook.

### Consequences

- Users can integrate existing scripts without modification beyond adding a `run()` wrapper function.
- Script introspection (`introspect.py`) must handle Python, R, and Julia function signatures — a moderate implementation effort.
- Inline mode executes code via `exec()`, which has security implications. Acceptable for single-user local deployment; requires sandboxing for any future multi-user scenario (see Appendix C.3 of ARCHITECTURE.md).
- Data delivery to user scripts requires explicit handling — see ADR-016 for the per-port `InputDelivery` mechanism that resolves the tension between lazy loading and script compatibility.

---

## ADR-006: External software integration via file-exchange bridge

**Status**: accepted  
**Date**: 2026-04-02

### Context

Many scientific workflows depend on standalone GUI applications (ElMAVEN for LC-MS peak picking, Fiji/ImageJ for image processing, napari for segmentation review, FlowJo for flow cytometry gating). These tools cannot be replaced — they have decades of domain-specific development. The framework must integrate them, not compete with them.

### Decision

`AppBlock` bridges external software via a file-exchange protocol:

1. Serialise input data to a temporary exchange directory in the app's native format.
2. Launch the external application as a subprocess.
3. Pause the workflow. Frontend shows "Waiting for external software."
4. Monitor the exchange directory for output files (using filesystem watcher).
5. When output files appear or are modified, read them, wrap as DataObjects, resume workflow.

### Alternatives considered

- **API-based integration (plugins for each app)**: most scientific GUI tools have no stable API, or their APIs are incomplete (e.g. Fiji's macro language cannot access all features). File exchange is the universal lowest-common-denominator.
- **Screen scraping / automation**: fragile, platform-dependent, and cannot access internal application state.
- **Ignore external tools (only support code-based processing)**: violates the core "inclusive" principle. Many users' workflows fundamentally depend on manual operations in these tools.

### Consequences

- File-based exchange is slow but universally compatible. No per-application plugin needed.
- The workflow pauses during external app use — batch throughput depends on human speed. Acceptable because these are inherently interactive steps.
- Exchange directory cleanup must be handled by the framework to avoid disk bloat.
- `watchdog` library dependency for filesystem monitoring.

---

## ADR-007: Lazy loading by default via ViewProxy

**Status**: accepted  
**Date**: 2026-04-02

### Context

Some datasets (MSI, spatial transcriptomics) exceed 100 GB. Loading full datasets into memory at block input is infeasible. Yet many blocks only need a small slice (one channel, one ROI, metadata only).

### Decision

`DataObject` instances are lightweight wrappers (~KB) holding a `StorageReference`. Blocks never receive raw data directly. The engine injects a `ViewProxy` that mediates access:

- `.slice(...)` — read a specific region (Zarr chunk-aware).
- `.iter_chunks(chunk_size)` — iterate in fixed-size pieces.
- `.to_memory()` — load everything (explicit opt-in, with large-data warnings).
- `.shape`, `.axes` — metadata without loading data.

### Alternatives considered

- **Eager loading (load everything into memory at block input)**: OOM on large datasets. Unacceptable for the target use case.
- **Memory-mapped files only**: works for single-machine, but doesn't extend to cloud/remote storage. Zarr-backed ViewProxy works with both local and remote stores.
- **Dask lazy arrays as the core abstraction**: adds a heavy dependency and forces all block authors to understand Dask semantics. ViewProxy is simpler — block authors who want full data just call `.to_memory()`.

### Consequences

- Block authors must be aware they're working with proxies, not raw arrays. Most blocks can call `.to_memory()` for small data or `.iter_chunks()` for large data.
- ViewProxy integrates with Zarr chunking for efficient partial reads.
- Storage backend is abstracted — switching from Zarr to a cloud store doesn't change block code.

---

## ADR-008: Two-tier block and type distribution

**Status**: accepted  
**Date**: 2026-04-02

### Context

The framework targets both bench scientists (who want to add a quick custom block without tooling knowledge) and community developers (who want to publish polished, versioned block packages). A single distribution mechanism cannot serve both audiences.

### Decision

Two tiers, both feeding into a unified registry:

- **Tier 1 — Drop-in files**: place a `.py` file in `{project}/blocks/` or `~/.scieasy/blocks/` (and corresponding `types/` directories). Framework auto-discovers on startup and via manual "Reload blocks" button. Zero packaging, zero config.
- **Tier 2 — pip install**: standard Python packages with `scieasy.blocks`, `scieasy.types`, and `scieasy.adapters` entry_points. `pip install scieasy-flowcyto` makes all blocks appear in the palette immediately.

Same two-tier model applies to custom data types.

### Alternatives considered

- **Tier 2 only (pip packages for everything)**: too heavy for "I just want to add a denoise block for this project." Requires pyproject.toml, package structure, pip install. Unacceptable friction for non-developers.
- **Three tiers with a Block Hub (in-app marketplace)**: desirable long-term but premature for v1. Adds significant infrastructure (index server, compatibility checking, in-app pip execution). Can be added later without architectural changes.
- **Dynamic code loading from a database or cloud**: introduces security and versioning complexity. Files on disk are inspectable, version-controllable (git), and debuggable with standard tools.

### Consequences

- Tier 1 makes the 5-minute "write a block, see it in the palette" experience possible.
- Tier 2 enables a healthy community ecosystem around modality-specific block packages.
- Registry scans two sources at startup — minimal performance impact since drop-in directories are typically small.
- Tier 2 entry_points shadow Tier 1 blocks with the same name (installed packages are authoritative).

---

## ADR-009: Registry stores specs, not class references

**Status**: accepted  
**Date**: 2026-04-02

### Context

Users modify drop-in block files during a session and click "Reload blocks" to pick up changes. Python's `importlib.reload()` produces a new class object that breaks `isinstance` checks against cached old references. The registry must handle reloads without corrupting running workflows.

### Decision

`BlockRegistry` and `TypeRegistry` store `BlockSpec` / `TypeSpec` descriptors (module path, class name, metadata, file mtime) — never the class object itself.

- **Scan phase** (startup + reload): import each file, read class-level metadata, build spec, discard class reference.
- **Instantiation phase** (workflow execution): fresh import from file using a unique module name incorporating mtime. Not placed in `sys.modules` to avoid cache pollution.

Running block instances are fully decoupled from the registry. A reload never affects in-flight workflows — only the next instantiation picks up new code.

### Alternatives considered

- **Store class references, use `importlib.reload()`**: reload produces a new class object. Old instances and new instances are incompatible under `isinstance`. Causes subtle breakage in port matching and type checking.
- **Restart the server on every change**: unacceptable UX for iterative development.
- **Hot-swap class references in running instances**: extremely complex, error-prone, and unsafe for stateful blocks mid-execution.

### Consequences

- Reload is safe and predictable: scan → update specs → notify frontend.
- Running workflows are never affected by reloads.
- Each fresh import has minor overhead (~ms per file) — acceptable for Tier 1 directories with typically <50 files.
- Tier 2 (pip packages) are not hot-reloaded — they update via `pip install --upgrade` and require restart.

---

## ADR-010: Batch execution mode declared per block

**Status**: superseded by ADR-020
**Date**: 2026-04-02

### Context

When processing a collection (e.g. 50 images), some blocks benefit from parallelism (Cellpose segmentation on CPU/GPU) while others require serial execution (napari manual review, one image at a time). A global batch strategy cannot accommodate both.

### Decision

Each block declares a `batch_mode` attribute:

- `PARALLEL`: all items through this block concurrently, then proceed to the next block. Uses `ProcessPoolExecutor` (CPU) or `ThreadPoolExecutor` (IO).
- `SERIAL`: each item runs through the full downstream sub-pipeline before the next item starts. Required for interactive/external blocks.
- `ADAPTIVE` (default): engine performs look-ahead on the DAG. If any downstream block in the same branch is SERIAL or INTERACTIVE, current block runs in SERIAL mode to avoid buffering. Otherwise, PARALLEL.

A `ResourceManager` throttles parallel dispatch based on GPU slots, CPU workers, and memory budget. Blocks declare resource needs via `ResourceRequest`.

### Alternatives considered

- **Global batch mode (entire workflow is parallel or serial)**: too coarse. A workflow with 8 auto blocks and 1 napari review block would be forced entirely serial, wasting parallelism on the 8 auto blocks.
- **No batch support (one item at a time always)**: unacceptable performance for automated pipelines with hundreds of items.
- **User configures batch mode per-run in the UI**: error-prone. The block author knows best whether their block supports parallelism. ADAPTIVE mode handles the common case automatically.

### Consequences

- Most blocks default to ADAPTIVE — authors only override for specific requirements.
- The engine's look-ahead scan adds minor complexity to the scheduler but eliminates the need for users to think about batch strategy.
- ResourceManager prevents GPU OOM by limiting concurrent GPU tasks even when batch_mode is PARALLEL.

---

## ADR-011: Workflow definition as declarative YAML, decoupled from frontend

**Status**: accepted  
**Date**: 2026-04-02

### Context

Workflows must be portable (shareable between users), version-controllable (git-friendly), machine-readable (AI synthesis and validation), and renderable by different frontends.

### Decision

Workflows are serialised as YAML files defining nodes (block type + config) and edges (source port → target port). The ReactFlow canvas is one visualisation of this definition, not the definition itself. An optional `layout` field per node stores canvas position for visual restoration.

### Alternatives considered

- **ReactFlow's internal JSON as the source of truth**: couples the workflow definition to a specific frontend library's data model. Makes headless execution, CLI validation, and AI synthesis harder.
- **Python DSL (workflow defined in code)**: powerful but excludes non-developers. YAML is readable by anyone and editable in any text editor.
- **Visual-only (no serialised format, workflow lives in the UI)**: makes version control, sharing, and headless execution impossible.

### Consequences

- Workflows are portable `.yaml` files that can be committed to git, shared via email, or published alongside papers.
- The `scieasy run workflow.yaml` CLI can execute workflows headlessly without a frontend.
- AI can generate and modify workflows by producing YAML.
- Frontend layout information is optional metadata — losing it only means the canvas auto-layouts on next open.

---

## ADR-012: Checkpoint-based pause and resume

**Status**: accepted  
**Date**: 2026-04-02

### Context

Workflows can be long-running (hours for large batch processing) and include interactive steps (AppBlock waiting for user action in external software). Users may close the browser, the machine may crash, or a collaborator may need to pick up where someone else left off.

### Decision

The engine serialises a `WorkflowCheckpoint` after every block completion:

- Block states (DONE / PAUSED / IDLE for each node).
- `StorageReference` for all intermediate outputs produced so far.
- ID of the pending block (if paused for interactive/external action).
- Full config snapshot at checkpoint time.

Checkpoints are saved to `{project}/checkpoints/` as JSON + references to Zarr/Parquet data. Resuming loads the latest checkpoint, skips completed blocks, and continues from the pending block.

### Alternatives considered

- **No checkpointing (always restart from the beginning)**: unacceptable for workflows with expensive blocks (hours of GPU compute) or interactive steps.
- **In-memory state only (no persistence)**: lost on browser close or crash.
- **Full data duplication at each checkpoint**: storage-prohibitive for large datasets. Storing `StorageReference` pointers instead of copying data keeps checkpoints lightweight.

### Consequences

- Crash recovery without re-running completed blocks.
- Collaborative handoff: one person runs automated steps, saves checkpoint, another person does manual review.
- Checkpoint files reference intermediate data by storage path — if underlying data is moved or deleted, checkpoint becomes invalid.

---

## ADR-013: AI as a four-tier service layer, not embedded in the core

**Status**: accepted  
**Date**: 2026-04-02

### Context

The framework aims to be "AI-native" — AI should be able to generate blocks, compose workflows, extend type hierarchy, and optimise parameters. But tightly coupling AI into the core would make the framework unusable offline or without API keys.

### Decision

AI capabilities are a separate service layer (Layer 4) that calls into the core layers but is not called by them. Four tiers:

1. **Block generation**: NL description → any of the five block categories.
2. **Type generation**: NL description → DataObject subtypes with helper methods.
3. **Workflow synthesis**: data description + goal → complete DAG.
4. **Runtime parameter optimisation**: observe intermediate results → suggest parameter adjustments.

All AI features are optional. The framework is fully functional without them. AI-generated code passes through a validation pipeline (static analysis → dry run → port contract check → user review) before registration.

### Alternatives considered

- **AI deeply integrated (e.g. automatic type inference on every connection, AI-driven error recovery)**: makes behaviour unpredictable, adds latency to basic operations, and creates hard dependency on LLM availability.
- **No AI (add later as plugins)**: misses the opportunity to design generation-friendly interfaces from the start. Validation pipeline, config schemas, and convention-based entry functions are all designed with AI generation in mind.

### Consequences

- Framework works offline, on air-gapped machines, without API keys.
- AI features degrade gracefully — if the LLM is unavailable, users manually write blocks and compose workflows.
- The validation pipeline adds safety but also latency to AI generation (~seconds for dry run).
- AI-generated blocks are indistinguishable from hand-written blocks once validated — no second-class citizenship.

---

## ADR-014: ReactFlow + FastAPI as the frontend-backend stack

**Status**: accepted  
**Date**: 2026-04-02

### Context

The framework needs a visual workflow editor (drag-drop blocks, wire connections, live status) backed by a Python server (scientific computing ecosystem). The frontend-backend boundary must support real-time updates (block progress, interactive prompts) and large file transfers.

### Decision

- **Frontend**: React + ReactFlow (node-graph canvas) + Zustand (state) + shadcn/ui (components).
- **Backend**: FastAPI (REST + WebSocket + SSE) with Pydantic validation.
- **Communication**: REST for CRUD, WebSocket for real-time block state / interactive signals, SSE for log streaming.

### Alternatives considered

- **Desktop-native (PyQt / Electron + Python)**: richer OS integration but harder to distribute, update, and extend. Web-based approach works on any OS and allows future multi-user scenarios.
- **Streamlit or Panel**: rapid prototyping but limited control over complex UIs like node-graph editors. ReactFlow is the mature, purpose-built solution for visual workflow canvases.
- **Django or Flask instead of FastAPI**: FastAPI's native async support, automatic OpenAPI docs, WebSocket handling, and Pydantic integration make it the better fit for a real-time, schema-heavy API.

### Consequences

- Two-language codebase (Python backend + TypeScript frontend). Manageable because the boundary is a well-defined API.
- ReactFlow provides minimap, zoom, drag-drop, and connection validation out of the box.
- WebSocket enables sub-second UI updates during workflow execution.

---

## ADR-015: Inclusive strategy — wrap existing tools, never replace

**Status**: accepted  
**Date**: 2026-04-02

### Context

Researchers have years of investment in existing tools, scripts, and pipelines. Asking them to migrate is a non-starter. The framework must demonstrate immediate value by working with what they already have.

### Decision

The framework provides three integration mechanisms that cover the vast majority of existing tools:

- `CodeBlock` (inline + script mode): wrap any R/Python/Julia code with minimal modification.
- `AppBlock` (file-exchange bridge): integrate any GUI application that can read/write files.
- `SubWorkflowBlock`: encapsulate any existing multi-step pipeline as a reusable block.

The framework never reimplements functionality that existing tools do well. Instead, it provides the connective tissue between them.

### Alternatives considered

- **Provide built-in implementations for common operations (reimplementing ElMAVEN peak picking, Cellpose segmentation, etc.)**: duplicates effort, always lags behind the original tool, and fragments the user community.
- **Require formal plugins/adapters for every external tool**: too much upfront work. File-exchange bridge works with any tool immediately.

### Consequences

- Users see value from day one: put existing scripts and tools into blocks, wire them together, gain reproducibility and multi-modal integration.
- The framework's value proposition is composition and integration, not replacing any single tool.
- File-based integration is slower than in-process integration but universally compatible.
- Community can build tighter integrations (e.g. programmatic Cellpose block) as ProcessBlock subclasses when the default file-exchange approach becomes a bottleneck.

---

## ADR-016: Per-port InputDelivery for CodeBlock data handoff

**Status**: accepted  
**Date**: 2026-04-02

### Context

The framework promises lazy loading via ViewProxy (ADR-007) — DataObjects are lightweight wrappers, and blocks receive proxies that load data on demand. However, CodeBlock must bridge between this framework-internal abstraction and user scripts that expect native Python/R objects (numpy arrays, pandas DataFrames). The original CodeBlock implementation called `proxy.to_memory()` on every input unconditionally, meaning a 100 GB MSImage connected to a CodeBlock would be fully loaded into memory regardless of whether the script needed all of it. This silently violated the lazy-loading contract for any CodeBlock with large inputs.

The tension is fundamental: user scripts written in plain numpy/pandas/R cannot operate on a `ViewProxy` object — they need real data. But forcing full materialisation on every input makes the memory boundary architecture meaningless at the CodeBlock boundary.

### Decision

Each input port on a CodeBlock independently declares an `InputDelivery` mode that controls how data is handed to the user's script:

| Mode | What the script receives | When to use |
|---|---|---|
| `MEMORY` (default) | Native object via `proxy.to_memory()` | Small-to-medium data. Compatible with any script. |
| `PROXY` | The `ViewProxy` itself | Large data, experienced user controls `.slice()` / `.iter_chunks()` |
| `CHUNKED` | One chunk per invocation (framework iterates) | Large homogeneous batches where each chunk is processed identically |

Inline mode is locked to MEMORY (short scripts should not manage proxies). Script mode supports all three, configured via the `input_delivery` key in the script's `configure()` return value, or overridden per-port in the UI config panel.

For MEMORY mode, the framework displays a warning in the config panel when an input exceeds a configurable threshold (default 2 GB), suggesting the user switch to PROXY or CHUNKED delivery.

For CHUNKED mode, the framework calls the script's `run()` function once per chunk, passing the chunk as a native object. Non-chunked inputs are prepared once and reused across all chunk invocations. The framework concatenates per-chunk outputs into the final result.

### Alternatives considered

- **Always `to_memory()` (original design)**: simple, universally compatible, but breaks the lazy-loading promise for large data. A single CodeBlock with a 100 GB MSI input would OOM.
- **Always pass ViewProxy (never materialise)**: breaks all existing scripts. `np.mean(proxy)` doesn't work. Requires every user to learn the ViewProxy API. Unacceptable friction.
- **Auto-detect based on data size (small → memory, large → proxy)**: unpredictable. The user writes a script expecting a numpy array, then it silently becomes a ViewProxy when the dataset grows. Debugging nightmare.
- **ProcessBlock-style (always pass proxy, block author calls `.to_memory()` explicitly)**: reasonable for ProcessBlock authors who are writing framework-aware code, but CodeBlock users are writing standalone scripts that should work without framework knowledge.

### Consequences

- Default behaviour (MEMORY) is unchanged for 90% of CodeBlock usage — no learning curve for simple scripts.
- PROXY and CHUNKED modes are opt-in, only relevant when large data enters a CodeBlock.
- The `configure()` convention gains a new `input_delivery` key — framework introspection reads it and adjusts the config panel accordingly.
- CHUNKED mode adds complexity to the CodeBlock bridge (iteration loop, result concatenation) but keeps user scripts simple (process one chunk, return result).
- The framework-user boundary is now explicit and documented rather than a hidden `to_memory()` call. Users who connect large data to CodeBlock without choosing PROXY/CHUNKED see a clear warning rather than a silent OOM.
- ProcessBlock does not need InputDelivery — ProcessBlock authors write framework-aware code and receive ViewProxy directly, deciding for themselves when to materialise.

---

## ADR-017: Subprocess isolation for all block execution

**Status**: proposed
**Date**: 2026-04-03

### Context

The original architecture implicitly assumed that blocks could execute in-process. Specifically:

- `CodeBlock` inline mode executes user code via `exec(script, namespace)` in the engine's Python process (`src/scieasy/blocks/code/runners/python_runner.py:27`).
- `CodeBlock` script mode loads user scripts via `importlib.util.spec_from_file_location()` and calls `spec.loader.exec_module(module)` in the engine's process (`python_runner.py:62–67`).
- `RRunner` was planned to use `rpy2` (in-process bridge) per its docstring (`src/scieasy/blocks/code/runners/r_runner.py:12`).
- `JuliaRunner` was planned to use `juliacall` (in-process bridge) per its docstring (`src/scieasy/blocks/code/runners/julia_runner.py:12`).
- `ProcessBlock` subclasses have their `run()` method called directly by the engine.
- `AppBlock` already launches an external subprocess via `subprocess.Popen` (`src/scieasy/blocks/app/bridge.py:81–86`), but the Popen handle is returned from `launch()` and never stored, tracked, or used for lifecycle management.

This creates fundamental problems:

1. **Unrecoverable hangs**: if user code enters an infinite loop, deadlocks, or blocks on I/O, the engine's main process freezes. Python threads cannot be reliably killed (`threading` has no `kill()` API; `ctypes.pythonapi.PyThreadState_SetAsyncExc` is unreliable for C-extension code like scipy, cellpose, and numpy). The scheduler, all other blocks, and the API server become unresponsive.

2. **No cancellation path**: the framework must support user-initiated cancellation of any running block at any time (ADR-018). Cancellation requires the ability to forcefully terminate execution. Only OS-level process termination provides a reliable kill guarantee across all code (pure Python, C extensions, R, Julia, external applications).

3. **Memory and crash isolation**: a block that segfaults (common with native C/Fortran extensions), triggers OOM, or leaks memory only affects its own subprocess. Without process isolation, a single misbehaving block can crash or degrade the entire engine.

4. **Resource accounting**: with all blocks in subprocesses, the ResourceManager can track actual system resource usage per-process (via OS-level metrics) rather than relying solely on declared estimates.

### Discussion points and resolution

| # | Topic | Options discussed | Final decision |
|---|---|---|---|
| 1 | Should framework-internal `ProcessBlock` get an `IN_PROCESS` fast path? | (A) Allow `IN_PROCESS` for trusted ProcessBlocks to save ~100ms subprocess startup. (B) All blocks subprocess, no exceptions. | **Decision: (B).** The complexity of maintaining two execution models in the scheduler, resource manager, and cancellation system outweighs the ~100ms savings. All blocks are treated identically. |
| 2 | Should `CodeBlock` inline mode remain `exec()` for simplicity? | (A) Keep `exec()` for inline only (short scripts, low risk). (B) All CodeBlock modes go through subprocess. | **Decision: (B).** Even short inline scripts can call `time.sleep(999999)` or import a module that hangs. The user cannot distinguish "inline" from "script" at the risk level. Uniform subprocess execution. |
| 3 | Use `multiprocessing.Process` or `subprocess.Popen`? | (A) `multiprocessing.Process` — convenient Python API, shared memory support. (B) `subprocess.Popen` — clean interpreter, no inherited state. | **Decision: (B).** `multiprocessing` fork/spawn inherits the engine's loaded modules and memory (hundreds of MB for a long-running server). `subprocess.Popen` starts a clean Python interpreter, importing only what the block needs. Cleaner isolation, more predictable memory. |
| 4 | How to handle cross-process data transfer? | (A) Serialise full data payloads across the process boundary (pickle/JSON). (B) Pass `StorageReference` only; subprocess rebuilds `ViewProxy` from storage. | **Decision: (B).** Leverages the existing lazy-loading architecture (ADR-007). `DataObject` instances are lightweight wrappers (~KB) holding `StorageReference` pointers. The subprocess reconstructs `ViewProxy` from the storage reference and accesses data directly from the backing store (Zarr/Parquet/filesystem). Output follows the same pattern: subprocess writes results to storage and returns `StorageReference` pointers. Cross-process overhead is limited to process startup + reference serialisation (~100ms), not data copying. |

### Decision

**All blocks execute in isolated subprocesses. No exceptions.** The engine process becomes a pure orchestrator that never executes block logic directly.

#### Execution model per block category

| Category | Previous execution model | New execution model | Change required |
|---|---|---|---|
| `ProcessBlock` | In-process `run()` call | Subprocess: serialise `StorageReference` → spawn Python subprocess → subprocess imports block class, reconstructs `ViewProxy`, calls `run()` → subprocess writes outputs to storage → return `StorageReference` | **New**: subprocess wrapper |
| `CodeBlock` (inline, Python) | `exec(script, namespace)` in engine process (`python_runner.py:27`) | Subprocess: engine sends script string + `StorageReference` via stdin/tempfile → subprocess reconstructs data, calls `exec()` → writes outputs → return references | **Rewrite**: `PythonRunner.execute_inline()` |
| `CodeBlock` (script, Python) | `importlib.util.spec_from_file_location()` in engine process (`python_runner.py:62–67`) | Subprocess: engine sends script path + `StorageReference` + config → subprocess loads module, calls entry function → writes outputs → return references | **Rewrite**: `PythonRunner.execute_script()` |
| `CodeBlock` (R) | Planned `rpy2` in-process bridge (`r_runner.py:12`) | Subprocess calling `Rscript`: engine writes inputs to temp JSON/files → `subprocess.Popen(["Rscript", wrapper.R, ...])` → R script reads inputs, runs user code, writes outputs → engine reads outputs | **Rewrite**: `RRunner` entirely |
| `CodeBlock` (Julia) | Planned `juliacall` in-process bridge (`julia_runner.py:12`) | Subprocess calling `julia`: same pattern as R | **Rewrite**: `JuliaRunner` entirely |
| `AppBlock` | `subprocess.Popen` already external, but handle discarded (`bridge.py:81–86`) | `subprocess.Popen` with handle stored in `ProcessHandle`, registered in `ProcessRegistry`, monitored by `ProcessMonitor` | **Modify**: `FileExchangeBridge.launch()` return type and handle registration |
| `AIBlock` | HTTP API call (already async/non-blocking) | Subprocess for isolation consistency: subprocess makes HTTP call, returns result. Alternatively, since HTTP calls are non-blocking and cancellable via `asyncio`, AIBlock _may_ remain in-process as a documented exception if profiling shows subprocess overhead is problematic for latency-sensitive AI calls. Initial implementation: subprocess. | **New**: subprocess wrapper |
| `IOBlock` | In-process file I/O | Subprocess: particularly important for large file reads that may OOM or hang on network filesystems | **New**: subprocess wrapper |
| `SubWorkflowBlock` | Recursive engine call | Subprocess with child DAGScheduler: the child workflow runs in its own process with its own scheduler, communicating results back via `StorageReference` | **New**: subprocess wrapper with nested scheduler |

#### Cross-process data transfer protocol

```
Engine process (orchestrator)              Block subprocess (worker)
────────────────────────────               ──────────────────────────
1. Prepare invocation payload:
   {
     "block_class": "scieasy.blocks.process.cellpose.CellposeSegment",
     "block_config": { "diameter": 30, "model": "cyto2" },
     "inputs": {
       "image": {
         "storage_ref": "zarr:///project/data/zarr/img_001",
         "dtype_info": {"type_chain": ["FluorImage","Image","Array","DataObject"]}
       }
     },
     "output_storage_dir": "/project/data/zarr/run_001/"
   }

2. Spawn subprocess:                      3. Subprocess starts clean Python interpreter.
   Popen(["python", "-m",                    Reads payload from stdin.
     "scieasy.engine.runners.worker",         Imports block class.
     ...])                                    Reconstructs ViewProxy from storage_ref.
   Register ProcessHandle.                    Calls block.run(inputs, config).
                                              Writes outputs to output_storage_dir.
                                              Prints output references to stdout.

4. Engine reads stdout.                   5. Subprocess exits with code 0.
   Parses output StorageReference(s).
   Deregisters ProcessHandle.
   Stores references for downstream blocks.
```

The payload is serialised as JSON via stdin (small payloads, <10 KB typically) or via a temporary file (for complex configs). The subprocess reads the payload, performs all heavy work, and returns lightweight references.

**Key invariant**: no scientific data crosses the process boundary. Only `StorageReference` pointers (~100 bytes each) and config dicts cross. The 100 GB MSI dataset stays in Zarr on disk; both the engine and the subprocess access it via `ViewProxy` pointing at the same storage path.

#### Platform-specific process lifecycle management

| Operation | Linux / macOS | Windows |
|---|---|---|
| Process group creation | `subprocess.Popen(..., start_new_session=True)` creates a new session and process group. `os.getpgid(pid)` retrieves the group ID. | `subprocess.Popen(..., creationflags=CREATE_NEW_PROCESS_GROUP)` for basic group. For full tree management: `CreateJobObject()` + `AssignProcessToJobObject()` via `ctypes` or `win32api`. Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` ensures child cleanup. |
| Graceful termination | `os.killpg(pgid, signal.SIGTERM)` sends SIGTERM to entire process group. Grace period (configurable, default 5 seconds) allows cleanup handlers to run. | Windows has no equivalent of SIGTERM. `GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, pid)` can be sent to console processes, but many GUI applications ignore it. Practical approach: skip grace period on Windows, go directly to forced termination. |
| Forced termination | `os.killpg(pgid, signal.SIGKILL)` after grace period expires. Cannot be caught or ignored. | `TerminateProcess(handle, exit_code)` via `ctypes`. For Job Objects: `TerminateJobObject(job_handle, exit_code)` kills all processes in the job. |
| Process tree termination | `os.killpg(pgid, signal)` kills all processes in the group. Processes that `setsid()` to escape the group are not affected (rare in scientific tools). | Job Objects are the authoritative mechanism. `TerminateJobObject()` kills all processes assigned to the job, including grandchildren. Without Job Objects, `taskkill /T /F /PID {pid}` can be used as fallback (requires subprocess call). |
| Process alive check | `os.kill(pid, 0)` — sends signal 0 (no-op) to test if process exists. Raises `ProcessLookupError` if dead, `PermissionError` if alive but owned by another user. | `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)` via `ctypes`. If it returns a valid handle, the process exists. Then `GetExitCodeProcess()` — if it returns `STILL_ACTIVE (259)`, the process is running. |
| Zombie process cleanup | `os.waitpid(pid, os.WNOHANG)` to reap zombie (child exited but parent hasn't waited). Must be called after detecting death to prevent zombie accumulation. | Not applicable. Windows automatically cleans up process entries when all handles to the process are closed. |
| Subprocess launch isolation | `start_new_session=True` in `Popen` kwargs. This calls `setsid()` in the child, detaching it from the engine's terminal/session. Prevents Ctrl-C from the terminal propagating to block subprocesses. | `CREATE_NEW_PROCESS_GROUP` flag in `Popen` `creationflags`. Prevents Ctrl-C propagation. Combined with Job Object for lifecycle management. |

All platform-specific code is encapsulated in `ProcessHandle` (ADR-019) and `engine/runners/platform.py`. The rest of the codebase interacts with `ProcessHandle.terminate()`, `ProcessHandle.is_alive()`, etc., without knowing the underlying platform.

### Alternatives considered

- **Keep `IN_PROCESS` as an option for trusted/fast blocks**: creates two execution models that the scheduler, resource manager, and cancellation system must each handle separately. Doubles the testing surface for execution lifecycle. The ~100ms subprocess startup overhead is negligible for scientific workflows where blocks typically run for seconds to hours. If profiling later reveals subprocess overhead is a bottleneck for specific hot-path blocks, a fast-path optimisation can be added as a targeted, documented exception — but the architectural default must be subprocess.

- **Use threads with cooperative cancellation (cancellation tokens / flags)**: requires every block author to periodically check a cancellation flag in their `run()` method. User scripts and third-party libraries (scipy.optimize, cellpose.eval, DESeq2) will never check a framework-specific cancellation flag. A hung native C extension call (common in scientific computing) will never yield to Python's thread scheduler. Only OS-level process termination is reliable.

- **Use `multiprocessing.Process` instead of `subprocess.Popen`**: `multiprocessing` uses fork (on Linux) or spawn to create a copy of the parent process, inheriting all loaded modules and memory. For a long-running engine with dozens of imported packages, the child starts with hundreds of MB of unnecessary state. `subprocess.Popen` starts a clean Python interpreter, importing only what the block needs. Additionally, `multiprocessing` shares some global state (logging config, signal handlers) in ways that can interfere with block execution. `subprocess.Popen` provides cleaner isolation.

- **Use Docker containers for isolation**: maximum isolation but massive overhead (seconds to start, GB of disk per image, requires Docker installation). Appropriate for future cloud/multi-user deployment (the `CONTAINER` level in `SandboxPolicy`) but overkill for single-user local installations. Subprocess isolation provides the necessary safety with minimal overhead.

### Consequences

- The engine process is protected from block crashes, hangs, segfaults, and memory leaks. A block that OOMs only kills its own subprocess; the engine continues running.
- Every block is cancellable at any time via `ProcessHandle.terminate()` (ADR-018, ADR-019).
- Subprocess startup adds ~50–200ms overhead per block execution. For scientific workflows where blocks typically run seconds to hours, this is negligible (<0.1% of execution time).
- Block authors do not need to change their code. The framework handles serialisation of `StorageReference` and reconstruction of `ViewProxy` transparently in the subprocess worker.
- R execution is simplified: always `subprocess` calling `Rscript`, no `rpy2` in-process bridge complexity. Julia execution: always `subprocess` calling `julia`, no `juliacall` dependency.
- The `SandboxPolicy` enum from Appendix C.3 of the architecture document is partially realised: `SUBPROCESS` is now the universal baseline rather than a future option. `CONTAINER` and `WASM` remain future extensions that build on the same `ProcessHandle` abstraction.
- Platform-specific process management (signals, process groups, Job Objects) is encapsulated in `ProcessHandle` and `engine/runners/platform.py`, keeping the rest of the codebase platform-agnostic.
- A new module `engine/runners/worker.py` must be created as the subprocess entry point. This module receives the invocation payload, sets up the execution environment, runs the block, and returns results.

### EventBus integration

| Event type | Emitted by | Payload fields | Subscribers |
|---|---|---|---|
| `PROCESS_SPAWNED` | `spawn_block_process()` | `block_id: str`, `pid: int`, `resource_request: ResourceRequest` | `ProcessRegistry` (register handle), `ResourceManager` (record allocation) |
| `PROCESS_EXITED` | `ProcessMonitor` | `block_id: str`, `exit_info: ProcessExitInfo` | `DAGScheduler` (update block state), `ResourceManager` (release resources), `ProcessRegistry` (deregister handle), `CheckpointManager` (save state) |

### Detailed impact scope

#### New files

| File | Contents | Key classes/functions |
|---|---|---|
| `src/scieasy/engine/runners/worker.py` | **Subprocess entry point.** Reads invocation payload from stdin (JSON), imports block class, reconstructs `ViewProxy` from `StorageReference`, calls `block.run()`, writes outputs to storage, prints output `StorageReference` JSON to stdout, exits. | `def main() -> None` (entry point), `def reconstruct_inputs(payload: dict) -> dict[str, ViewProxy]` (rebuild proxies from storage refs), `def serialise_outputs(outputs: dict, output_dir: Path) -> dict` (write outputs, return refs) |
| `src/scieasy/engine/runners/platform.py` | **Platform abstraction layer.** Isolates all OS-specific process management (signals, process groups, Job Objects, alive checks, zombie cleanup). | `class PlatformOps(Protocol)` with methods: `create_process_group(popen: Popen) -> None`, `terminate_tree(pid: int, grace_period: float) -> ProcessExitInfo`, `kill_tree(pid: int) -> ProcessExitInfo`, `is_alive(pid: int) -> bool`, `get_exit_info(pid: int) -> ProcessExitInfo`. Implementations: `class PosixOps(PlatformOps)` (Linux+macOS), `class WindowsOps(PlatformOps)` (Windows). Factory: `def get_platform_ops() -> PlatformOps`. |
| `src/scieasy/engine/runners/process_handle.py` | **ProcessHandle and ProcessRegistry.** See ADR-019 for complete specification. Created as a separate file rather than in `process_mgr.py` because it is an engine-layer concern, not a block-layer concern. | See ADR-019 |
| `src/scieasy/engine/runners/process_monitor.py` | **ProcessMonitor background coroutine.** See ADR-019 for complete specification. | See ADR-019 |

#### Rewritten files

| File | Current state | New state | Detailed changes |
|---|---|---|---|
| `src/scieasy/blocks/code/runners/python_runner.py` | `execute_inline()`: calls `exec(script, namespace)` in-process (line 27). `execute_script()`: calls `importlib.util.spec_from_file_location()` + `spec.loader.exec_module()` in-process (lines 62–67). | Both methods prepare an invocation payload and delegate to `spawn_block_process()`. The actual `exec()` / `importlib` logic moves to `worker.py` and only runs inside the subprocess. | `execute_inline(self, script, namespace) -> dict`: **remove** `exec(script, namespace)` call. **Replace with**: build payload `{"mode": "inline", "script": script, "inputs": serialise_refs(namespace)}`, call `spawn_block_process(["python", "-m", "scieasy.engine.runners.worker"], ...)`, read stdout for output refs, return deserialised outputs. The `exec()` call itself moves to `worker.py`. `execute_script(self, script_path, entry_function, inputs, config) -> dict`: **remove** `importlib.util.spec_from_file_location()` + `exec_module()` calls. **Replace with**: build payload `{"mode": "script", "script_path": str(script_path), "entry_function": entry_function, "inputs": serialise_refs(inputs), "config": config}`, call `spawn_block_process(...)`, read stdout. The `importlib` loading moves to `worker.py`. **Remove** import of `importlib.util` (line 2). **Add** imports: `from scieasy.engine.runners.process_handle import spawn_block_process`. |
| `src/scieasy/blocks/code/runners/r_runner.py` | Both methods raise `NotImplementedError` with message suggesting `rpy2` (lines 17–18, 29–30). | **Remove** all `rpy2` references from docstring and error messages. Implement both methods using subprocess calling `Rscript`. | `execute_inline(self, script, namespace) -> dict`: write `script` to a temp `.R` file, write inputs to temp JSON files, build a wrapper R script that reads JSON inputs, `source()`s the user script, writes JSON outputs. Call `spawn_block_process(["Rscript", wrapper_path, ...])`. Parse output JSON. `execute_script(self, script_path, entry_function, inputs, config) -> dict`: write inputs to temp JSON files, build wrapper R script that calls `source(script_path)` then calls `entry_function(inputs, config)`, writes output JSON. Call `spawn_block_process(["Rscript", wrapper_path, ...])`. Parse output JSON. **Remove** docstring line "Planned backends: rpy2 (in-process)". **Add** docstring: "Executes R code in an isolated Rscript subprocess." |
| `src/scieasy/blocks/code/runners/julia_runner.py` | Both methods raise `NotImplementedError` with message suggesting `juliacall` (lines 17–18, 29–30). | **Remove** all `juliacall` references. Implement both methods using subprocess calling `julia`. | Same pattern as `RRunner`: write inputs to temp JSON, build wrapper Julia script, call `spawn_block_process(["julia", wrapper_path, ...])`, parse output JSON. **Remove** docstring line "Planned backends: juliacall (in-process)". **Add** docstring: "Executes Julia code in an isolated julia subprocess." |
| `src/scieasy/engine/runners/local.py` | All three methods (`run`, `check_status`, `cancel`) raise `NotImplementedError` (lines 37, 52, 62). Class docstring says "in the local process or as a local subprocess" (line 9). | **Implement** all three methods using subprocess execution via `spawn_block_process()`. Remove "in the local process" from docstring. | `run(self, block, inputs, config) -> dict`: build invocation payload from `block.__class__`, `inputs` (converted to `StorageReference` dicts), and `config`. Call `spawn_block_process()` to get `ProcessHandle`. Await subprocess completion by reading stdout. Parse output `StorageReference` JSON. Return output mapping. Store `ProcessHandle` in `self._active_runs: dict[str, ProcessHandle]` keyed by `run_id`. `check_status(self, run_id) -> Any`: look up `ProcessHandle` from `self._active_runs[run_id]`. Call `handle.is_alive()`. If alive, return `BlockState.RUNNING`. If exited, return `handle.exit_info()`. `cancel(self, run_id) -> None`: look up `ProcessHandle`. Call `await handle.terminate(grace_period_sec=5.0)`. Remove from `self._active_runs`. **Add** instance attribute: `self._active_runs: dict[str, ProcessHandle] = {}`. **Add** imports: `from scieasy.engine.runners.process_handle import ProcessHandle, spawn_block_process`. **Change** class docstring from "in the local process or as a local subprocess" to "as an isolated local subprocess". |
| `src/scieasy/blocks/code/code_block.py` | `run()` (lines 38–77): directly calls `runner.execute_inline()` or `runner.execute_script()`, performs state transitions (`self.transition(BlockState.RUNNING)`, `self.transition(BlockState.DONE)`), and handles errors. | `run()` no longer performs state transitions directly (the engine/scheduler manages state transitions based on subprocess exit). The method prepares the execution request and returns it. State transitions move to the scheduler layer. | `run(self, inputs, config) -> dict`: **remove** `self.transition(BlockState.RUNNING)` (line 42) and `self.transition(BlockState.DONE)` (line 73) — state transitions are managed by the scheduler based on subprocess lifecycle, not by the block itself. **Remove** try/except that catches `Exception` and calls `self.transition(BlockState.ERROR)` (lines 43, 75–77) — error detection is based on subprocess exit code, handled by the scheduler. The method becomes a pure function: prepare inputs, select runner, call runner method, return results. **Note**: `_prepare_inputs()` (lines 79–112) logic for `InputDelivery.MEMORY` (calling `value.to_memory()`) moves inside the subprocess worker, because `to_memory()` loads data into the subprocess's memory, not the engine's. The engine-side `_prepare_inputs()` changes to: for all delivery modes, convert `ViewProxy` to `StorageReference` dict (lightweight). The subprocess-side `worker.py` handles the actual delivery mode dispatch. |

#### Modified files

| File | Current state | Changes | Detailed field/parameter changes |
|---|---|---|---|
| `src/scieasy/blocks/app/bridge.py` | `launch()` (line 75) returns `subprocess.Popen[bytes]`. The Popen handle is created with `subprocess.Popen([command, str(exchange_dir)], cwd=..., stdout=PIPE, stderr=PIPE)` (lines 81–86). Handle is returned but never stored or registered by caller. | `launch()` must use `spawn_block_process()` and return `ProcessHandle` instead of raw `Popen`. | `launch(self, command: str, exchange_dir: Path) -> ProcessHandle`: **change return type** from `subprocess.Popen[bytes]` to `ProcessHandle`. **Replace** `subprocess.Popen(...)` call with `spawn_block_process(block_id=..., command=[command, str(exchange_dir)], resource_request=ResourceRequest(), cwd=str(exchange_dir))`. **Add** `block_id: str` parameter to `launch()` signature (needed for `ProcessHandle` registration). **Add** import: `from scieasy.engine.runners.process_handle import ProcessHandle, spawn_block_process`. **Remove** import: `import subprocess` (line 6, no longer directly used). The `ExternalAppBridge` protocol (line 12) must update `launch()` signature to return `ProcessHandle` and accept `block_id`. |
| `src/scieasy/blocks/app/app_block.py` | `run()` (lines 48–102): calls `bridge.launch(command, exchange_dir)` (line 75) but discards the return value. Error handling: bare `except Exception` → `self.transition(BlockState.ERROR)` → `raise` (lines 100–102). | Must store the `ProcessHandle` from `bridge.launch()`. Must pass `block_id` to `bridge.launch()`. State transitions move to scheduler (same as CodeBlock). | `run()`: **change** line 75 from `bridge.launch(command, exchange_dir)` to `self._process_handle = bridge.launch(block_id=self._block_id, command=command, exchange_dir=exchange_dir)`. **Add** instance attribute: `self._process_handle: ProcessHandle | None = None`. **Add** `self._block_id: str` parameter to `__init__()` (or set by the scheduler before `run()`). **Remove** `self.transition(BlockState.RUNNING)` (line 57), `self.transition(BlockState.PAUSED)` (line 74), `self.transition(BlockState.RUNNING)` (line 94), `self.transition(BlockState.DONE)` (line 97) — state transitions managed by scheduler. **Remove** try/except ERROR transition (lines 100–102) — error detection via subprocess exit code. |
| `src/scieasy/blocks/app/watcher.py` | `wait_for_output()` (lines 47–72): polls for files only. No process awareness. Timeout raises `TimeoutError`. | **Add** optional `process_handle: ProcessHandle | None` parameter to `__init__()` and `wait_for_output()`. When a process handle is provided, each poll iteration also checks `process_handle.is_alive()`. If the process has exited and no output files are detected, raise a new `ProcessExitedWithoutOutputError` instead of continuing to poll forever. | `__init__()`: **add** parameter `process_handle: ProcessHandle | None = None` after `poll_interval`. Store as `self._process_handle`. `wait_for_output()`: **add** inside the `while self._running:` loop (after `new_files` check, before timeout check): `if self._process_handle is not None and not await self._process_handle.is_alive(): exit_info = await self._process_handle.exit_info(); if not new_files: raise ProcessExitedWithoutOutputError(f"External process exited (code={exit_info.exit_code}) without producing output files matching {self.patterns}")`. **Add** new exception class at module level: `class ProcessExitedWithoutOutputError(RuntimeError): pass`. **Note**: `wait_for_output()` becomes `async` because `ProcessHandle.is_alive()` is async. This cascading change affects `AppBlock.run()` (must `await watcher.wait_for_output()`). |
| `src/scieasy/blocks/app/process_mgr.py` | Contains only a docstring: `"""External process lifecycle management (subprocess)."""` (line 1). Completely empty. | This file is superseded by `engine/runners/process_handle.py` and `engine/runners/process_monitor.py` (engine-layer concerns). | **Option A**: Delete the file entirely and remove from `__init__.py` imports. **Option B**: Keep as a thin re-export: `from scieasy.engine.runners.process_handle import ProcessHandle, ProcessRegistry`. **Recommended**: Option A (delete). The process lifecycle is an engine concern, not a block concern. Blocks interact with processes only through the `ProcessHandle` returned by `bridge.launch()`. |
| `src/scieasy/engine/runners/base.py` | `BlockRunner` protocol defines `run()` returning `dict[str, Any]` (line 16), `check_status()` returning `Any` (line 40), `cancel()` returning `None` (line 55). | `run()` return type changes to include `ProcessHandle` for lifecycle tracking. `check_status()` return type becomes structured. | `run()`: **change** return type from `dict[str, Any]` to `tuple[str, ProcessHandle]` where the `str` is a `run_id`. The actual output data is not returned by `run()` — instead, the scheduler reads outputs from storage after the subprocess exits. **Alternative**: `run()` returns a `RunHandle` dataclass containing `run_id: str`, `process_handle: ProcessHandle`, and a `result_future: asyncio.Future[dict[str, Any]]` that resolves when the subprocess completes. **Recommended**: the `RunHandle` approach, because it allows the scheduler to fire-and-forget and await the future when ready. **Add** new dataclass: `@dataclass class RunHandle: run_id: str; process_handle: ProcessHandle; result: asyncio.Future[dict[str, Any]]`. `check_status()`: **change** return type from `Any` to `BlockState`. `cancel()`: no signature change, but the docstring should note that cancellation is via `ProcessHandle.terminate()`. |
| `src/scieasy/blocks/base/block.py` | `_VALID_TRANSITIONS` dict (lines 13–20) defines allowed state transitions. No CANCELLED or SKIPPED states. | Updated in ADR-018 (see below). Listed here for completeness as a cross-ADR dependency. | See ADR-018 detailed impact scope. |
| `src/scieasy/engine/events.py` | `EngineEvent` dataclass with `event_type: str` (line 19). No defined event type constants. `EventBus` with `emit()`, `subscribe()`, `unsubscribe()` all raising `NotImplementedError`. | **Add** event type constants for `PROCESS_SPAWNED` and `PROCESS_EXITED`. EventBus implementation is part of ADR-018 (shared dependency). | **Add** at module level: `PROCESS_SPAWNED = "process_spawned"`, `PROCESS_EXITED = "process_exited"`. These are imported by `spawn_block_process()` and `ProcessMonitor` respectively. Full event type enumeration is in ADR-018. |

#### Documentation impact

| Document | Current state | Required changes |
|---|---|---|
| `docs/architecture/ARCHITECTURE.md` Section 5.1 (Block base class, lines 362–414) | Shows `Block.run()` being called directly, with no mention of subprocess isolation. | **Update** to describe that `run()` executes inside a subprocess, not in the engine process. Add a note that block authors do not need to change their code — the subprocess wrapper is transparent. |
| `docs/architecture/ARCHITECTURE.md` Section 5.3 (Block categories) | `CodeBlock` section (lines 563–784) describes `exec()` for inline mode, `importlib` for script mode, `rpy2` for R, `juliacall` for Julia. Mentions "`exec()` with a sandboxed namespace (inline), or subprocess / importlib for script mode" (line 781) and "R: via rpy2 bridge or subprocess calling Rscript" (line 782). | **Rewrite** the code runners paragraph (lines 780–783) to state all execution is via subprocess. **Remove** references to `exec()`, `importlib`, `rpy2`, `juliacall` as in-process execution paths. **Update** the framework bridge implementation code example (lines 704–772) to show subprocess delegation instead of direct runner calls. |
| `docs/architecture/ARCHITECTURE.md` Section 6.1 (DAG scheduler, lines 1024–1056) | `execute()` example shows direct block invocation: `result = await self.run_auto(block, inputs)` (line 1051). | **Update** to show subprocess-based execution: scheduler calls `runner.run()` which returns a `RunHandle`, then awaits `handle.result`. |
| `docs/architecture/ARCHITECTURE.md` Section 6.7 (Remote execution, lines 1209–1231) | `BlockRunner` protocol shows `async def run(self, block, inputs, config) -> dict` (line 1216). | **Update** return type to `RunHandle`. **Update** `LocalRunner` description from "Runs blocks in-process or as local subprocesses" to "Runs blocks as isolated local subprocesses". |
| `docs/architecture/ARCHITECTURE.md` Appendix C.3 (Sandbox policy, lines 1832–1847) | Lists `SandboxPolicy` enum with `NONE` as current default. States "Not implementing in v1". | **Update** to note that `SUBPROCESS` is now the universal default (no longer `NONE`). `NONE` is removed as an option. `CONTAINER` and `WASM` remain future. |
| `docs/architecture/ARCHITECTURE.md` Section 11 (Technology stack, lines 1690–1708) | Lists "Process management: subprocess + watchdog" (line 1700). | **Add** "Process lifecycle: ProcessHandle + ProcessRegistry + ProcessMonitor" to the table. **Note** platform abstraction: "Cross-platform process management via platform.py (POSIX signals + process groups / Windows Job Objects + TerminateProcess)". |

---

## ADR-018: Block cancellation, graceful workflow degradation, and event-driven runtime

**Status**: proposed
**Date**: 2026-04-03

### Context

The original architecture defined only the happy path for block execution. Specifically:

- `BlockState` enum (`src/scieasy/blocks/base/state.py:8–16`) defines six states: `IDLE`, `READY`, `RUNNING`, `PAUSED`, `DONE`, `ERROR`. There is no state for user-initiated cancellation or for blocks that cannot execute due to upstream failure.

- `_VALID_TRANSITIONS` (`src/scieasy/blocks/base/block.py:13–20`) defines the state machine:
  ```
  IDLE    → {READY, ERROR}
  READY   → {RUNNING, ERROR}
  RUNNING → {DONE, PAUSED, ERROR}
  PAUSED  → {RUNNING, ERROR}
  DONE    → {IDLE}
  ERROR   → {IDLE}
  ```
  No transition leads to a "cancelled" or "skipped" state.

- `DAGScheduler` (`src/scieasy/engine/scheduler.py:8–54`) is a skeleton with `execute()`, `pause()`, `resume()`, and `save_checkpoint()` all raising `NotImplementedError`. There is no `cancel_block()` or `cancel_workflow()` method. The architecture document describes `execute()` as a simple for-loop over topological sort (ARCHITECTURE.md lines 1039–1056), with no ability to respond to external signals during execution.

- `EventBus` (`src/scieasy/engine/events.py:25–62`) defines `emit()`, `subscribe()`, `unsubscribe()` all raising `NotImplementedError`. No event types are defined. The bus is not connected to any component.

- WebSocket handler (`src/scieasy/api/ws.py:8–28`) is a skeleton raising `NotImplementedError`. Only server→client events are mentioned in the architecture document (ARCHITECTURE.md lines 1457–1480). No client→server cancel messages are defined.

- `LineageRecord` (`src/scieasy/core/lineage/record.py:12–35`) records only successful executions: `output_hashes`, `duration_ms`, etc. There is no field for termination reason, partial outputs, or skip reasons.

- `WorkflowCheckpoint` (`src/scieasy/engine/checkpoint.py:12–24`) stores `block_states: dict[str, str]` but was designed for only the original six states.

Users need to:
1. Cancel blocks that run too long (e.g., Cellpose on a large batch).
2. Cancel workflows waiting for external software they no longer need.
3. Have the system respond predictably when an external application crashes or is killed via the OS task manager.
4. See unaffected parallel branches continue executing after a cancellation.
5. Understand why downstream blocks did not execute (clear skip reasons).

### Discussion points and resolution

| # | Topic | Options discussed | Final decision |
|---|---|---|---|
| 1 | Should there be a `TIMED_OUT` state separate from `ERROR`? | (A) Add `TIMED_OUT` for automatic timeout detection. (B) No automatic timeout; only `CANCELLED` (user-initiated) and `ERROR` (crash/failure). | **Decision: (B).** No automatic timeouts. AppBlocks delegate to external software where a 30-minute session is normal. Scientific computations vary wildly in duration. False timeouts interrupt valid work and erode trust. Users cancel manually when they decide something is stuck. |
| 2 | Should downstream blocks enter `ERROR` or a new `SKIPPED` state? | (A) Downstream blocks enter `ERROR`. (B) New `SKIPPED` state with diagnostic reason. | **Decision: (B).** `ERROR` implies something went wrong in that block. `SKIPPED` communicates "this block did not run because its prerequisites were not met." Different semantics → different user response (ERROR → investigate this block; SKIPPED → investigate the upstream block). |
| 3 | Should cancel propagation ask the user about each downstream block? | (A) Prompt user for each downstream block. (B) Deterministic propagation: if required inputs cannot be satisfied, skip automatically. | **Decision: (B).** The propagation is deterministic — if block X produces no output, nothing that needs X's output can run. No decision to make. |
| 4 | Should the scheduler remain a synchronous for-loop? | (A) Keep for-loop, add cancellation check between iterations. (B) Rewrite as event-driven loop. | **Decision: (B).** An event-driven scheduler can react to cancellation, errors, and process death at any time, not just at block boundaries. This also enables true parallel branch execution (the for-loop model is inherently sequential). |
| 5 | Which runtime components need event-driven architecture? | (A) Only DAGScheduler. (B) All runtime components that react to state changes. | **Decision: (B).** The EventBus becomes the backbone of the runtime. DAGScheduler, ResourceManager, ProcessRegistry, WebSocket handler, LineageRecorder, and CheckpointManager all subscribe to events. |
| 6 | What happens when a user cancels an AppBlock while the external app is running? | (A) Ask user to save work first. (B) Kill the process immediately; data loss is the user's responsibility. | **Decision: (B).** Cancellation is immediate. The user clicked cancel. No "save your work?" prompt. External process is killed via `ProcessHandle.terminate()`. |
| 7 | Should the framework detect process crashes (not just cancellation)? | (A) No — only handle user-initiated cancellation. (B) Detect unexpected process exit (crash, OOM-kill, user killing via task manager). | **Decision: (B).** The `ProcessMonitor` (ADR-019) detects unexpected process death. If an AppBlock's external app is killed via the OS task manager, the framework detects it, checks for output files, and transitions to ERROR or DONE accordingly. The runtime never crashes because an external process died. |

### Decision

#### Extended state machine

Two new states added to `BlockState`:

| State | Value | Meaning | Triggered by |
|---|---|---|---|
| `CANCELLED` | `"cancelled"` | User explicitly requested termination of this block | User action via WebSocket `cancel_block` message or REST `POST /api/workflows/{id}/blocks/{block_id}/cancel` |
| `SKIPPED` | `"skipped"` | Block cannot execute because a required upstream block did not produce output | Automatic propagation by DAGScheduler when an upstream block enters `ERROR`, `CANCELLED`, or `SKIPPED` without producing required outputs |

**New state transition table** (replaces `_VALID_TRANSITIONS` in `block.py:13–20`):

```
IDLE      → { READY, SKIPPED, ERROR }
READY     → { RUNNING, SKIPPED, ERROR }
RUNNING   → { DONE, PAUSED, ERROR, CANCELLED }
PAUSED    → { RUNNING, ERROR, CANCELLED }
DONE      → { IDLE }
ERROR     → { IDLE }
CANCELLED → { IDLE }
SKIPPED   → { IDLE }
```

**State diagram:**

```
                          ┌──────────────────────────────────────────────┐
                          │               WORKFLOW RESET                  │
                          │  (only when starting a new run of the same   │
                          │   workflow — all blocks return to IDLE)       │
                          └──┬─────┬─────────┬───────────┬──────────────┘
                             │     │         │           │
                             ▼     ▼         ▼           ▼
          ┌───────────── IDLE ◄── DONE    ERROR ──► IDLE
          │                │                ▲
          │                ▼                │
          │    ┌──── READY ────────────► ERROR
          │    │       │                    ▲
          │    │       ▼                    │
          │    │   RUNNING ──────┬───── ERROR
          │    │       │        │          ▲
          │    │       ▼        │          │
          │    │   PAUSED ──────┤───── ERROR
          │    │       │        │
          │    │       │        ▼
          │    │       │      DONE ──────► IDLE
          │    │       │
          │    │       │    (user cancels)
          │    │       └─────────────► CANCELLED ──► IDLE
          │    │                            ▲
          │    │                            │
          │    │       (user cancels        │
          │    │        while RUNNING) ─────┘
          │    │
          │    │    (upstream failed/cancelled,
          │    │     required inputs unsatisfiable)
          │    └──────────────────────► SKIPPED ────► IDLE
          │                                ▲
          └────────────────────────────────┘
              (upstream failed/cancelled
               before block left IDLE)
```

**Terminal states for a single workflow run**: `DONE`, `ERROR`, `CANCELLED`, `SKIPPED`. All four can transition back to `IDLE` only when the workflow is reset for a new execution.

#### No automatic timeout

The framework does not impose automatic timeouts on block execution. Rationale:

- AppBlocks delegate to external software where the user is actively working. A 30-minute session in ElMAVEN picking LC-MS peaks is normal operation, not a timeout.
- Scientific computations vary wildly in duration. Cellpose on 1000 high-resolution images may legitimately take hours. A training run may take days.
- False timeouts are worse than no timeouts: they interrupt valid work, lose partial results, and erode user trust in the framework.
- The user is the best judge of whether a process is stuck. When they decide it is, they cancel manually.

If per-block user-configurable timeouts are desired in the future, they can be added as an optional `timeout_sec: int | None = None` field on `Block` with `None` meaning "no timeout." The timeout would trigger the same cancellation flow (emit `CANCEL_BLOCK_REQUEST`). This is a future enhancement, not an architectural requirement.

#### Cancellation flow

**Single block cancellation:**

```
1. User clicks "Cancel" on Block X (currently RUNNING or PAUSED)
   │
   ▼
2. Frontend sends WebSocket message:
   {"type": "cancel_block", "block_id": "cellpose_001", "workflow_id": "wf_001"}
   │
   ▼
3. WebSocket handler receives message, emits to EventBus:
   EventBus.emit(EngineEvent(
       event_type=CANCEL_BLOCK_REQUEST,
       block_id="cellpose_001",
       data={"workflow_id": "wf_001"}
   ))
   │
   ├──────────────────────────────────────────────────────────────────┐
   │                                                                  │
   ▼                                                                  ▼
4a. ProcessRegistry receives event:                    4b. DAGScheduler receives event:
    handle = registry.get_handle("cellpose_001")           scheduler.handle_cancel("cellpose_001")
    await handle.terminate(grace_period_sec=5.0)           │
    │                                                      ▼
    │ On Linux/macOS:                                  5. Scheduler marks cellpose_001
    │   SIGTERM to process group                          as CANCELLED:
    │   → wait up to 5s                                    block_states["cellpose_001"] = CANCELLED
    │   → SIGKILL if still alive                           │
    │                                                      ▼
    │ On Windows:                                      6. Scheduler propagates SKIPPED:
    │   TerminateProcess on Job Object                     Identify all downstream blocks whose
    │   (no grace period — immediate)                      required inputs depend on cellpose_001's
    │                                                      outputs (directly or transitively).
    ▼                                                      │
4c. ProcessMonitor detects process exit:                   For each such block:
    emit PROCESS_EXITED event                               block_states[block_id] = SKIPPED
    │                                                       skip_reason[block_id] =
    ▼                                                         "upstream 'cellpose_001' cancelled"
4d. ResourceManager receives                               │
    CANCEL_BLOCK_REQUEST or PROCESS_EXITED:                Continue executing unaffected
    Release resources held by cellpose_001:                 parallel branches.
    gpu_slots += 1                                         │
    memory_budget += 4.0 GB                                ▼
    │                                                  7. Scheduler emits state change events:
    ▼                                                      emit BLOCK_CANCELLED(cellpose_001)
4e. LineageRecorder receives                               emit BLOCK_SKIPPED(napari_review_001,
    BLOCK_CANCELLED event:                                   reason="upstream cancelled")
    Write lineage record:                                  emit BLOCK_SKIPPED(srs_extract_001,
    termination="cancelled"                                  reason="upstream cancelled")
    duration_ms=elapsed since start                        │
    output_hashes=[] (no outputs)                          ▼
    │                                                  8. WebSocket handler receives state events:
    ▼                                                      Push to frontend:
4f. CheckpointManager receives                             {"type": "block_state",
    BLOCK_CANCELLED event:                                  "block_id": "cellpose_001",
    Save checkpoint with updated states.                    "state": "cancelled"}
                                                           {"type": "cancel_propagation",
                                                            "cancelled_block": "cellpose_001",
                                                            "skipped_blocks": [
                                                              {"block_id": "napari_review_001",
                                                               "reason": "upstream cancelled"},
                                                              {"block_id": "srs_extract_001",
                                                               "reason": "upstream cancelled"}
                                                            ],
                                                            "unaffected_blocks": [
                                                              "raman_preprocess_001",
                                                              "load_raman_001"
                                                            ]}
```

**Workflow-level cancellation:**

```
1. User clicks "Cancel Workflow"
   → emit CANCEL_WORKFLOW_REQUEST(workflow_id)
   → For each block in RUNNING or PAUSED state:
       emit CANCEL_BLOCK_REQUEST(block_id)
       (triggers the single-block flow above)
   → For each block in IDLE or READY state:
       block_states[block_id] = SKIPPED
       skip_reason = "workflow cancelled"
```

#### Downstream propagation logic (detailed)

When a block enters a terminal-without-output state (`ERROR` or `CANCELLED`):

```python
def propagate_skipped(self, failed_block_id: str, reason: str) -> list[str]:
    """Mark all unreachable downstream blocks as SKIPPED.

    Returns list of block_ids that were marked SKIPPED.
    """
    skipped = []
    # Get output ports that produced no data
    missing_ports = self._get_empty_output_ports(failed_block_id)

    # Find all downstream blocks connected to those empty ports
    queue = self._get_downstream_blocks(failed_block_id, missing_ports)

    while queue:
        block_id = queue.pop(0)
        if self.block_states[block_id] in (DONE, ERROR, CANCELLED, SKIPPED):
            continue  # already in a terminal state

        # Check: can this block's required inputs still be satisfied?
        unsatisfied = self._get_unsatisfied_required_inputs(block_id)
        if unsatisfied:
            self.block_states[block_id] = SKIPPED
            self.skip_reasons[block_id] = (
                f"Required input(s) {unsatisfied} cannot be satisfied: "
                f"upstream block '{failed_block_id}' {reason}"
            )
            skipped.append(block_id)

            # This block also produces no output → propagate further
            further_missing = self._get_all_output_ports(block_id)
            further_downstream = self._get_downstream_blocks(block_id, further_missing)
            queue.extend(further_downstream)

    return skipped
```

**Critical rule**: the propagation logic is identical for `ERROR` and `CANCELLED`. The scheduler does not distinguish between them — it only checks: "does this block have all required inputs satisfied?" This means:

- A crashed AppBlock (ERROR) and a user-cancelled AppBlock (CANCELLED) trigger the same downstream behaviour.
- Optional inputs do not trigger SKIPPED. If a block has one required and one optional input, and only the optional input's upstream fails, the block is still schedulable.

#### AppBlock-specific scenarios

| Scenario | Detection | Framework response |
|---|---|---|
| External app running normally, user working | `ProcessHandle.is_alive()` = True, no output files yet | Do nothing. Wait. |
| External app finishes, writes output files | `ProcessHandle.is_alive()` = False (exit code 0), FileWatcher detects files | → `DONE`. Collect output files. Continue workflow. |
| External app finishes, does NOT write output files | `ProcessHandle.is_alive()` = False (exit code 0), FileWatcher detects no matching files | → `ERROR` with message "External process exited normally (code 0) but did not produce expected output files matching patterns {patterns}". Propagate `SKIPPED` downstream. |
| External app crashes (segfault, unhandled exception) | `ProcessHandle.is_alive()` = False (exit code ≠ 0), no output files | → `ERROR` with message "External process exited with code {code}". Propagate `SKIPPED` downstream. |
| User kills external app via OS task manager | `ProcessMonitor` detects PID gone. `ProcessHandle.is_alive()` = False. | Same as crash: → `ERROR` with message "External process terminated unexpectedly (exit code {code})". Propagate `SKIPPED` downstream. |
| User cancels AppBlock via SciEasy UI | `CANCEL_BLOCK_REQUEST` → `ProcessHandle.terminate()` kills external app | → `CANCELLED`. External process killed immediately. No "save your work?" prompt. Propagate `SKIPPED` downstream. |
| External app crashes AFTER writing output files | `ProcessHandle.is_alive()` = False (exit code ≠ 0), but FileWatcher detected files | → `DONE`. Output files exist and are valid. The crash was after the useful work completed. (Edge case: partially written files. The block author's `collect()` method should validate file integrity.) |

#### Event-driven runtime architecture

The `EventBus` becomes the backbone of the runtime. All runtime components communicate through events rather than direct method calls. This decouples components and enables the system to react to cancellation, errors, and process death at any point during execution.

**Complete event type catalogue:**

| Event type constant | Emitted by | Payload (`data` dict fields) | Description |
|---|---|---|---|
| `BLOCK_READY` | `DAGScheduler` | `block_id: str` | Block's required inputs are all satisfied; ready to execute. |
| `BLOCK_RUNNING` | `DAGScheduler` | `block_id: str`, `run_id: str` | Block dispatched to runner, subprocess started. |
| `BLOCK_PAUSED` | `DAGScheduler` | `block_id: str`, `reason: str` | Block entered PAUSED state (waiting for external app or user interaction). |
| `BLOCK_DONE` | `DAGScheduler` | `block_id: str`, `output_refs: dict[str, str]`, `duration_ms: int` | Block completed successfully with output references. |
| `BLOCK_ERROR` | `DAGScheduler` | `block_id: str`, `error_detail: str`, `exit_code: int | None` | Block failed with error. |
| `BLOCK_CANCELLED` | `DAGScheduler` | `block_id: str` | Block was cancelled by user. |
| `BLOCK_SKIPPED` | `DAGScheduler` | `block_id: str`, `skip_reason: str`, `caused_by: str` | Block skipped because upstream did not produce required output. `caused_by` = block_id of the root cause. |
| `CANCEL_BLOCK_REQUEST` | WebSocket handler, REST endpoint | `block_id: str`, `workflow_id: str` | User requests cancellation of a specific block. |
| `CANCEL_WORKFLOW_REQUEST` | WebSocket handler, REST endpoint | `workflow_id: str` | User requests cancellation of the entire workflow. |
| `PROCESS_SPAWNED` | `spawn_block_process()` | `block_id: str`, `pid: int`, `resource_request: ResourceRequest` | A subprocess was created for a block. |
| `PROCESS_EXITED` | `ProcessMonitor` | `block_id: str`, `exit_info: ProcessExitInfo` | A subprocess exited (normally, crashed, or killed). |
| `WORKFLOW_STARTED` | `DAGScheduler` | `workflow_id: str` | Workflow execution began. |
| `WORKFLOW_COMPLETED` | `DAGScheduler` | `workflow_id: str`, `final_states: dict[str, str]` | All blocks reached terminal states (DONE/ERROR/CANCELLED/SKIPPED). |
| `CHECKPOINT_SAVED` | `CheckpointManager` | `workflow_id: str`, `checkpoint_path: str` | A checkpoint was persisted to disk. |

**Subscription matrix — who listens to what:**

| Subscriber | `BLOCK_DONE` | `BLOCK_ERROR` | `BLOCK_CANCELLED` | `BLOCK_SKIPPED` | `CANCEL_BLOCK_REQUEST` | `CANCEL_WORKFLOW_REQUEST` | `PROCESS_SPAWNED` | `PROCESS_EXITED` |
|---|---|---|---|---|---|---|---|---|
| **DAGScheduler** | ✓ schedule next | ✓ propagate SKIPPED | ✓ propagate SKIPPED | — | ✓ initiate cancel | ✓ cancel all | — | ✓ update block state |
| **ResourceManager** | ✓ release | ✓ release | ✓ release | — | — | — | ✓ record allocation | ✓ release |
| **ProcessRegistry** | — | — | — | — | ✓ terminate process | ✓ terminate all | ✓ register handle | ✓ deregister handle |
| **WebSocket handler** | ✓ push to client | ✓ push to client | ✓ push to client | ✓ push to client | — | — | — | — |
| **LineageRecorder** | ✓ write record | ✓ write record | ✓ write record | ✓ write record | — | — | — | — |
| **CheckpointManager** | ✓ save | ✓ save | ✓ save | ✓ save | — | — | — | — |

### Alternatives considered

- **`TIMED_OUT` as a separate state**: adds a state that cannot be reliably distinguished from "my computation is just slow." Since we decided against automatic timeouts, the state has no trigger. If user-configurable timeouts are added later, the timeout action is semantically identical to a cancel — using `CANCELLED` with a reason field (`"cancelled: user-configured timeout exceeded"`) is sufficient. No separate state needed.

- **Downstream blocks enter `ERROR` instead of `SKIPPED`**: `ERROR` implies something went wrong inside that block. `SKIPPED` accurately communicates "this block did not run because its prerequisites were not met." Different semantics lead to different user actions: ERROR → look at this block's logs; SKIPPED → look at the upstream block that caused it.

- **Cancel propagation stops the entire workflow**: too aggressive. A multi-branch workflow (LC-MS + Raman + IF) should not lose the Raman and IF results because the user cancelled one LC-MS block. Only the dependent subgraph is affected.

- **Keep the synchronous for-loop scheduler, add cancellation checks between iterations**: a for-loop model cannot react to events during block execution — it only checks between blocks. If a Cellpose block runs for 2 hours, the cancel request sits in a queue for 2 hours. Event-driven scheduling reacts immediately.

- **Direct method calls between components instead of EventBus**: tight coupling. Adding a new subscriber (e.g., a metrics collector) requires modifying the scheduler. EventBus allows adding subscribers without changing emitters. Also enables testing components in isolation by mocking the bus.

### Consequences

- `BlockState` grows from 6 to 8 states. All state-dependent code must handle `CANCELLED` and `SKIPPED`.
- The DAGScheduler changes from a synchronous for-loop to an event-driven loop. This is a fundamental rewrite of the scheduler.
- Every block is cancellable at any time because of subprocess isolation (ADR-017). No cooperative cancellation protocol needed.
- `SKIPPED` propagation is deterministic and auditable — the reason chain traces back to the original `CANCELLED` or `ERROR` block.
- The EventBus becomes a critical runtime component. A bug in the EventBus can affect all subscribers. It must be well-tested and have clear error handling (a failing subscriber should not block event delivery to other subscribers).
- The runtime never crashes because an upstream block failed. Missing inputs are a normal condition that triggers `SKIPPED`, not an exception.

### Detailed impact scope

#### New files

| File | Contents | Key classes/functions |
|---|---|---|
| (None — all changes are modifications to existing files or new files already listed in ADR-017 and ADR-019) | | |

#### Rewritten files

| File | Current state | New state | Detailed changes |
|---|---|---|---|
| `src/scieasy/engine/scheduler.py` | Skeleton class (54 lines). `__init__()`, `execute()`, `pause()`, `resume()`, `set_state()`, `save_checkpoint()` all raise `NotImplementedError`. No `cancel_block()` or `cancel_workflow()` methods. | Fully event-driven scheduler. | **Rewrite entirely.** `__init__(self, workflow: WorkflowDefinition, event_bus: EventBus, runner: BlockRunner, resource_manager: ResourceManager) -> None`: store workflow graph, build internal DAG (via `build_dag()`), initialise `block_states: dict[str, BlockState]` (all IDLE), `skip_reasons: dict[str, str]` (empty), subscribe to events on `event_bus`. Subscriptions: `PROCESS_EXITED` → `self._on_process_exited`, `CANCEL_BLOCK_REQUEST` → `self._on_cancel_block`, `CANCEL_WORKFLOW_REQUEST` → `self._on_cancel_workflow`. `async execute(self) -> None`: emit `WORKFLOW_STARTED`. Scan for blocks whose required inputs are all satisfied → transition to READY → dispatch via `runner.run()` → transition to RUNNING. Enter event loop: await events from EventBus. On `BLOCK_DONE`: store output refs, scan for newly-ready blocks, dispatch them. On `BLOCK_ERROR`/`BLOCK_CANCELLED`: call `propagate_skipped()`, check if workflow is complete. On `WORKFLOW_COMPLETED`: break loop. `async _on_cancel_block(self, event: EngineEvent) -> None`: validate block is in RUNNING or PAUSED state. Call `runner.cancel(run_id)`. Transition block to CANCELLED. Call `propagate_skipped(block_id, "cancelled")`. Emit `BLOCK_CANCELLED`. `async _on_cancel_workflow(self, event: EngineEvent) -> None`: for each RUNNING/PAUSED block: emit `CANCEL_BLOCK_REQUEST`. For each IDLE/READY block: transition to SKIPPED, emit `BLOCK_SKIPPED`. `def propagate_skipped(self, failed_block_id: str, reason: str) -> list[str]`: implementation as described in "Downstream propagation logic" section above. **Add** `cancel_block(block_id)` and `cancel_workflow()` public methods (emit events). **Remove** `pause()` and `resume()` — these are not removed from the API but internally they now emit events rather than directly manipulating state. |
| `src/scieasy/engine/events.py` | `EngineEvent` dataclass (lines 12–22) with `event_type: str`, `block_id: str | None`, `data: dict`, `timestamp: datetime`. `EventBus` class (lines 25–62) with `emit()`, `subscribe()`, `unsubscribe()` all raising `NotImplementedError`. | Fully implemented EventBus with event type constants and async support. | **Add** event type constants at module level (13 constants as listed in the event catalogue above): `BLOCK_READY = "block_ready"`, `BLOCK_RUNNING = "block_running"`, `BLOCK_PAUSED = "block_paused"`, `BLOCK_DONE = "block_done"`, `BLOCK_ERROR = "block_error"`, `BLOCK_CANCELLED = "block_cancelled"`, `BLOCK_SKIPPED = "block_skipped"`, `CANCEL_BLOCK_REQUEST = "cancel_block_request"`, `CANCEL_WORKFLOW_REQUEST = "cancel_workflow_request"`, `PROCESS_SPAWNED = "process_spawned"`, `PROCESS_EXITED = "process_exited"`, `WORKFLOW_STARTED = "workflow_started"`, `WORKFLOW_COMPLETED = "workflow_completed"`, `CHECKPOINT_SAVED = "checkpoint_saved"`. **Implement** `EventBus`: `__init__()`: `self._subscribers: dict[str, list[Callable]] = defaultdict(list)`. `emit(event)`: iterate `self._subscribers[event.event_type]`, call each callback with the event. If a callback raises, log the error and continue (one failing subscriber must not block others). If callback is a coroutine, schedule it with `asyncio.create_task()`. `subscribe(event_type, callback)`: append callback to `self._subscribers[event_type]`. `unsubscribe(event_type, callback)`: remove callback from list. **Change** `EngineEvent.data` type annotation from `dict[str, Any]` to remain as-is (generic dict is intentional for flexibility), but **add** docstring specifying the expected payload fields per event type (referencing the event catalogue). |

#### Modified files

| File | Current state | Changes | Detailed field/parameter changes |
|---|---|---|---|
| `src/scieasy/blocks/base/state.py` | `BlockState` enum (lines 8–16): 6 values: `IDLE`, `READY`, `RUNNING`, `PAUSED`, `DONE`, `ERROR`. | **Add** two new enum values. | **Add** after `ERROR = "error"` (line 16): `CANCELLED = "cancelled"` and `SKIPPED = "skipped"`. Final enum has 8 values. No other changes to this file (other enums `ExecutionMode`, `BatchMode`, `InputDelivery`, `BatchErrorStrategy` are unchanged). |
| `src/scieasy/blocks/base/block.py` | `_VALID_TRANSITIONS` (lines 13–20): 6 entries. | **Replace** the entire dict with the new 8-entry transition table. | **Replace** lines 13–20 with: `_VALID_TRANSITIONS: dict[BlockState, set[BlockState]] = { BlockState.IDLE: {BlockState.READY, BlockState.SKIPPED, BlockState.ERROR}, BlockState.READY: {BlockState.RUNNING, BlockState.SKIPPED, BlockState.ERROR}, BlockState.RUNNING: {BlockState.DONE, BlockState.PAUSED, BlockState.ERROR, BlockState.CANCELLED}, BlockState.PAUSED: {BlockState.RUNNING, BlockState.ERROR, BlockState.CANCELLED}, BlockState.DONE: {BlockState.IDLE}, BlockState.ERROR: {BlockState.IDLE}, BlockState.CANCELLED: {BlockState.IDLE}, BlockState.SKIPPED: {BlockState.IDLE}, }`. **Add** import of `CANCELLED` and `SKIPPED` in the `from .state import ...` line if they are used directly (currently the import on line 10 imports the `BlockState` class, which is sufficient). |
| `src/scieasy/core/lineage/record.py` | `LineageRecord` dataclass (lines 12–35): 9 fields. No termination or skip fields. | **Add** 3 new fields for termination tracking. | **Add** after `batch_info` (line 35): `termination: str = "completed"` (allowed values: `"completed"`, `"cancelled"`, `"error"`, `"skipped"`), `partial_output_refs: list[str] | None = None` (storage references for any partial outputs produced before cancellation/error), `termination_detail: str | None = None` (human-readable detail: error message, skip reason, or cancellation source). |
| `src/scieasy/core/lineage/store.py` | `_CREATE_TABLE` SQL (lines 13–26): 9 columns. `write()` method (lines 53–82): inserts 9 values. `_row_to_record()` (lines 84–100): reads 9 columns. | **Add** 3 new columns to the schema. **Update** `write()`, `_row_to_record()`, and `query()`. | **Change** `_CREATE_TABLE` (lines 13–26): add 3 columns after `batch_info TEXT`: `termination TEXT NOT NULL DEFAULT 'completed'`, `partial_output_refs TEXT`, `termination_detail TEXT`. **Add** new index: `CREATE INDEX IF NOT EXISTS idx_lineage_termination ON lineage (termination);` (for filtering by termination type). **Change** `write()` (line 67): add `termination`, `partial_output_refs`, `termination_detail` to INSERT statement and values tuple. **Change** `_row_to_record()`: add parsing of 3 new columns from row tuple (indices 9, 10, 11). **Add** to `query()`: optional `termination: str | None = None` filter parameter. When provided, add `WHERE termination = ?` clause. |
| `src/scieasy/engine/checkpoint.py` | `WorkflowCheckpoint` dataclass (lines 12–24): 5 fields including `block_states: dict[str, str]`. | **Add** `skip_reasons` field. **Update** block_states documentation to include CANCELLED and SKIPPED as valid values. | **Add** after `config_snapshot` (line 24): `skip_reasons: dict[str, str] = field(default_factory=dict)` (mapping of block_id to skip reason string for all SKIPPED blocks). The `block_states` field already uses `str` values, so CANCELLED and SKIPPED are automatically valid. **Update** docstring to list all 8 valid state values. |
| `src/scieasy/engine/resources.py` | `ResourceManager` class (lines 27–72): `__init__()`, `acquire()`, `release()`, `available` property — all `raise NotImplementedError`. No EventBus integration. | **Add** EventBus subscription for automatic resource release. | **Change** `__init__()` signature: add `event_bus: EventBus | None = None` parameter. If provided, subscribe to `BLOCK_DONE`, `BLOCK_ERROR`, `BLOCK_CANCELLED`, `PROCESS_EXITED` events with `self._on_block_terminal` callback. **Add** method `_on_block_terminal(self, event: EngineEvent) -> None`: look up resource allocation for `event.block_id`, call `self.release(allocation)`. **Add** internal tracking: `self._allocations: dict[str, ResourceRequest] = {}` mapping block_id to its allocated resources. `acquire()` stores the allocation; `release()` removes it. |
| `src/scieasy/engine/batch.py` | `BatchExecutor` class (lines 8–99): `execute_serial()`, `execute_parallel()`, `execute_adaptive()` all `raise NotImplementedError`. | **Add** cancellation awareness to batch execution. | **Add** parameter to all three `execute_*` methods: `cancel_event: asyncio.Event | None = None`. When set, the executor checks `cancel_event.is_set()` before dispatching each item. If set, remaining items are not dispatched; results for unstarted items are marked as SKIPPED in the `BatchResult`. **Add** to returned `BatchResult` (needs new dataclass or dict): `skipped: list[int]` for item indices that were skipped due to cancellation. |
| `src/scieasy/api/ws.py` | Single function `websocket_handler()` (lines 8–28) raising `NotImplementedError`. | **Implement** WebSocket handler with bidirectional event routing. | **Rewrite** `websocket_handler(websocket, event_bus)`: `await websocket.accept()`. Start two concurrent tasks: (1) **Inbound loop**: `async for message in websocket: data = json.loads(message); if data["type"] == "cancel_block": event_bus.emit(EngineEvent(event_type=CANCEL_BLOCK_REQUEST, block_id=data["block_id"], data={"workflow_id": data["workflow_id"]})); elif data["type"] == "cancel_workflow": event_bus.emit(EngineEvent(event_type=CANCEL_WORKFLOW_REQUEST, data={"workflow_id": data["workflow_id"]}))`. (2) **Outbound loop**: subscribe to `BLOCK_READY`, `BLOCK_RUNNING`, `BLOCK_PAUSED`, `BLOCK_DONE`, `BLOCK_ERROR`, `BLOCK_CANCELLED`, `BLOCK_SKIPPED`, `WORKFLOW_COMPLETED` events. On each event, `await websocket.send_json(serialise_event(event))`. **Add** helper `serialise_event(event: EngineEvent) -> dict` that converts event to the WebSocket JSON protocol format. **Add** `cancel_propagation` message type: when `BLOCK_CANCELLED` is followed by one or more `BLOCK_SKIPPED` events, aggregate them into a single `cancel_propagation` message listing all skipped blocks and unaffected blocks. |
| `src/scieasy/api/schemas.py` | 10 Pydantic models for workflow, block, data, AI, and error responses (lines 1–119). No cancel-related schemas. | **Add** cancel-related request/response schemas. | **Add** after the Workflow section (after line 31): `class CancelBlockRequest(BaseModel): block_id: str; workflow_id: str`. `class CancelWorkflowRequest(BaseModel): workflow_id: str`. `class CancelBlockResponse(BaseModel): block_id: str; state: str; skipped_blocks: list[dict[str, str]] = []` (each dict has `block_id` and `reason`). `class CancelWorkflowResponse(BaseModel): workflow_id: str; cancelled_blocks: list[str] = []; skipped_blocks: list[str] = []`. |
| `src/scieasy/api/routes/workflows.py` | 7 endpoints (lines 1–96): create, get, update, delete, execute, pause, resume. No cancel endpoints. | **Add** 2 cancel endpoints. | **Add** after `resume_workflow()` (line 96): `@router.post("/{workflow_id}/cancel", response_model=CancelWorkflowResponse) async def cancel_workflow(workflow_id: str) -> dict[str, Any]:` — emits `CANCEL_WORKFLOW_REQUEST` to EventBus. `@router.post("/{workflow_id}/blocks/{block_id}/cancel", response_model=CancelBlockResponse) async def cancel_block(workflow_id: str, block_id: str) -> dict[str, Any]:` — emits `CANCEL_BLOCK_REQUEST` to EventBus. **Add** import: `from scieasy.api.schemas import CancelBlockRequest, CancelBlockResponse, CancelWorkflowRequest, CancelWorkflowResponse`. |

#### Documentation impact

| Document | Current state | Required changes |
|---|---|---|
| `docs/architecture/ARCHITECTURE.md` Section 5.1 (Block base class, lines 362–414) | Shows `BlockState` with 6 values (lines 367–373). Shows `_VALID_TRANSITIONS` equivalent in prose. | **Update** `BlockState` enum to show 8 values. **Add** the new state diagram. **Add** description of `CANCELLED` and `SKIPPED` semantics. |
| `docs/architecture/ARCHITECTURE.md` Section 6.1 (DAG scheduler, lines 1024–1056) | Shows synchronous for-loop scheduler. | **Rewrite** to describe event-driven scheduler. **Add** description of cancellation flow and SKIPPED propagation. **Add** the EventBus subscription matrix. |
| `docs/architecture/ARCHITECTURE.md` Section 6.3 (Pause, resume, checkpointing, lines 1105–1126) | `WorkflowCheckpoint` dataclass with 5 fields. | **Add** `skip_reasons` field. **Update** description to explain that CANCELLED and SKIPPED blocks are included in checkpoints. |
| `docs/architecture/ARCHITECTURE.md` Section 6.5 (Batch error handling, lines 1174–1192) | `BatchErrorStrategy` and `BatchResult`. | **Add** cancellation-aware batch execution description. **Add** `skipped` field to `BatchResult`. |
| `docs/architecture/ARCHITECTURE.md` Section 8.2 (REST endpoints, lines 1429–1453) | 10 endpoints listed. No cancel endpoints. | **Add** `POST /api/workflows/{id}/cancel` and `POST /api/workflows/{id}/blocks/{block_id}/cancel`. |
| `docs/architecture/ARCHITECTURE.md` Section 8.3 (WebSocket protocol, lines 1455–1480) | Only server→client messages shown. | **Add** client→server messages: `cancel_block`, `cancel_workflow`. **Add** server→client message: `cancel_propagation`. |
| `docs/architecture/ARCHITECTURE.md` Section 4.4 (Data lineage, lines 275–290) | `LineageRecord` with 9 fields. | **Add** `termination`, `partial_output_refs`, `termination_detail` fields. |
| `docs/architecture/ARCHITECTURE.md` Appendix A (Concrete example walkthrough, lines 1729–1783) | Describes only the happy-path execution flow. | **Add** a cancellation scenario variant: "What happens if the user cancels Cellpose during step 4?" showing CANCELLED → napari SKIPPED → SRS extract SKIPPED → Raman branch continues. |
| `CHANGELOG.md` | Current entries. | **Add** entry under `[Unreleased]` for ADR-018: block cancellation and event-driven runtime. |

---

## ADR-019: ProcessHandle, ProcessRegistry, and cross-platform process lifecycle

**Status**: proposed
**Date**: 2026-04-03

### Context

With all blocks executing in subprocesses (ADR-017) and user-initiated cancellation requiring reliable process termination (ADR-018), the framework needs a unified abstraction for managing OS processes across Linux, macOS, and Windows.

The original codebase had:

- `subprocess.Popen` calls in `FileExchangeBridge.launch()` (`src/scieasy/blocks/app/bridge.py:81–86`) that returned a `Popen` handle, but the caller (`AppBlock.run()` at `app_block.py:75`) discarded it. The process was fire-and-forget with no monitoring or termination capability.
- `src/scieasy/blocks/app/process_mgr.py` — a file containing only a docstring (`"""External process lifecycle management (subprocess)."""`). Completely empty.
- No process tracking anywhere in the codebase. No PID registry. No process monitoring loop. No cross-platform termination logic.

Process management is complicated by three platform-specific concerns:

1. **Termination semantics**: Linux/macOS support graceful (`SIGTERM`) then forced (`SIGKILL`) termination with process groups. Windows only has `TerminateProcess()` (always forced, no graceful equivalent) with Job Objects for tree management.
2. **Process tree management**: a block's subprocess may spawn child processes (R launching worker processes, ElMAVEN spawning helpers, multiprocessing pools). Killing only the root process leaves orphan children consuming resources.
3. **Death detection**: detecting that a subprocess has crashed, been OOM-killed, or been killed by the user via the OS task manager requires periodic polling with platform-specific APIs.

### Discussion points and resolution

| # | Topic | Options discussed | Final decision |
|---|---|---|---|
| 1 | Should we use `psutil` for cross-platform process management? | (A) Use `psutil` for all process operations. (B) Custom implementation with platform abstraction layer. (C) `psutil` as helper, custom Job Object handling on Windows. | **Decision: (C).** `psutil` provides convenient cross-platform `Process.is_running()`, `Process.children()`, `Process.kill()` etc. However, it does not manage Windows Job Objects (children spawned after `psutil.Process()` creation are not tracked). For reliable process tree management on Windows, explicit Job Object handling is needed. Use `psutil` where it helps, custom code where it doesn't. |
| 2 | Should ProcessHandle, ProcessRegistry, and ProcessMonitor be one class or separate? | (A) Single `ProcessManager` class. (B) Three separate components. | **Decision: (B).** ProcessHandle is per-process state, ProcessRegistry is global tracking, ProcessMonitor is an active polling loop. Separating them keeps each testable and replaceable independently. |
| 3 | Where should process lifecycle code live — in the block layer or engine layer? | (A) In `blocks/app/process_mgr.py` (current empty file location). (B) In `engine/runners/`. | **Decision: (B).** Process lifecycle management is an engine concern (applies to all block types via subprocess isolation), not a block-specific concern. The `blocks/app/process_mgr.py` file should be deleted. |
| 4 | Grace period on terminate: should it be configurable per block? | (A) Fixed 5-second grace period for all. (B) Configurable per block via class attribute. | **Decision: (B).** Some blocks (e.g., a database-connected block) may need more time for cleanup. Add `terminate_grace_sec: ClassVar[float] = 5.0` to `Block` base class. Note: Windows has no graceful termination, so grace period is only effective on Linux/macOS. |

### Decision

#### ProcessHandle

`ProcessHandle` is a cross-platform abstraction over an OS process providing three guarantees:

1. **Always terminable**: `terminate()` kills the process and all its children, on any platform.
2. **Always observable**: `is_alive()` and `exit_info()` report process status without blocking.
3. **Always tracked**: every `ProcessHandle` is registered in `ProcessRegistry` at creation and deregistered at cleanup.

```python
@dataclass
class ProcessExitInfo:
    """Information about how a process exited."""
    exit_code: int | None          # process exit code (None if killed by signal)
    signal_number: int | None      # signal that killed it (Linux/macOS only, None on Windows)
    was_killed_by_framework: bool   # True if terminated via ProcessHandle.terminate()/kill()
    platform_detail: str            # human-readable detail, e.g. "SIGKILL", "TerminateProcess"


class ProcessHandle:
    """Cross-platform handle for a managed subprocess.

    Created exclusively by spawn_block_process(). Never instantiated directly.
    """

    block_id: str                       # which block owns this process
    pid: int                            # OS process ID
    start_time: datetime                # when the process was launched
    resource_request: ResourceRequest   # resources this process holds
    _popen: subprocess.Popen            # underlying Popen object (private)
    _platform_ops: PlatformOps          # platform-specific operations (private)

    async def is_alive(self) -> bool:
        """Check if the process is still running. Non-blocking.

        Linux/macOS: os.kill(pid, 0) — signal 0 tests existence.
        Windows: OpenProcess() + GetExitCodeProcess() checks for STILL_ACTIVE.
        """

    async def exit_info(self) -> ProcessExitInfo | None:
        """Return exit information if process has exited, None if still running.

        Linux/macOS: os.waitpid(pid, WNOHANG) to reap zombie and get status.
            Decodes signal number from status via os.WIFSIGNALED/os.WTERMSIG.
        Windows: GetExitCodeProcess(). If != STILL_ACTIVE, process has exited.
        """

    async def terminate(self, grace_period_sec: float = 5.0) -> ProcessExitInfo:
        """Terminate the process and all its children.

        Linux/macOS:
            1. os.killpg(pgid, signal.SIGTERM) — send SIGTERM to entire process group.
            2. Wait up to grace_period_sec for process to exit gracefully.
            3. If still alive: os.killpg(pgid, signal.SIGKILL) — force kill entire group.
            4. os.waitpid() to reap.

        Windows:
            1. TerminateJobObject(job_handle, exit_code=1) — kills all processes in the Job Object.
               (No grace period — Windows TerminateProcess is always immediate.)
            2. Or if no Job Object: TerminateProcess(process_handle, 1) for root process,
               then taskkill /T /F /PID for tree cleanup.

        Returns ProcessExitInfo describing how the process was terminated.
        """

    async def kill(self) -> ProcessExitInfo:
        """Immediate forced termination. No grace period.

        Linux/macOS: os.killpg(pgid, signal.SIGKILL)
        Windows: TerminateJobObject or TerminateProcess
        """
```

#### spawn_block_process factory function

All subprocess creation in the framework goes through this single function. No code anywhere calls `subprocess.Popen` directly.

```python
def spawn_block_process(
    block_id: str,
    command: list[str],
    resource_request: ResourceRequest,
    event_bus: EventBus,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    stdin_data: bytes | None = None,
) -> ProcessHandle:
    """Launch a subprocess with platform-appropriate isolation and register it.

    Linux/macOS:
        subprocess.Popen(..., start_new_session=True)
        This calls setsid() in the child, creating a new process group.
        os.getpgid(pid) retrieves the group ID for future killpg() calls.

    Windows:
        subprocess.Popen(..., creationflags=CREATE_NEW_PROCESS_GROUP)
        CreateJobObject() + AssignProcessToJobObject(job, process_handle)
        SetInformationJobObject with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        (ensures all child processes die when the Job Object handle is closed).

    After launch:
        1. Creates ProcessHandle wrapping the Popen object.
        2. Registers handle in ProcessRegistry.
        3. Emits PROCESS_SPAWNED event on EventBus.
        4. Returns the handle.

    Parameters:
        block_id: Identifier of the block this process belongs to.
        command: Command and arguments (e.g., ["python", "-m", "scieasy.engine.runners.worker"]).
        resource_request: Resources declared by the block.
        event_bus: EventBus for emitting PROCESS_SPAWNED event.
        cwd: Working directory for the subprocess.
        env: Environment variables (merged with os.environ).
        stdin_data: Optional data to write to subprocess stdin after launch.
    """
```

#### ProcessRegistry

```python
class ProcessRegistry:
    """Singleton tracking all active block processes.

    Thread-safe. Used by ProcessMonitor for polling, by DAGScheduler for
    cancellation, and by engine shutdown for cleanup.
    """

    _handles: dict[str, ProcessHandle]   # keyed by block_id
    _lock: threading.Lock                # thread-safe access

    def register(self, handle: ProcessHandle) -> None:
        """Add a handle. Called by spawn_block_process()."""

    def deregister(self, block_id: str) -> None:
        """Remove a handle. Called when process exits (detected by ProcessMonitor)."""

    def get_handle(self, block_id: str) -> ProcessHandle | None:
        """Look up handle by block_id. Returns None if not found."""

    def active_handles(self) -> list[ProcessHandle]:
        """Return a snapshot of all currently active handles. Safe to iterate."""

    def terminate_all(self, grace_period_sec: float = 5.0) -> None:
        """Emergency shutdown: terminate every active process.
        Called during engine shutdown (SIGINT handler, server stop)."""
```

#### ProcessMonitor

```python
class ProcessMonitor:
    """Background coroutine that polls active processes for unexpected exits.

    Detects: crashes (non-zero exit), OOM kills, user killing via task manager,
    external app closing normally. Emits PROCESS_EXITED event for each detection.
    """

    registry: ProcessRegistry
    event_bus: EventBus
    poll_interval_sec: float = 1.0

    async def run(self) -> None:
        """Main polling loop. Runs until cancelled.

        Each iteration:
        1. Get snapshot of active handles from registry.
        2. For each handle, call is_alive().
        3. If not alive:
           a. Call exit_info() to get exit details.
           b. Emit PROCESS_EXITED event with block_id and exit_info.
           c. Deregister from registry.
        4. Sleep poll_interval_sec.
        """

    async def stop(self) -> None:
        """Signal the monitor to stop after the current poll cycle."""
```

**Event flow when ProcessMonitor detects unexpected process death:**

```
ProcessMonitor detects handle.is_alive() == False
    │
    ▼
emit PROCESS_EXITED(block_id="elmaven_001", exit_info={exit_code=1, signal=None, ...})
    │
    ├──→ DAGScheduler._on_process_exited():
    │       If block was PAUSED (AppBlock waiting for external app):
    │           Check exchange_dir for output files.
    │           Files present → transition to DONE (app wrote output before crashing).
    │           No files → transition to ERROR ("External process exited (code 1)
    │                                            without producing output files").
    │           Call propagate_skipped() → downstream blocks SKIPPED.
    │       If block was RUNNING:
    │           Transition to ERROR.
    │           Call propagate_skipped() → downstream blocks SKIPPED.
    │
    ├──→ ResourceManager._on_block_terminal():
    │       Release GPU/CPU/memory held by elmaven_001.
    │
    ├──→ ProcessRegistry:
    │       Deregister handle (already done by ProcessMonitor).
    │
    ├──→ LineageRecorder:
    │       Write lineage record: termination="error",
    │       termination_detail="Process exited with code 1".
    │
    └──→ CheckpointManager:
            Save checkpoint with elmaven_001 state = ERROR.
```

### Alternatives considered

- **Use `psutil` exclusively for all process management**: `psutil` provides convenient cross-platform process APIs but does not manage Windows Job Objects. Children spawned after the `psutil.Process` object is created are not automatically tracked. For reliable tree termination, explicit Job Object handling is required. `psutil` is used as a helper where appropriate (e.g., `psutil.pid_exists()` as a fast alive check), but the core lifecycle management is custom.

- **Rely on `Popen.terminate()` and `Popen.kill()`**: these methods only affect the root process, not its children. A scientific block that uses `multiprocessing.Pool` or spawns R child processes would leave orphans. Process group (`os.killpg`) and Job Object (`TerminateJobObject`) management is essential for clean termination.

- **No `ProcessMonitor` — only detect death when the scheduler checks**: the scheduler operates at block boundaries (between blocks), not continuously. If an AppBlock's external process crashes while the workflow is PAUSED, the crash goes undetected until the user interacts or the watcher times out. Continuous monitoring provides prompt detection and clean error reporting.

- **Single `ProcessManager` class combining Handle + Registry + Monitor**: conflates three distinct responsibilities with different lifecycles. ProcessHandle is created per-process and garbage-collected when the process exits. ProcessRegistry is a singleton that lives for the engine's lifetime. ProcessMonitor is a background task that runs and stops. Combining them makes testing harder (can't test registry logic without running a monitor loop) and makes the code harder to understand.

### Consequences

- Every subprocess in the framework is tracked, monitorable, and terminable from creation to cleanup. No orphan processes.
- Platform-specific code is confined to `engine/runners/platform.py`. Adding support for a new platform means implementing one `PlatformOps` subclass.
- `ProcessMonitor` adds a background polling loop at 1-second intervals. With typically <10 active processes, CPU overhead is negligible.
- `ProcessRegistry.terminate_all()` provides a clean engine shutdown path. On `SIGINT` or server stop, all block processes are terminated rather than orphaned.
- The `spawn_block_process()` factory enforces that all subprocesses are created with process group (POSIX) or Job Object (Windows) isolation. Code review can verify that no `subprocess.Popen` calls exist outside this function.
- External applications launched by AppBlock are now subject to the same lifecycle management as framework subprocesses. Killing an AppBlock kills ElMAVEN and all of ElMAVEN's child processes.
- The `ProcessHandle` abstraction is reusable if future runners (SSHRunner, SlurmRunner from ARCHITECTURE.md section 6.7) need different process management — they implement their own `ProcessHandle` subclass with appropriate remote termination logic.

### Detailed impact scope

#### New files

| File | Contents | Key classes/functions | Detailed specification |
|---|---|---|---|
| `src/scieasy/engine/runners/process_handle.py` | ProcessHandle, ProcessExitInfo, ProcessRegistry, spawn_block_process | See Decision section above | `ProcessExitInfo` dataclass: 4 fields (`exit_code: int | None`, `signal_number: int | None`, `was_killed_by_framework: bool`, `platform_detail: str`). `ProcessHandle` class: 6 attributes (`block_id: str`, `pid: int`, `start_time: datetime`, `resource_request: ResourceRequest`, `_popen: subprocess.Popen`, `_platform_ops: PlatformOps`), 4 async methods (`is_alive`, `exit_info`, `terminate`, `kill`). `ProcessRegistry` class: 2 internal attributes (`_handles: dict[str, ProcessHandle]`, `_lock: threading.Lock`), 5 methods (`register`, `deregister`, `get_handle`, `active_handles`, `terminate_all`). `spawn_block_process` function: 7 parameters, returns `ProcessHandle`. |
| `src/scieasy/engine/runners/process_monitor.py` | ProcessMonitor background coroutine | See Decision section above | `ProcessMonitor` class: 3 attributes (`registry: ProcessRegistry`, `event_bus: EventBus`, `poll_interval_sec: float = 1.0`), 1 internal attribute (`_running: bool`), 2 async methods (`run`, `stop`). |
| `src/scieasy/engine/runners/platform.py` | PlatformOps protocol, PosixOps, WindowsOps, get_platform_ops factory | See ADR-017 Decision section | `PlatformOps(Protocol)`: 5 methods (`create_process_group(popen) -> None`, `terminate_tree(pid, grace_period) -> ProcessExitInfo`, `kill_tree(pid) -> ProcessExitInfo`, `is_alive(pid) -> bool`, `get_exit_info(popen) -> ProcessExitInfo | None`). `PosixOps`: implements using `os.killpg`, `os.kill(pid, 0)`, `os.waitpid`, `signal.SIGTERM`, `signal.SIGKILL`, `os.getpgid`. `WindowsOps`: implements using `ctypes.windll.kernel32` for `CreateJobObject`, `AssignProcessToJobObject`, `TerminateJobObject`, `TerminateProcess`, `OpenProcess`, `GetExitCodeProcess`. `get_platform_ops() -> PlatformOps`: returns `WindowsOps()` if `sys.platform == "win32"`, else `PosixOps()`. |

#### Modified files

| File | Changes | Detailed field/parameter changes |
|---|---|---|
| `src/scieasy/blocks/base/block.py` | **Add** `terminate_grace_sec` class variable. | **Add** after `key_dependencies: ClassVar[list[str]] = []` (line 43): `terminate_grace_sec: ClassVar[float] = 5.0` — grace period in seconds for `ProcessHandle.terminate()`. Used by the scheduler when cancelling this block. Default 5 seconds. Linux/macOS: SIGTERM → wait this long → SIGKILL. Windows: ignored (TerminateProcess is always immediate). |
| `src/scieasy/blocks/app/process_mgr.py` | **Delete** this file. | File currently contains only `"""External process lifecycle management (subprocess)."""`. Process lifecycle is an engine-layer concern (ADR-019), not a block-layer concern. All process management is in `engine/runners/process_handle.py`, `engine/runners/process_monitor.py`, and `engine/runners/platform.py`. **Also update** `src/scieasy/blocks/app/__init__.py` if it imports from `process_mgr`. |
| `src/scieasy/engine/runners/__init__.py` | **Add** exports for new modules. | **Add** imports: `from scieasy.engine.runners.process_handle import ProcessHandle, ProcessExitInfo, ProcessRegistry, spawn_block_process`, `from scieasy.engine.runners.process_monitor import ProcessMonitor`, `from scieasy.engine.runners.platform import PlatformOps, get_platform_ops`. |

#### Documentation impact

| Document | Current state | Required changes |
|---|---|---|
| `docs/architecture/ARCHITECTURE.md` Section 6.4 (Resource management, lines 1127–1171) | Describes `ResourceManager` with `acquire()` / `release()`. No mention of automatic release on process death. | **Add** description of EventBus-triggered automatic resource release. Reference ProcessMonitor detection of process death. |
| `docs/architecture/ARCHITECTURE.md` Section 11 (Technology stack, lines 1690–1708) | "Process management: subprocess + watchdog" (line 1700). | **Update** to: "Process lifecycle: ProcessHandle + ProcessRegistry + ProcessMonitor. Cross-platform: POSIX signals + process groups (Linux/macOS), Job Objects + TerminateProcess (Windows). Optional: psutil for convenience methods." |
| `docs/architecture/ARCHITECTURE.md` Appendix B (Glossary, lines 1786–1803) | 12 glossary terms. No process management terms. | **Add** glossary entries: `ProcessHandle` — "Cross-platform abstraction over an OS process, providing terminate/monitor/query capabilities. Every subprocess in the framework is wrapped in a ProcessHandle." `ProcessRegistry` — "Singleton tracking all active block subprocesses. Enables cancellation, monitoring, and clean shutdown." `ProcessMonitor` — "Background coroutine that polls active processes for unexpected exits (crash, OOM, user kill via task manager)." |
| `docs/architecture/ARCHITECTURE.md` new subsection after Section 6.4 | Does not exist. | **Add** new Section 6.5: "Process lifecycle management" describing ProcessHandle, ProcessRegistry, ProcessMonitor, platform abstraction, and the spawn_block_process factory. |
| `CHANGELOG.md` | Current entries. | **Add** entry under `[Unreleased]` for ADR-019. |

---

## ADR-020: Collection-based data transport — eliminate engine-level batch iteration

**Status**: proposed
**Date**: 2026-04-03

### Context

The original architecture defined three batch execution modes at the engine level: `PARALLEL` (all items through one block concurrently, then the next block), `SERIAL` (each item through the full downstream pipeline before the next), and `ADAPTIVE` (engine decides based on downstream blocks). These modes were declared per-block via `batch_mode` and executed by a dedicated `BatchExecutor` component.

This design created cascading architectural problems that were discovered during the cancellation and process lifecycle design (ADR-017, ADR-018, ADR-019):

1. **ProcessRegistry key collision**: in parallel mode, the same `block_id` spawns multiple concurrent subprocesses, but `ProcessRegistry` uses `block_id` as a unique key — only one handle per block can be stored, making parallel subprocess tracking impossible.

2. **Parallel→serial→parallel pipeline problem**: when a parallel block (Cellpose) feeds into a serial block (napari review), the current block-level scheduler forces ALL items to complete the parallel block before ANY item enters the serial block. For 50 images with Cellpose taking 5 minutes each, the user waits ~4 hours before they can review the first result — even though img1's result was ready in 5 minutes. Solving this requires item-level pipelining with buffering between blocks, fundamentally changing the scheduler from block-level to item-level granularity.

3. **External software integration failure**: AppBlock's serial batch mode opens one instance of the external application per item (100 ElMAVEN windows for 100 mzXML files). Users expect to open ONE ElMAVEN window and load all 100 files. The `batch_mode` abstraction cannot express "pass the entire collection to a single invocation."

4. **Complexity cost**: `BatchExecutor` required parallel/serial/adaptive dispatch strategies, `BatchErrorStrategy` (STOP/SKIP/RETRY/PAUSE), `BatchResult` tracking (succeeded/failed/skipped per item), and interaction with `ResourceManager` for per-item resource allocation. This complexity propagated into the scheduler, checkpoint system, lineage records (`batch_info`), cancellation logic (cancel one item vs. entire batch), and frontend display (per-item progress).

The root cause of all four problems is the same: **the engine is trying to manage item-level iteration that it does not have domain knowledge to perform correctly.** The engine does not know whether Cellpose should process images independently (per-item), whether ElMAVEN should receive all files at once (collection), or whether napari should present images one by one (serial per-item). Only the block author knows the correct batch semantics for their tool.

### Discussion points and resolution

| # | Topic | Options discussed | Final decision |
|---|---|---|---|
| 1 | Should Collection be a 7th base data type alongside Array, Series, etc.? | (A) Yes, add Collection to the type hierarchy. (B) No, Collection is a transport wrapper — its type identity is determined by its contents. | **Decision: (B).** Collection is not a data type — it is a packaging mechanism at the port/block boundary. A `Collection[Image]` is typed as `Image` for port matching purposes. This keeps the 6 base types stable and avoids polluting the type system. |
| 2 | Should the engine ever iterate over items? | (A) Engine iterates by default, blocks can opt out with `batch_handling=COLLECTION`. (B) Engine never iterates — all data flows as Collections, blocks handle iteration internally. | **Decision: (B).** Complete elimination of engine-level iteration. The engine only passes Collections between blocks. This is the maximally simple model for the engine and gives blocks full control. |
| 3 | Does this increase block author burden? | (A) Yes, unacceptably — block authors must write iteration loops. (B) Manageable — the Block base class provides `pack()`, `unpack()`, `map_items()`, `parallel_map()` utilities, and a `PerItemProcessBlock` convenience base class can be offered. | **Decision: (B).** The Block base class provides utilities that make simple per-item blocks as easy to write as before. The `map_items()` one-liner covers 80% of cases. Advanced blocks (ElMAVEN, napari) benefit from full control. |
| 4 | How should CodeBlock handle Collections? | (A) Pass Collections directly to user scripts (breaking change — scripts must understand Collection). (B) CodeBlock auto-unpacks before calling user code, auto-repacks after. | **Decision: (B).** CodeBlock transparently unwraps: length=1 → single native object (numpy/pandas/etc.), length>1 → list of native objects. User scripts never see a Collection object. This preserves the "zero framework knowledge" promise for script authors. |
| 5 | What happens to partial results when a block is cancelled? | (A) Engine guarantees partial result preservation. (B) All results lost on cancel — block can optionally save partial results to storage. | **Decision: (B).** Cancellation kills the subprocess, losing in-memory state. This is the same behaviour as stopping a Jupyter notebook cell. Blocks that need partial result preservation can write to storage incrementally — this is a block-level concern, not an engine concern. |
| 6 | How should Port type checking work with Collections? | Port declares `accepted_types=[Image]`. A `Collection[Image]` flows through. Is this compatible? | **Decision: Yes, transparently.** The port system checks the Collection's `item_type` against `accepted_types`, not the Collection wrapper itself. `Collection[Image]` matches `accepted_types=[Image]`. From the port system's perspective, Collection is invisible. |

### Decision

#### Core model change

**All data flowing between blocks is wrapped in a `Collection`.** The engine never unpacks, iterates, or inspects the contents of a Collection. It treats every Collection as an opaque unit: one Collection in, one Collection out, one subprocess, one ProcessHandle.

```
BEFORE (engine-driven iteration):
    IOBlock outputs [img1, img2, ..., img100]
        → engine unpacks into 100 items
        → BatchExecutor calls Cellpose.run(img1), run(img2), ..., run(img100)
        → engine collects 100 results
    [mask1, mask2, ..., mask100]

AFTER (Collection-based transport):
    IOBlock outputs Collection[Image](100 items)   ← one DataObject-like wrapper
        → engine passes it as-is to one run() call
        → Cellpose.run(inputs={"images": Collection[Image]})   ← called once
        → returns Collection[Image](100 masks)   ← one wrapper
```

A single item is simply `Collection` with `length=1`. There is no special case — the engine always deals with Collections.

#### Collection specification

```python
class Collection:
    """Homogeneous ordered collection of DataObjects.

    NOT a DataObject subclass — it is a transport wrapper, not a data type.
    Its type identity for port matching is determined by item_type.

    Invariants:
        - All items must be instances of the same base DataObject subclass.
        - item_type is set at construction and cannot change.
        - length=0 is valid (empty collection).
    """

    items: list[DataObject]
    item_type: type                    # e.g. Image, DataFrame

    def __init__(self, items: list[DataObject], item_type: type | None = None):
        if items and item_type is None:
            item_type = type(items[0])
        if items:
            for i, item in enumerate(items):
                if not isinstance(item, item_type):
                    raise TypeError(
                        f"Collection requires homogeneous types: item[{i}] is "
                        f"{type(item).__name__}, expected {item_type.__name__}")
        self.items = items
        self.item_type = item_type or DataObject

    def __getitem__(self, index): ...
    def __iter__(self): ...
    def __len__(self): return len(self.items)

    @property
    def length(self) -> int: return len(self.items)

    def storage_refs(self) -> list[StorageReference]:
        """Return StorageReference for each item (for cross-process serialisation)."""
        return [item.storage_ref for item in self.items]
```

#### Port system adaptation

Port type checking becomes Collection-transparent:

```python
def port_accepts_type(port: Port, data_type: type) -> bool:
    # If data_type is Collection, check item_type against accepted_types
    if data_type is Collection:
        return True  # Collection itself is always structurally valid;
                     # item_type is checked at runtime via constraint or connection validation

def validate_connection(source_port: OutputPort, target_port: InputPort) -> tuple[bool, str]:
    # Check that source's item_type (inside Collection) matches target's accepted_types
    # Since ALL data is Collection, this means:
    #   source produces Collection[X] → check X against target.accepted_types
    # Port.accepted_types still declares the ITEM type, not Collection
```

Block authors declare ports exactly as before:

```python
input_ports = [InputPort(name="images", accepted_types=[Image])]
```

This port accepts `Collection[Image]` of any length. The port system extracts `item_type=Image` from the Collection and checks it against `accepted_types=[Image]`.

#### Block base class utilities

```python
class Block(ABC):

    @abstractmethod
    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        ...

    # --- Pack / unpack ---

    @staticmethod
    def pack(items: list[DataObject], item_type: type | None = None) -> Collection:
        """Pack a list of DataObjects into a Collection."""
        return Collection(items, item_type=item_type)

    @staticmethod
    def unpack(collection: Collection) -> list[DataObject]:
        """Unpack a Collection into a list of individual DataObjects."""
        return list(collection.items)

    @staticmethod
    def unpack_single(collection: Collection) -> DataObject:
        """Unpack a length-1 Collection into a single DataObject.
        Raises ValueError if length != 1."""
        if len(collection) != 1:
            raise ValueError(f"Expected single-item Collection, got length {len(collection)}")
        return collection.items[0]

    # --- Iteration helpers (execute inside the block's subprocess) ---

    @staticmethod
    def map_items(func: Callable[[DataObject], DataObject],
                  collection: Collection) -> Collection:
        """Apply func to each item sequentially. Returns new Collection."""
        results = [func(item) for item in collection]
        return Collection(results)

    @staticmethod
    def parallel_map(func: Callable[[DataObject], DataObject],
                     collection: Collection,
                     max_workers: int = 4) -> Collection:
        """Apply func to each item using a process pool. Returns new Collection."""
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(func, collection.items))
        return Collection(results)
```

#### CodeBlock auto-unpack/repack

CodeBlock inserts a transparent conversion layer so user scripts never see Collection objects:

```python
class CodeBlock(Block):
    def run(self, inputs: dict[str, Collection], config: BlockConfig) -> dict[str, Collection]:
        # Auto-unpack: Collection → native object(s) for user scripts
        user_inputs = {}
        for name, coll in inputs.items():
            if len(coll) == 1:
                user_inputs[name] = coll[0].to_memory()        # single native object
            else:
                user_inputs[name] = [item.to_memory() for item in coll]  # list

        # Execute user script (user sees numpy arrays, pandas DataFrames, etc.)
        result = runner.execute(script, user_inputs, config)

        # Auto-repack: native object(s) → Collection
        outputs = {}
        for name, value in result.items():
            if isinstance(value, list):
                outputs[name] = self.pack([wrap_as_dataobject(v) for v in value])
            else:
                outputs[name] = self.pack([wrap_as_dataobject(value)])
        return outputs
```

User scripts remain unchanged:

```python
# length=1: user receives a numpy array
smoothed = savgol_filter(input_0, 11, 3)
output_0 = smoothed

# length=100: user receives a list of numpy arrays
output_0 = [savgol_filter(s, 11, 3) for s in input_0]
```

#### What is removed

| Component | File | Status |
|---|---|---|
| `BatchMode` enum (PARALLEL, SERIAL, ADAPTIVE) | `blocks/base/state.py` | **Deleted** |
| `BatchErrorStrategy` enum (STOP, SKIP, RETRY, PAUSE) | `blocks/base/state.py` | **Deleted** |
| `BatchResult` dataclass | `blocks/base/result.py` | **Deleted** |
| `Block.batch_mode` class variable | `blocks/base/block.py` | **Deleted** |
| `Block.on_batch_error` class variable | `blocks/base/block.py` | **Deleted** |
| `BatchExecutor` class | `engine/batch.py` | **Entire file deleted** |
| `NodeDef.batch_mode` field | `workflow/definition.py` | **Deleted** |
| `LineageRecord.batch_info` field | `core/lineage/record.py` | **Deleted** |
| `batch_info TEXT` column | `core/lineage/store.py` | **Deleted from schema** |
| ADR-010 (Batch execution mode per block) | `docs/adr/ADR.md` | **Superseded by ADR-020** |

### Alternatives considered

- **Keep engine-level iteration with a `BatchHandling` flag (PER_ITEM vs COLLECTION)**: adds a new enum and branching logic in the scheduler ("if COLLECTION, pass whole; if PER_ITEM, iterate"). This halves the complexity compared to the original three-mode system but still leaves the engine responsible for iteration semantics. The Collection-only model eliminates this branching entirely.

- **Add a buffer mechanism between blocks for parallel→serial transitions**: solves the pipeline problem but adds a new runtime component (buffer), flush-condition configuration, and type-system complexity (buffer wraps items). The Collection model eliminates the need for inter-block buffering because there are no mode transitions — every block receives and returns one Collection.

- **Keep `BatchExecutor` but fix ProcessRegistry to support one-to-many**: addresses the ProcessRegistry collision but not the ElMAVEN problem, not the pipeline problem, and not the complexity cost. A targeted fix for a systemic issue.

### Consequences

- **Engine simplification**: `BatchExecutor` is deleted. `DAGScheduler` becomes a pure block-level orchestrator with no item-level logic. ~200 lines of batch code removed (BatchExecutor, BatchMode, BatchErrorStrategy, BatchResult, batch-related scheduler logic).
- **Block author control**: block authors have full control over how they process collections — parallel, serial, whole-collection, or any custom strategy. This matches reality: Cellpose has built-in GPU batching, ElMAVEN loads multiple files natively, napari supports multi-image sessions.
- **ProcessRegistry stays simple**: always 1 block = 1 subprocess = 1 ProcessHandle. No one-to-many mapping needed.
- **Cancellation stays simple**: cancel block = kill one subprocess = done. No per-item cancel tracking, no partial batch results, no multi-process termination coordination.
- **CodeBlock transparency**: user scripts are unaffected. The auto-unpack/repack layer in CodeBlock ensures that scripts written for the old model continue to work — a single-item Collection is unwrapped to a single native object, identical to what the script received before.
- **ADR-010 superseded**: the per-block `batch_mode` declaration is replaced by block-internal iteration logic. Blocks that previously declared `batch_mode=PARALLEL` now use `self.parallel_map()`. Blocks that declared `batch_mode=SERIAL` now use a simple for-loop. Blocks that declared `batch_mode=ADAPTIVE` no longer need the engine's look-ahead — they choose their own strategy.
- **Tradeoff — partial results**: the engine no longer guarantees per-item error isolation or partial result preservation. A subprocess crash loses all items. This is acceptable because: (1) it matches user expectations (like Jupyter cell interruption), (2) blocks can implement incremental saving if needed, (3) the complexity cost of per-item tracking far exceeds its benefit for the target use case.
- **New Collection type**: `Collection` is a new construct at the transport layer. It must be supported in cross-process serialisation (subprocess worker), checkpoint serialisation, and lineage recording. Since Collection holds `StorageReference` pointers (not data), serialisation overhead is minimal.

### Detailed impact scope

#### New files

| File | Contents |
|---|---|
| `src/scieasy/core/types/collection.py` | `Collection` class with homogeneity enforcement, `__getitem__`, `__iter__`, `__len__`, `storage_refs()`. |
| `tests/core/test_collection.py` | Tests: construction, homogeneity enforcement (reject mixed types), length-0 edge case, pack/unpack round-trip, storage_refs extraction. |

#### Deleted files

| File | Reason |
|---|---|
| `src/scieasy/engine/batch.py` | `BatchExecutor` is entirely eliminated. All batch logic moves to Block internals. |

#### Modified files — Layer 1 (Data Foundation)

| File | Changes |
|---|---|
| `core/lineage/record.py` | **Delete** `batch_info: dict[str, Any] \| None = field(default=None)` (line 35). |
| `core/lineage/store.py` | **Delete** `batch_info TEXT` from `_CREATE_TABLE` SQL (line 24). **Remove** `batch_info` from `write()` INSERT statement (line 67–81) and values tuple. **Remove** `batch_info` parsing from `_row_to_record()` (line 99). **Remove** `batch_info` from all SELECT column lists in `query()` (line 111) and `ancestors()` (line 141). **Update** row index offsets in `_row_to_record()` after column removal. |
| `core/types/__init__.py` | **Add** re-export: `from scieasy.core.types.collection import Collection`. |

#### Modified files — Layer 2 (Block System)

| File | Changes |
|---|---|
| `blocks/base/state.py` | **Delete** `BatchMode` enum (lines 27–33, 3 values). **Delete** `BatchErrorStrategy` enum (lines 43–49, 4 values). File retains: `BlockState`, `ExecutionMode`, `InputDelivery`. |
| `blocks/base/block.py` | **Delete** import of `BatchErrorStrategy, BatchMode` from line 10. **Delete** `batch_mode: ClassVar[BatchMode] = BatchMode.PARALLEL` (line 40). **Delete** `on_batch_error: ClassVar[BatchErrorStrategy] = BatchErrorStrategy.SKIP` (line 41). **Change** `run()` signature (line 111) from `dict[str, Any] -> dict[str, Any]` to `dict[str, Collection] -> dict[str, Collection]`. **Add** import `from scieasy.core.types.collection import Collection`. **Add** 6 utility methods: `pack()`, `unpack()`, `unpack_single()`, `map_items()`, `parallel_map()`, `get_single_or_list()` (for CodeBlock). |
| `blocks/base/result.py` | **Delete** `BatchResult` dataclass (lines 18–24). Retain `BlockResult`. |
| `blocks/base/__init__.py` | **Remove** imports/exports: `BatchErrorStrategy`, `BatchMode`, `BatchResult` (lines 16, 18–19, 26–28). **Add** import/export: `Collection`. |
| `blocks/base/ports.py` | **Update** `port_accepts_type()` (line 36): if incoming type is `Collection`, extract `item_type` and check that against `accepted_types`. **Update** `port_accepts_signature()` (line 48): handle `Collection` signature by delegating to item signature. **Update** `validate_connection()` (line 80): when source produces `Collection[X]`, check `X` against target's `accepted_types`. |
| `blocks/io/io_block.py` | **Update** `run()` return: wrap result in `Collection`. `direction="input"`: single file → `self.pack([result])`, directory → `self.pack(results)`. `direction="output"`: `self.unpack()` or `self.unpack_single()` before writing. |
| `blocks/process/process_block.py` | **Update** `run()` signature to `dict[str, Collection] -> dict[str, Collection]`. |
| `blocks/process/builtins/merge.py` | **Update** to unpack input Collections, perform Arrow concat, pack result. |
| `blocks/process/builtins/split.py` | **Update** to unpack input Collection, split, pack into two output Collections. |
| `blocks/code/code_block.py` | **Add** auto-unpack layer before user script execution: Collection len=1 → single native object, len>1 → list. **Add** auto-repack layer after: single value → `pack([wrap(value)])`, list → `pack([wrap(v) for v in value])`. **Update** `_prepare_inputs()` to first extract from Collection, then apply `InputDelivery` mode. |
| `blocks/app/app_block.py` | **Update** `run()` to receive `Collection`. Block decides internally whether to unpack (napari) or pass whole collection to bridge (ElMAVEN). |
| `blocks/ai/ai_block.py` | **Update** `run()` signature to `dict[str, Collection]`. |
| `blocks/subworkflow/subworkflow_block.py` | **Update** `run()` and `_sequential_execute()` to pass Collections through child workflow. |

#### Modified files — Layer 3 (Execution Engine)

| File | Changes |
|---|---|
| `engine/batch.py` | **Deleted** (see above). |
| `engine/__init__.py` | **Update** docstring: remove "batch executor" (line 1). |
| `engine/scheduler.py` | **Remove** any `BatchExecutor` usage or batch_mode branching. Scheduler calls `runner.run()` once per block, passing Collection inputs. |
| `engine/events.py` | **Remove** any batch-related event types if present. |
| `engine/checkpoint.py` | **Remove** any batch-related fields from `WorkflowCheckpoint` if present. |

#### Modified files — Layer 4 (Workflow Definition)

| File | Changes |
|---|---|
| `workflow/definition.py` | **Delete** `batch_mode: str \| None = None` from `NodeDef` (line 21). |

#### Modified files — Tests

| File | Changes |
|---|---|
| `tests/blocks/test_code_block.py` | **Add** tests for Collection auto-unpack/repack: single item, multiple items, list output. |
| `tests/blocks/test_io_block.py` | **Update** assertions to expect Collection-wrapped outputs. |
| `tests/blocks/test_app_block.py` | **Update** to pass Collection inputs, verify Collection outputs. |
| `tests/blocks/test_process_block.py` | **Update** to use pack/unpack in test assertions. |
| `tests/blocks/test_ports.py` | **Add** tests for Collection-transparent type checking: `Collection[Image]` matches port `accepted_types=[Image]`. |
| `tests/blocks/test_subworkflow.py` | **Update** to pass/expect Collections. |

#### Modified files — Documentation

| File | Changes |
|---|---|
| `docs/architecture/ARCHITECTURE.md` | Section 3 (layer overview): remove "batch executor" from Layer 3 description. Section 4.4 (lineage): remove `batch_info` field. Section 5.1 (Block base): remove `BatchMode`, `batch_mode`, add Collection and utility methods. Section 6.2 (Batch execution): **rewrite entirely** — describe Collection model, block-internal iteration, pack/unpack utilities. Section 6.6 (Batch error handling): **rewrite or delete** — no engine-level batch error strategy. Section 10.1 (Workflow YAML): remove `batch_mode` and `batch: true` from all node examples. Appendix A (example): update execution description. Appendix B (glossary): add `Collection` definition. |
| `docs/architecture/PROJECT_TREE.md` | Remove `engine/batch.py` entry. Update `blocks/base/state.py` annotation (remove BatchMode). Update `blocks/base/result.py` annotation (remove BatchResult). Update `blocks/base/block.py` annotation (remove batch_mode, add Collection utilities). Add `core/types/collection.py` entry. Update engine file count (11→10). Update total file count. |
| `docs/adr/ADR.md` | **Change** ADR-010 status from `accepted` to `superseded by ADR-020`. |
| `docs/roadmap/ROADMAP_v0.1.md` | Remove `BatchExecutor`, `BatchMode`, `BatchErrorStrategy` checklist items. Update Phase 5 description. |
| `docs/testing/phase-5-ai-tests.md` | Remove `tests/engine/test_batch.py` section. Replace with Collection transport tests. |
| `docs/testing/phase-5-human-tests.md` | Remove Test 9 (Batch Execution). Remove checklist items 12–14. Replace with Collection-based test scenarios. |
| `CHANGELOG.md` | Add ADR-020 entry under `[Unreleased]`. |

---

## ADR-021: MergeCollection and Collection operation blocks

**Status**: proposed
**Date**: 2026-04-03

### Context

With the Collection-based data transport model (ADR-020), users sometimes need to combine multiple Collections into one before passing them to a block. For example, two batches of LC-MS data processed through different pipelines must be merged into a single Collection for ElMAVEN to open in one session.

### Decision

Provide a set of built-in Collection operation blocks as framework infrastructure. These blocks operate purely at the Collection level — they do not inspect or transform the contained DataObjects.

| Block | Purpose | Input ports | Output ports |
|---|---|---|---|
| `MergeCollection` | Concatenate 2 same-typed Collections into 1 | `a: [DataObject]`, `b: [DataObject]` | `merged: [DataObject]` |
| `SplitCollection` | Split a Collection by index or condition | `data: [DataObject]` + config (split point / predicate) | `left: [DataObject]`, `right: [DataObject]` |
| `FilterCollection` | Keep items matching a metadata predicate | `data: [DataObject]` + config (predicate) | `filtered: [DataObject]` |
| `SliceCollection` | Extract a contiguous sub-range `[start:end]` | `data: [DataObject]` + config (start, end) | `sliced: [DataObject]` |

These blocks preserve the static port contract — no dynamic ports. Users who need to merge 3+ Collections chain two `MergeCollection` blocks.

### Alternatives considered

- **Dynamic input ports on downstream blocks**: breaks the static port contract principle, requires frontend support for runtime port addition, and forces every block that might receive multiple collections to implement merge logic. Rejected.

### Consequences

- Collection operations are composable utility blocks, not special engine features.
- Users who need multi-source data merge add a `MergeCollection` node to the canvas — one extra node, zero framework complexity.
- Future Collection operations (sort, deduplicate, sample) can be added as new blocks without engine changes.
