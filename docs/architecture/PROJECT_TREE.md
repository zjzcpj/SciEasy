# SciEasy — Project Tree

> Maps 1:1 to the Architecture Document (ARCHITECTURE.md).
> Each file is annotated with its responsibility.

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
│       │       ├── record.py           # LineageRecord dataclass (hashes, config, environment)
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
│       │   │   │                       #   execution_mode, batch_mode, resource_request
│       │   │   ├── ports.py            # Port, InputPort, OutputPort
│       │   │   │                       #   Type matching + optional constraint function
│       │   │   ├── config.py           # BlockConfig: validated param container (Pydantic)
│       │   │   ├── state.py            # BlockState enum, ExecutionMode, BatchMode enums
│       │   │   └── result.py           # BlockResult, BatchResult (succeeded/failed/skipped)
│       │   │
│       │   ├── io/                     # IOBlock — data ingress / egress
│       │   │   ├── __init__.py
│       │   │   ├── io_block.py         # IOBlock: direction="input"|"output", format dispatch
│       │   │   ├── adapters/           # Pluggable format adapters
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base.py         # FormatAdapter protocol (read → DataObject, write → file)
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
│       │   │   ├── runners/            # Language-specific execution environments
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base.py         # CodeRunner protocol (execute_inline, execute_script)
│       │   │   │   ├── python_runner.py    # Python: exec() for inline, importlib for script
│       │   │   │   ├── r_runner.py         # R: rpy2 bridge or Rscript subprocess
│       │   │   │   └── julia_runner.py     # Julia: juliacall or subprocess
│       │   │   ├── runner_registry.py  # Maps language string → runner class
│       │   │   └── introspect.py       # Script introspection: parse run() signature,
│       │   │                           #   extract configure() schema, auto-gen ports
│       │   │
│       │   ├── app/                    # AppBlock — external GUI software bridge
│       │   │   ├── __init__.py
│       │   │   ├── app_block.py        # AppBlock: launch → pause → watch → resume
│       │   │   ├── bridge.py           # ExternalAppBridge protocol (serialise, launch, watch)
│       │   │   ├── watcher.py          # File watcher (watchdog) for output detection
│       │   │   └── process_mgr.py      # External process lifecycle management (subprocess)
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
│       │   ├── scheduler.py            # DAGScheduler: walk DAG in topo-order,
│       │   │                           #   check readiness, dispatch blocks, propagate state
│       │   │
│       │   ├── batch.py                # BatchExecutor: handles parallel/serial/adaptive
│       │   │                           #   dispatch for collections of data items.
│       │   │                           #   Implements BatchErrorStrategy (stop/skip/retry/pause).
│       │   │
│       │   ├── resources.py            # ResourceManager: GPU slots, CPU workers, memory budget.
│       │   │                           #   ResourceRequest dataclass. acquire()/release().
│       │   │
│       │   ├── runners/                # BlockRunner protocol + implementations
│       │   │   ├── __init__.py
│       │   │   ├── base.py             # BlockRunner protocol (run, check_status, cancel)
│       │   │   └── local.py            # LocalRunner: in-process / subprocess execution
│       │   │   # └── ssh.py            # (future) SSHRunner
│       │   │   # └── slurm.py          # (future) SlurmRunner
│       │   │
│       │   ├── checkpoint.py           # WorkflowCheckpoint: serialise/deserialise workflow state
│       │   │                           #   (block states, intermediate data refs, pending block)
│       │   │
│       │   └── events.py              # Engine event bus: block state changes, progress updates.
│       │                               #   Consumed by API layer for WebSocket broadcast.
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
│       │   │   ├── workflows.py        # CRUD /api/workflows, execute, pause, resume
│       │   │   ├── blocks.py           # GET /api/blocks (palette), validate-connection
│       │   │   ├── data.py             # Upload, metadata, preview /api/data
│       │   │   ├── ai.py               # POST /api/ai/generate-block, suggest-workflow, optimize
│       │   │   └── projects.py         # Project CRUD, workspace management
│       │   │
│       │   ├── ws.py                   # WebSocket handler: real-time block state, progress,
│       │   │                           #   interactive block signals (prompt / complete)
│       │   │
│       │   ├── sse.py                  # Server-Sent Events: log streaming from execution
│       │   │
│       │   ├── schemas.py              # Pydantic models for all API request/response shapes
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
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   │
│   └── src/
│       ├── main.tsx                    # React entry point
│       ├── App.tsx                     # Top-level layout: palette | canvas | config panel
│       │
│       ├── components/
│       │   ├── canvas/                 # ReactFlow integration
│       │   │   ├── WorkflowCanvas.tsx  # ReactFlow instance, event handlers, minimap
│       │   │   ├── BlockNode.tsx       # Custom ReactFlow node: ports, state badge, progress
│       │   │   ├── TypedEdge.tsx       # Custom edge: color-coded by data type
│       │   │   └── SubWorkflowNode.tsx # Drill-down node for SubWorkflowBlock
│       │   │
│       │   ├── palette/                # Block palette sidebar
│       │   │   ├── BlockPalette.tsx    # Searchable, categorised block list
│       │   │   └── BlockCard.tsx       # Draggable block card (icon, name, port summary)
│       │   │
│       │   ├── config/                 # Block config panel (right sidebar)
│       │   │   ├── ConfigPanel.tsx     # Auto-generated form from JSON Schema
│       │   │   ├── CodeEditor.tsx      # Monaco-based editor for CodeBlock inline mode
│       │   │   ├── ScriptPicker.tsx    # File picker for CodeBlock script mode
│       │   │   └── PortInspector.tsx   # Port types, constraints, connection status
│       │   │
│       │   ├── status/                 # Execution status bar
│       │   │   ├── StatusBar.tsx       # Overall progress, run/pause/resume controls
│       │   │   ├── LogStream.tsx       # Live log viewer (SSE consumer)
│       │   │   └── BatchProgress.tsx   # Per-item progress for batch execution
│       │   │
│       │   └── data/                   # Data preview components
│       │       ├── TablePreview.tsx     # First N rows of DataFrame
│       │       ├── ImagePreview.tsx     # Thumbnail viewer for Array/Image
│       │       ├── SpectrumPreview.tsx  # Plotly line chart for Series/Spectrum
│       │       └── CompositePreview.tsx # Tabbed view of CompositeData slots
│       │
│       ├── hooks/
│       │   ├── useWebSocket.ts         # WebSocket connection for live block state
│       │   ├── useSSE.ts               # SSE connection for log streaming
│       │   ├── useBlockRegistry.ts     # Fetch and cache block palette data
│       │   └── useWorkflow.ts          # Workflow CRUD operations
│       │
│       ├── stores/
│       │   ├── workflowStore.ts        # Zustand: workflow definition, node/edge state
│       │   ├── executionStore.ts       # Zustand: block states, progress, batch results
│       │   └── uiStore.ts             # Zustand: selected block, panel visibility, layout
│       │
│       ├── api/
│       │   └── client.ts              # Typed API client (REST endpoints → fetch wrappers)
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
│   ├── core/
│   │   ├── test_types.py              # DataObject hierarchy, TypeSignature, inheritance matching
│   │   ├── test_composite.py          # CompositeData slot access, nested composites
│   │   ├── test_storage.py            # Zarr/Arrow/filesystem read/write round-trips
│   │   ├── test_proxy.py              # ViewProxy: lazy loading, slice, iter_chunks
│   │   └── test_lineage.py            # LineageRecord creation, SQLite store, graph queries
│   │
│   ├── blocks/
│   │   ├── test_ports.py              # Port type matching, constraint validation
│   │   ├── test_io_block.py           # Load/save across formats via adapters
│   │   ├── test_process_block.py      # Built-in transforms: merge, split, transform
│   │   ├── test_code_block.py         # Inline + script mode, Python/R runners
│   │   ├── test_app_block.py          # Mock external app lifecycle (launch → watch → resume)
│   │   ├── test_ai_block.py           # Mock LLM responses, structured output parsing
│   │   ├── test_subworkflow.py        # Nested workflow execution, input/output mapping
│   │   └── test_registry.py           # Block discovery via entry_points
│   │
│   ├── engine/
│   │   ├── test_dag.py                # DAG construction, topological sort, cycle detection
│   │   ├── test_scheduler.py          # End-to-end workflow execution, state propagation
│   │   ├── test_batch.py              # Parallel/serial/adaptive modes, error strategies
│   │   ├── test_resources.py          # ResourceManager acquire/release, GPU throttling
│   │   └── test_checkpoint.py         # Serialise/restore workflow state, resume from pause
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
      engine/    engine/    engine/
      batch.py   resources  runners/
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
| `core/` | 14 | Data types, storage, proxy, lineage |
| `blocks/` | 30 | All block categories, adapters, runners, registry |
| `engine/` | 7 | Scheduler, batch, resources, checkpoint, events |
| `ai/` | 6 | Generation, synthesis, optimization |
| `api/` | 9 | FastAPI routes, WebSocket, SSE |
| `workflow/` | 4 | Definition, serialization, validation, layout |
| `utils/` | 3 | Hashing, wrapping, logging |
| `cli/` | 1 | CLI entry point |
| **Total backend** | **~74** | |
| `frontend/src/` | ~25 `.tsx/.ts` | React components, hooks, stores, API client |
| `tests/` | ~22 | Unit + integration tests |
