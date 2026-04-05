# SciEasy — Project Tree

> Maps 1:1 to the Architecture Document (ARCHITECTURE.md).
> Each file is annotated with its responsibility.

> **Note:** This tree shows the **target architecture**. Sections marked *"planned"* contain files that do not yet exist in the repository.

```
scieasy/                               # ← repo root
│
├── pyproject.toml                      # Package metadata, dependencies, entry_points
├── README.md
├── ARCHITECTURE.md
├── LICENSE
├── Makefile                            # dev shortcuts: make test, make lint, make serve
│
│
│ ══════════════════════════════════════════════════════════════════
│  PYTHON BACKEND  (src layout — `pip install -e .` installs scieasy)
│ ══════════════════════════════════════════════════════════════════
│
├── src/
│   └── scieasy/
│       ├── __init__.py                 # Package root, version string
│       │
│       │
│       │ ── Layer 1: Data Foundation ─────────────────────────────
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   │
│       │   ├── types/                  # DataObject type hierarchy
│       │   │   ├── __init__.py         # Re-exports all base types
│       │   │   ├── base.py             # DataObject ABC, TypeSignature, metadata
│       │   │   ├── array.py            # Array (wraps ndarray-like, Zarr-backed)
│       │   │   ├── series.py           # Series (1D indexed data)
│       │   │   ├── dataframe.py        # DataFrame (columnar tabular data)
│       │   │   ├── text.py             # Text (plain text, markdown, JSON)
│       │   │   ├── artifact.py         # Artifact (opaque files: PDF, binary, etc.)
│       │   │   ├── composite.py        # CompositeData (named heterogeneous slots)
│       │   │   ├── collection.py       # Collection: homogeneous ordered transport wrapper
│       │   │   │                       #   for DataObjects between blocks (ADR-020).
│       │   │   │                       #   NOT a DataObject subclass — type identity from contents.
│       │   │   └── registry.py         # TypeRegistry: discovers types from
│       │   │                           #   Tier 1: {project}/types/ + ~/.scieasy/types/
│       │   │                           #   Tier 2: scieasy.types entry_points
│       │   │                           #   Resolves inheritance for port matching
│       │   │
│       │   ├── storage/                # Storage backends (per-type persistence)
│       │   │   ├── __init__.py
│       │   │   ├── base.py             # StorageBackend protocol (read/write/slice/iter_chunks)
│       │   │   ├── zarr_backend.py     # Zarr store for Array types (chunked, lazy)
│       │   │   ├── arrow_backend.py    # Apache Arrow / Parquet for DataFrame types
│       │   │   ├── filesystem.py       # Plain filesystem for Text, Artifact
│       │   │   ├── composite_store.py  # Directory-of-slots storage for CompositeData
│       │   │   └── ref.py              # StorageReference: pointer to a stored object
│       │   │
│       │   ├── proxy.py                # ViewProxy: lazy-loading accessor (slice, iter_chunks,
│       │   │                           #   to_memory, shape). Injected into block.run() inputs.
│       │   │
│       │   └── lineage/                # Provenance tracking
│       │       ├── __init__.py
│       │       ├── record.py           # LineageRecord dataclass (hashes, config, environment,
│       │       │                       #   termination status, partial_output_refs; ADR-018)
│       │       ├── environment.py      # EnvironmentSnapshot: python version, key_packages, freeze
│       │       ├── store.py            # LineageStore: SQLite read/write for lineage records
│       │       └── graph.py            # Provenance graph queries (ancestors, diff, audit)
│       │
│       │
│       │ ── Layer 2: Block System ────────────────────────────────
│       │
│       ├── blocks/
│       │   ├── __init__.py
│       │   │
│       │   ├── base/                   # Block ABC and core machinery
│       │   │   ├── __init__.py
│       │   │   ├── block.py            # Block ABC: validate(), run(), postprocess()
│       │   │   │                       #   Fields: name, version, input_ports, output_ports,
│       │   │   │                       #   execution_mode, resource_request,
│       │   │   │                       #   terminate_grace_sec (ADR-019). run() always
│       │   │   │                       #   executes in subprocess, not engine process (ADR-017).
│       │   │   │                       #   Utilities: pack(), unpack(), map_items(),
│       │   │   │                       #   parallel_map() for Collection handling (ADR-020).
│       │   │   │                       #   process_item() convenience method + _auto_flush()
│       │   │   │                       #   for memory-safe per-item processing (ADR-020 Addendum 5).
│       │   │   ├── ports.py            # Port, InputPort, OutputPort
│       │   │   │                       #   Type matching + optional constraint function
│       │   │   ├── config.py           # BlockConfig: validated param container (Pydantic)
│       │   │   ├── state.py            # BlockState enum (8 states incl. CANCELLED, SKIPPED;
│       │   │   │                       #   ADR-018), ExecutionMode, InputDelivery enums
│       │   │   │                       #   BatchMode/BatchErrorStrategy removed (ADR-020)
│       │   │   └── result.py           # BlockResult (BatchResult removed per ADR-020)
│       │   │
│       │   ├── io/                     # IOBlock — data ingress / egress
│       │   │   ├── __init__.py
│       │   │   ├── io_block.py         # IOBlock: direction="input"|"output", format dispatch
│       │   │   │                       #   Lazy Collection construction: creates StorageReference
│       │   │   │                       #   per file, no eager data read (ADR-020 Addendum 2)
│       │   │   ├── adapters/           # Pluggable format adapters
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base.py         # FormatAdapter protocol (read → DataObject, write → file)
│       │   │   │   │                   #   + create_reference(path) for lazy loading (ADR-020 Addendum 2)
│       │   │   │   ├── csv_adapter.py
│       │   │   │   ├── tiff_adapter.py
│       │   │   │   ├── zarr_adapter.py
│       │   │   │   ├── parquet_adapter.py
│       │   │   │   ├── mzxml_adapter.py
│       │   │   │   ├── h5ad_adapter.py     # AnnData .h5ad ↔ CompositeData
│       │   │   │   ├── fcs_adapter.py      # Flow cytometry .fcs
│       │   │   │   └── generic_adapter.py  # Fallback: binary → Artifact
│       │   │   └── adapter_registry.py # Maps file extensions → adapter classes
│       │   │
│       │   ├── process/                # ProcessBlock — data transformation
│       │   │   ├── __init__.py
│       │   │   ├── process_block.py    # ProcessBlock base (algorithm, params)
│       │   │   │                       #   Default run() iterates via process_item() + auto-flush
│       │   │   │                       #   (ADR-020 Addendum 5 Tier 1)
│       │   │   ├── builtins/           # Built-in process blocks shipped with framework
│       │   │   │   ├── __init__.py
│       │   │   │   ├── merge.py        # Merge / join / concatenate multi-input
│       │   │   │   ├── split.py        # Filter / subset / train-test split
│       │   │   │   ├── transform.py    # Generic column/array transforms
│       │   │   │   └── register.py     # Image registration (cross-modal alignment)
│       │   │   └── contrib/            # Community-contributed process blocks (examples)
│       │   │       ├── __init__.py
│       │   │       ├── cellpose_segment.py
│       │   │       ├── baseline_correction.py
│       │   │       └── spectral_pca.py
│       │   │
│       │   ├── code/                   # CodeBlock — user-provided scripts
│       │   │   ├── __init__.py
│       │   │   ├── code_block.py       # CodeBlock: inline mode + script mode
│       │   │   │                       #   Dispatches to CodeRunner by language
│       │   │   │                       #   Auto-unpack: Collection → native objects / LazyList
│       │   │   │                       #   Auto-repack: native objects → Collection (ADR-020 Addendum 4)
│       │   │   ├── lazy_list.py        # LazyList: looks like list, loads items on demand from
│       │   │   │                       #   Collection via ViewProxy. Memory-safe iteration for
│       │   │   │                       #   user scripts (ADR-020 Addendum 4)
│       │   │   ├── runners/            # Language-specific execution environments
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base.py         # CodeRunner protocol (execute_inline, execute_script)
│       │   │   │   ├── python_runner.py    # Python: subprocess worker calls exec()/importlib (ADR-017)
│       │   │   │   ├── r_runner.py         # R: subprocess calling Rscript (ADR-017, no rpy2)
│       │   │   │   └── julia_runner.py     # Julia: subprocess calling julia (ADR-017, no juliacall)
│       │   │   ├── runner_registry.py  # Maps language string → runner class
│       │   │   └── introspect.py       # Script introspection: parse run() signature,
│       │   │                           #   extract configure() schema, auto-gen ports
│       │   │
│       │   ├── app/                    # AppBlock — external GUI software bridge
│       │   │   ├── __init__.py
│       │   │   ├── app_block.py        # AppBlock: launch → pause → watch → resume
│       │   │   ├── bridge.py           # ExternalAppBridge protocol (serialise, launch, watch)
│       │   │   │                       #   prepare() iterates Collection, writes files one at a
│       │   │   │                       #   time for memory safety (ADR-020 Addendum 5)
│       │   │   └── watcher.py          # File watcher (polling) for output detection
│       │   │                           #   + process death detection via ProcessHandle (ADR-019)
│       │   │
│       │   ├── ai/                     # AIBlock — LLM-driven processing
│       │   │   ├── __init__.py
│       │   │   ├── ai_block.py         # AIBlock: prompt template + model dispatch
│       │   │   ├── providers.py        # LLM provider abstraction (Anthropic, OpenAI, local)
│       │   │   └── parsers.py          # Structured output parsing (JSON → DataObject)
│       │   │
│       │   ├── subworkflow/            # SubWorkflowBlock — workflow-as-block
│       │   │   ├── __init__.py
│       │   │   └── subworkflow_block.py  # SubWorkflowBlock: load child workflow,
│       │   │                             #   inject inputs, run child DAG, extract outputs
│       │   │
│       │   └── registry.py             # BlockRegistry: discovers blocks from
│       │                               #   Tier 1: {project}/blocks/ + ~/.scieasy/blocks/
│       │                               #   Tier 2: scieasy.blocks entry_points
│       │                               #   Maintains palette metadata (name, icon, category,
│       │                               #   port schemas, config JSON Schema)
│       │
│       │
│       │ ── Layer 3: Execution Engine ────────────────────────────
│       │
│       ├── engine/
│       │   ├── __init__.py
│       │   │
│       │   ├── dag.py                  # DAG construction from workflow definition
│       │   │                           #   (topological sort, dependency resolution)
│       │   │
│       │   ├── scheduler.py            # DAGScheduler: event-driven DAG execution (ADR-018)
│       │   │                           #   Subscribes to EventBus for cancel/error/done events.
│       │   │                           #   Propagates SKIPPED to unreachable downstream blocks.
│       │   │
│       │   ├── resources.py            # ResourceManager: GPU slots, CPU workers, OS memory
│       │   │                           #   monitoring via psutil (ADR-022). ResourceRequest
│       │   │                           #   dataclass (no estimated_memory_gb). can_dispatch()/
│       │   │                           #   release(). Auto-release via EventBus (ADR-018).
│       │   │
│       │   ├── runners/                # BlockRunner protocol + implementations
│       │   │   ├── __init__.py
│       │   │   ├── base.py             # BlockRunner protocol (run→RunHandle, check_status, cancel)
│       │   │   ├── local.py            # LocalRunner: isolated subprocess execution (ADR-017)
│       │   │   ├── worker.py           # Subprocess entry point: receives payload via stdin,
│       │   │   │                       #   imports block, reconstructs ViewProxy from StorageRef,
│       │   │   │                       #   calls block.run(), writes outputs, returns refs (ADR-017)
│       │   │   ├── process_handle.py   # ProcessHandle, ProcessExitInfo, ProcessRegistry,
│       │   │   │                       #   spawn_block_process() factory (ADR-019)
│       │   │   ├── process_monitor.py  # ProcessMonitor: background polling loop detecting
│       │   │   │                       #   unexpected process exits (crash, OOM, task manager kill)
│       │   │   ├── platform.py         # PlatformOps protocol + PosixOps + WindowsOps (ADR-019)
│       │   │   │                       #   Isolates: signals, process groups, Job Objects,
│       │   │   │                       #   alive checks, zombie cleanup
│       │   │   # └── ssh.py            # (future) SSHRunner
│       │   │   # └── slurm.py          # (future) SlurmRunner
│       │   │
│       │   ├── checkpoint.py           # WorkflowCheckpoint: serialise/deserialise workflow state
│       │   │                           #   (block states incl. CANCELLED/SKIPPED, skip_reasons,
│       │   │                           #    intermediate data refs, pending block)
│       │   │
│       │   └── events.py              # EventBus: publish/subscribe backbone of the runtime (ADR-018)
│       │                               #   14 event types: BLOCK_READY/RUNNING/PAUSED/DONE/ERROR/
│       │                               #   CANCELLED/SKIPPED, CANCEL_BLOCK/WORKFLOW_REQUEST,
│       │                               #   PROCESS_SPAWNED/EXITED, WORKFLOW_STARTED/COMPLETED,
│       │                               #   CHECKPOINT_SAVED. All runtime components subscribe.
│       │
│       │
│       │ ── Layer 4: AI Services ─────────────────────────────────
│       │
│       ├── ai/
│       │   ├── __init__.py
│       │   │
│       │   ├── generation/             # AI-driven code generation
│       │   │   ├── __init__.py
│       │   │   ├── block_generator.py  # Generate any of the 5 block types from NL description
│       │   │   ├── type_generator.py   # Generate new DataObject subtypes from NL description
│       │   │   ├── validator.py        # Validation pipeline: static analysis → dry run →
│       │   │   │                       #   port contract check → user review
│       │   │   └── templates.py        # Prompt templates for each block/type category
│       │   │
│       │   ├── synthesis/              # Workflow synthesis
│       │   │   ├── __init__.py
│       │   │   └── workflow_planner.py # Given data description + goal → propose DAG
│       │   │
│       │   └── optimization/           # Runtime parameter optimization
│       │       ├── __init__.py
│       │       └── param_optimizer.py  # Observe intermediate results → suggest/apply param changes
│       │
│       │
│       │ ── Layer 5: API ─────────────────────────────────────────
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py                  # FastAPI app factory, lifespan, CORS, middleware
│       │   │
│       │   ├── routes/                 # REST endpoints
│       │   │   ├── __init__.py
│       │   │   ├── workflows.py        # CRUD /api/workflows, execute, pause, resume, cancel
│       │   │   │                       #   + per-block cancel endpoint (ADR-018)
│       │   │   ├── blocks.py           # GET /api/blocks (palette), validate-connection
│       │   │   ├── data.py             # Upload, metadata, preview /api/data
│       │   │   ├── ai.py               # POST /api/ai/generate-block, suggest-workflow, optimize
│       │   │   └── projects.py         # Project CRUD, workspace management
│       │   │
│       │   ├── ws.py                   # WebSocket handler: bidirectional event routing (ADR-018)
│       │   │                           #   Inbound: cancel_block, cancel_workflow, interactive_complete
│       │   │                           #   Outbound: block_state, cancel_propagation, interactive_prompt
│       │   │
│       │   ├── sse.py                  # Server-Sent Events: log streaming from execution
│       │   │
│       │   ├── schemas.py              # Pydantic models for all API request/response shapes
│       │   │                           #   Includes CancelBlockRequest, CancelWorkflowRequest,
│       │   │                           #   CancelBlockResponse, CancelWorkflowResponse (ADR-018)
│       │   │
│       │   └── deps.py                 # FastAPI dependency injection (engine, registry, etc.)
│       │
│       │
│       │ ── Workflow Definition ───────────────────────────────────
│       │
│       ├── workflow/
│       │   ├── __init__.py
│       │   ├── definition.py           # WorkflowDefinition: nodes, edges, metadata
│       │   ├── serializer.py           # YAML ↔ WorkflowDefinition (load/save)
│       │   ├── validator.py            # Validate workflow: type compatibility, cycles,
│       │   │                           #   missing connections, port constraint pre-check
│       │   └── layout.py              # Optional node position storage for ReactFlow restore
│       │
│       │
│       │ ── Utilities ─────────────────────────────────────────────
│       │
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── hashing.py             # Content hashing for lineage (xxhash on data chunks)
│       │   ├── wrapping.py            # wrap_as_dataobject(): auto-detect type from raw data
│       │   ├── broadcast.py           # broadcast_apply(): named-axis-aware broadcast of
│       │   │                           #   low-dim arrays over high-dim arrays (e.g. mask → MSI)
│       │   └── logging.py             # Structured logging config (JSON, levels, rotation)
│       │
│       │
│       │ ── CLI ───────────────────────────────────────────────────
│       │
│       └── cli/
│           ├── __init__.py
│           └── main.py                 # CLI entry point:
│                                       #   scieasy serve      — start FastAPI server
│                                       #   scieasy run <wf>   — run workflow headless
│                                       #   scieasy validate   — validate workflow YAML
│                                       #   scieasy init       — create new project workspace
│                                       #   scieasy blocks     — list installed blocks
│
│
│ ══════════════════════════════════════════════════════════════════
│  REACT FRONTEND  (Layer 6)
│ ══════════════════════════════════════════════════════════════════
│
├── frontend/                                        # Phase 8 — planned, not yet created (ADR-023)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   │
│   └── src/
│       ├── main.tsx                    # React entry point
│       ├── App.tsx                     # Root layout: three-column + toolbar + bottom panel (ADR-023)
│       │
│       ├── components/
│       │   ├── Toolbar.tsx             # Projects menu, file, execution, edit buttons (ADR-023-Add1)
│       │   ├── ProjectDialog.tsx       # New/Open project modal dialogs (ADR-023-Add1)
│       │   ├── WelcomeScreen.tsx       # Welcome screen when no project is open (ADR-023-Add1)
│       │   │
│       │   ├── canvas/                 # ReactFlow integration
│       │   │   ├── WorkflowCanvas.tsx  # ReactFlow instance, minimap, zoom, pan
│       │   │   ├── BlockNode.tsx       # Custom node: header, inline config, ports, state badge
│       │   │   ├── PortHandle.tsx      # Custom handle: type-coloured circle / double-ring
│       │   │   ├── TypedEdge.tsx       # Custom edge: color-coded by source port type
│       │   │   └── SubWorkflowNode.tsx # Drill-down node for SubWorkflowBlock
│       │   │
│       │   ├── palette/                # Block palette (left column, full height)
│       │   │   ├── BlockPalette.tsx    # Searchable, categorised block list
│       │   │   └── BlockCard.tsx       # Draggable block card (icon, name, port summary)
│       │   │
│       │   ├── preview/                # Data preview (right column, full height)
│       │   │   ├── DataPreview.tsx     # Port selector, collection tabs, renderer dispatch
│       │   │   ├── TableRenderer.tsx   # DataFrame/PeakTable: paginated table, sort, search
│       │   │   ├── ImageRenderer.tsx   # Array/Image: zoomable, channel selector, brightness
│       │   │   ├── ChartRenderer.tsx   # Series/Spectrum: Plotly line chart
│       │   │   ├── TextRenderer.tsx    # Text: Monaco read-only with syntax highlighting
│       │   │   ├── ArtifactRenderer.tsx # Artifact: PDF/image inline, others metadata+download
│       │   │   └── CompositeRenderer.tsx # CompositeData: expandable slot list
│       │   │
│       │   └── bottom/                 # Bottom panel (browser-style tabs)
│       │       ├── BottomPanel.tsx      # Tab container with drag-resize handle
│       │       ├── AIChat.tsx           # AI conversational interface
│       │       ├── ConfigPanel.tsx      # Full parameter form from JSON Schema
│       │       ├── LogViewer.tsx        # SSE log stream with block/severity filters
│       │       ├── LineageView.tsx      # Provenance chain visualisation (Phase 8.5)
│       │       ├── JobsList.tsx         # Current/historical execution list (Phase 8.5)
│       │       └── ProblemsPanel.tsx    # Validation errors and warnings (Phase 8.5)
│       │
│       ├── hooks/
│       │   ├── useWebSocket.ts         # WebSocket connection + event dispatch to Zustand
│       │   ├── useSSE.ts               # SSE connection for log streaming
│       │   ├── useBlockRegistry.ts     # Fetch and cache block palette data
│       │   └── useWorkflow.ts          # Workflow CRUD operations
│       │
│       ├── store/
│       │   ├── index.ts                # Zustand store with slices
│       │   ├── projectSlice.ts         # Current project, recent projects, isProjectOpen (ADR-023-Add1)
│       │   ├── workflowSlice.ts        # Nodes, edges, workflow metadata
│       │   ├── executionSlice.ts       # Per-block state, timing, output refs (WebSocket)
│       │   ├── uiSlice.ts              # Panel widths, collapsed states, selected block, active tab
│       │   ├── previewSlice.ts         # Cached preview data keyed by StorageReference
│       │   ├── paletteSlice.ts         # Available blocks from registry, search filter
│       │   └── chatSlice.ts            # AI chat message history
│       │
│       ├── config/
│       │   └── typeColorMap.ts         # Base type → colour hex mapping for port handles/edges
│       │
│       ├── lib/
│       │   └── api.ts                  # Typed REST API client (fetch wrappers)
│       │
│       └── types/
│           ├── workflow.ts             # TypeScript types mirroring backend workflow schema
│           ├── blocks.ts               # Block metadata, port definitions, config schemas
│           └── data.ts                 # DataObject type info, preview payloads
│
│
│ ══════════════════════════════════════════════════════════════════
│  TESTS
│ ══════════════════════════════════════════════════════════════════
│
├── tests/
│   ├── conftest.py                     # Shared fixtures: sample data, temp project workspace
│   │
│   ├── architecture/                   # Structural enforcement tests (Phase 2)
│   │   ├── test_layer_deps.py          # Layer import direction: core→blocks→engine→api
│   │   ├── test_type_system.py         # DataObject hierarchy, axes, expected_slots,
│   │   │                               #   Collection is NOT DataObject (ADR-020)
│   │   ├── test_block_system.py        # Block category inheritance, run() signature
│   │   │                               #   matches dict[str, Collection] (ADR-020),
│   │   │                               #   process_item() signature (ADR-020 Addendum 5),
│   │   │                               #   Collection utilities exist on Block base class
│   │   ├── test_registries.py          # BlockSpec/TypeSpec storage, entry_points valid
│   │   └── test_placement.py           # Module docstrings, file placement conventions
│   │
│   ├── core/
│   │   ├── test_types.py              # DataObject hierarchy, TypeSignature, inheritance matching
│   │   ├── test_composite.py          # CompositeData slot access, nested composites
│   │   ├── test_storage.py            # Zarr/Arrow/filesystem read/write round-trips
│   │   ├── test_proxy.py              # ViewProxy: lazy loading, slice, iter_chunks
│   │   ├── test_lineage.py            # LineageRecord creation, SQLite store, graph queries
│   │   └── test_collection.py         # Collection construction, homogeneity, pack/unpack,
│   │                                   #   auto-flush in pack/map_items (ADR-020)
│   │
│   ├── blocks/
│   │   ├── test_ports.py              # Port type matching, constraint validation
│   │   ├── test_io_block.py           # Load/save across formats via adapters
│   │   ├── test_process_block.py      # Built-in transforms: merge, split, transform
│   │   ├── test_code_block.py         # Inline + script mode, Python/R runners
│   │   ├── test_app_block.py          # Mock external app lifecycle (launch → watch → resume)
│   │   ├── test_ai_block.py           # Mock LLM responses, structured output parsing
│   │   ├── test_subworkflow.py        # Nested workflow execution, input/output mapping
│   │   ├── test_registry.py           # Block discovery via entry_points
│   │   └── test_lazy_list.py          # LazyList iteration, indexing, len, GC (ADR-020 Addendum 4)
│   │
│   ├── engine/
│   │   ├── test_dag.py                # DAG construction, topological sort, cycle detection
│   │   ├── test_scheduler.py          # Event-driven execution, cancel propagation, SKIPPED
│   │   ├── test_resources.py          # ResourceManager acquire/release, auto-release via EventBus
│   │   ├── test_checkpoint.py         # Serialise/restore with CANCELLED/SKIPPED states
│   │   ├── test_process_handle.py     # ProcessHandle terminate/kill, platform ops (ADR-019)
│   │   ├── test_process_monitor.py    # Death detection, event emission (ADR-019)
│   │   └── test_events.py            # EventBus emit/subscribe, error isolation (ADR-018)
│   │
│   ├── ai/
│   │   ├── test_block_generator.py    # Generate all 5 block types, validation pipeline
│   │   ├── test_type_generator.py     # Generate DataObject subtypes, slot declarations
│   │   └── test_workflow_planner.py   # Workflow synthesis from NL description
│   │
│   ├── api/
│   │   ├── test_workflow_routes.py    # REST CRUD, execute, pause, resume
│   │   ├── test_block_routes.py       # Block listing, connection validation
│   │   └── test_ws.py                 # WebSocket message flow, interactive block signals
│   │
│   ├── workflow/
│   │   ├── test_serializer.py         # YAML round-trip, layout preservation
│   │   └── test_validator.py          # Type mismatch detection, dangling ports
│   │
│   └── integration/
│       ├── test_multimodal_workflow.py # Full example: LC-MS + Raman + IF + SRS pipeline
│       └── test_subworkflow_nesting.py # Recursive SubWorkflowBlock composition
│
│
│ ══════════════════════════════════════════════════════════════════
│  DOCS & CONFIG
│ ══════════════════════════════════════════════════════════════════
│
├── docs/
│   ├── getting-started.md             # Installation, first workflow, tutorial
│   ├── block-development.md           # How to write a custom block (with examples)
│   ├── type-extension.md              # How to create new DataObject subtypes
│   ├── script-integration.md          # CodeBlock inline vs script mode guide
│   ├── external-apps.md              # How to configure AppBlock for your software
│   └── api-reference.md              # Auto-generated from FastAPI OpenAPI schema
│
├── examples/
│   ├── workflows/
│   │   ├── raman_preprocessing.yaml   # Simple: load → denoise → baseline → export
│   │   ├── lcms_elmaven.yaml          # With AppBlock: load → ElMAVEN → R annotation
│   │   └── multimodal_fusion.yaml     # Full: LC-MS + Raman + IF + SRS (from Appendix A)
│   │
│   ├── blocks/
│   │   ├── savgol_smooth.py           # Example ProcessBlock: Savitzky-Golay smoothing
│   │   └── deseq2_analysis.R          # Example CodeBlock script mode: DESeq2 in R
│   │
│   └── types/
│       └── maldi_image.py             # Example CompositeData subtype: MALDIImage
│
└── .github/
    └── workflows/
        ├── ci.yml                     # Lint + test on PR
        └── release.yml                # Build + publish to PyPI
```

