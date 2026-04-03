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

**Status**: accepted  
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