## Module dependency graph

```
                 cli/main.py
                      │
                      ▼
                  api/app.py
                 ╱    │    ╲
                ▼     ▼     ▼
          api/routes  api/ws  api/sse
                ╲     │     ╱
                 ▼    ▼    ▼
              engine/scheduler.py
              ╱      │       ╲
             ▼       ▼        ▼
      engine/    engine/
      resources  runners/
                     │
              ┌──────┼──────────────────┐
              ▼      ▼                  ▼
         blocks/  blocks/base/     workflow/
         registry  (Block ABC,      definition.py
              │     ports, state)    serializer.py
              │         │
              │    ┌────┼────┬────┬────┬────┐
              │    ▼    ▼    ▼    ▼    ▼    ▼
              │   io/ process/ code/ app/ ai/ subworkflow/
              │
              └──────────────┐
                             ▼
                         core/types/     ← everything depends on this
                         core/storage/
                         core/proxy.py
                         core/lineage/
```

## Key entry_points (pyproject.toml)

```toml
[project.scripts]
scieasy = "scieasy.cli.main:app"

[project.entry-points."scieasy.blocks"]
# Built-in blocks
io_block = "scieasy.blocks.io:IOBlock"
process_merge = "scieasy.blocks.process.builtins.merge:MergeBlock"
process_split = "scieasy.blocks.process.builtins.split:SplitBlock"
code_block = "scieasy.blocks.code:CodeBlock"
app_block = "scieasy.blocks.app:AppBlock"
ai_block = "scieasy.blocks.ai:AIBlock"
subworkflow_block = "scieasy.blocks.subworkflow:SubWorkflowBlock"

[project.entry-points."scieasy.adapters"]
csv = "scieasy.blocks.io.adapters.csv_adapter:CSVAdapter"
tiff = "scieasy.blocks.io.adapters.tiff_adapter:TIFFAdapter"
mzxml = "scieasy.blocks.io.adapters.mzxml_adapter:MzXMLAdapter"
h5ad = "scieasy.blocks.io.adapters.h5ad_adapter:H5ADAdapter"
parquet = "scieasy.blocks.io.adapters.parquet_adapter:ParquetAdapter"

[project.entry-points."scieasy.types"]
# Built-in domain types (base types are always available, no entry_point needed)
image = "scieasy.core.types.array:Image"
spectrum = "scieasy.core.types.series:Spectrum"
peak_table = "scieasy.core.types.dataframe:PeakTable"

[project.entry-points."scieasy.runners"]
python = "scieasy.blocks.code.runners.python_runner:PythonRunner"
r = "scieasy.blocks.code.runners.r_runner:RRunner"
julia = "scieasy.blocks.code.runners.julia_runner:JuliaRunner"
```

## File count summary

| Directory | Python files | Purpose |
|---|---|---|
| `core/` | 15 | Data types, Collection transport, storage, proxy, lineage |
| `blocks/` | 30 | All block categories, adapters, runners, registry, lazy_list (process_mgr.py deleted per ADR-019, lazy_list.py added per ADR-020) |
| `engine/` | 10 | Scheduler, resources, checkpoint, events, runners (worker, process_handle, process_monitor, platform) |
| `ai/` | 6 | Generation, synthesis, optimization |
| `api/` | 9 | FastAPI routes, WebSocket, SSE |
| `workflow/` | 4 | Definition, serialization, validation, layout |
| `utils/` | 3 | Hashing, wrapping, logging |
| `cli/` | 1 | CLI entry point |
| **Total backend** | **~78** | |
| `frontend/src/` | ~34 `.tsx/.ts` | React components, hooks, stores, config, API client (ADR-023, ADR-023-Add1) |
| `tests/` | ~30 | Architecture enforcement, unit, and integration tests |
