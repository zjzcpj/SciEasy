# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- [#237] Fix canvas annotation code review issues — MiniMap crash guard, DAG edge KeyError guard, random position offset (@claude, 2026-04-06, branch: fix/issue-237/code-review-fixes)

### Added

- [#233] Parameter optimization -- LLM-powered param suggestions with schema validation (@claude, 2026-04-05, branch: feat/issue-233/param-optimizer, session: 20260405-235030-feat-233-parameter-optimization-backend)
- [#230] Type Generator + Validator Stages 4-5 — generate_type() with LLM-driven code generation, family inference, retry loop; dry_run_generated_code() stage 4, validate_port_contracts() stage 5, validate_generated_type() pipeline; 45 new tests (@claude, 2026-04-05, branch: feat/issue-230/type-generator-validator, session: 20260405-232504-phase-9-1c-type-generator-validator-stag)
- [#229] Block Generator + API endpoint wiring — generate_block() pipeline with category inference, prompt construction, LLM call, code extraction, validation, retry loop; POST /api/ai/generate-block endpoint; 33 tests (@claude, 2026-04-05, branch: feat/issue-229/block-generator, session: 20260405-232453-phase-9-1b-block-generator-api-endpoint)
- [#241] Phase 10 Roadmap v0.3 — 4-stage integration plan: palette refinement, 5 domain plugin packages, block-level testing, demo workflows (@claude, 2026-04-05, branch: docs/phase10-roadmap-v0.3, session: 20260405-234433-phase-10-roadmap-v0-3-integration-domain)
- [#237] Canvas annotation and group frame nodes -- _annotation (floating text note) and _group (resizable dashed-border frame) with toolbar buttons, DAG skip for _-prefixed nodes, 13 tests (@claude, 2026-04-05, branch: feat/issue-237/canvas-annotations, session: 20260405-232810-canvas-annotations-and-group-frames-237)
- [#228] LLM Provider Foundation — LLMProvider protocol, AnthropicProvider, OpenAIProvider, AIConfig, get_provider() factory, extract_code/extract_json parsers, [ai] optional deps, 64 tests (@claude, 2026-04-05, branch: feat/issue-228/llm-provider-foundation, session: 20260405-225710-phase-9-1a-llm-provider-foundation-228)
- [#218] Block SDK end-to-end integration tests — 30 tests covering registry entry-point roundtrip, Tier 1 drop-in scanning, adapter priority enforcement, TypeRegistry entry-points, and cross-cutting integration (@claude, 2026-04-05, branch: test/issue-218/block-sdk-e2e, session: 20260405-225642-t3-5-block-sdk-integration-test-218)
- [#217] Comprehensive block SDK developer guide covering all 5 block types, Tier 1/2 distribution, Collection transport, port system, configuration, and testing (@claude, 2026-04-05, branch: docs/issue-217/block-sdk-guide, session: 20260405-225639-t3-4-developer-documentation-for-block-s)
- [#215] BlockTestHarness utility for external block developers — validates block contracts, PackageInfo, entry-point callables, and smoke-test execution (@claude, 2026-04-05, branch: feat/issue-215/block-test-harness, session: 20260405-224022-t3-1-blocktestharness-utility-215)
- [#224] Write comprehensive project README.md covering architecture, features, tech stack, installation, and development setup (@claude, 2026-04-05, branch: docs/issue-224/readme-and-gitattributes, session: 20260405-223925-write-comprehensive-readme-md-and-fix-17)
- [#172] Add .gitattributes with CHANGELOG.md merge=union to prevent merge conflicts (@claude, 2026-04-05, branch: docs/issue-224/readme-and-gitattributes, session: 20260405-223925-write-comprehensive-readme-md-and-fix-17)

### Fixed

- [#233] Expose search_space in optimize-params API, wire endpoint to param_optimizer, remove dead NotImplementedError catch (@claude, 2026-04-05, branch: feat/issue-233/param-optimizer)
- [#206] Browse button supports file multi-select for Load blocks, folder select for Save blocks (@claude, 2026-04-06, branch: fix/issue-206-207-208/io-block-ux)
- [#207] Remove unused Format Override field from IO block config schema (@claude, 2026-04-06, branch: fix/issue-206-207-208/io-block-ux)
- [#208] Hide direction field in bottom Config panel for IO blocks to match canvas display (@claude, 2026-04-06, branch: fix/issue-206-207-208/io-block-ux)
- [#203] Handle asyncio.CancelledError in WebSocket handler for clean server shutdown (@claude, 2026-04-05, branch: fix/issue-203/ws-shutdown-hang, session: 20260405-212520-fix-websocket-shutdown-hang-by-handling)
- [#195] Guard panel resize persistence — minimum size threshold in onLayoutChanged + hydration validation in Zustand store (@claude, 2026-04-05, branch: fix/issue-195/panel-resize-persist, session: 20260405-205531-fix-panel-resize-broken-onlayoutchanged)
- [#194] Improve project dialog UX — remove useless "Optional note" field, add Browse button for native directory selection (@claude, 2026-04-05, branch: fix/issue-194/project-dialog-browse, session: 20260405-205530-fix-project-dialog-ux-remove-useless-fie)
- [#192] Fix post-redesign frontend: panel resize handles (12px hit area), block delete button, IO block split into Load/Save, drag ghost preview, port label row removal, horizontal scrollbar overflow (@claude, 2026-04-05, branch: fix/issue-192/post-redesign-frontend, session: 20260405-202012-fix-p0-post-redesign-frontend-issues-pan)
- [#179] Restrict CORS origins to localhost by default, configurable via SCIEASY_CORS_ORIGINS env var (@claude, 2026-04-05, branch: fix/issue-179/cors-origins, session: 20260405-193319-fix-179-restrict-cors-allow-origins-befo)
- [#178] Replace PPM image preview with PNG encoding for universal browser support (@claude, 2026-04-05, branch: fix/issue-178/png-image-preview, session: 20260405-192915-fix-178-replace-ppm-image-preview-with-p)
- [#180] Generate block config schema from Block class metadata instead of hardcoding (@claude, 2026-04-05, branch: fix/issue-180/block-config-schema, session: 20260405-193622-fix-180-generate-block-config-schema-fro)
- [#184] Align frontend GUI with ARCHITECTURE.md Section 9 spec: resizable 3-column layout, 3-part BlockNode with inline editable config, spec-correct port type colors, 6 bottom panel tabs, 14+ keyboard shortcuts, shadcn/ui integration, Projects dropdown toolbar (@claude, 2026-04-05, branch: fix/issue-184/frontend-spec-compliance, session: 20260405-192530-fix-critical-frontend-design-deviations)
- [#182] Add Vite dev server proxy for /api and /ws to fix HTML-instead-of-JSON error in dev mode (@claude, 2026-04-05, branch: fix/issue-182/vite-api-proxy, session: 20260405-182205-fix-frontend-dev-server-missing-api-prox)
- [#166] Create LineageRecorder component that persists LineageRecord on terminal block events via EventBus (@claude, 2026-04-05, branch: fix/batch-b2/issues-166-169, session: 20260405-163539-fix-issues-166-169-lineagerecorder-zarrb)
- [#167] Make ZarrBackend.write() atomic via write-to-temp-then-rename (@claude, 2026-04-05, branch: fix/batch-b2/issues-166-169, session: 20260405-163539-fix-issues-166-169-lineagerecorder-zarrb)
- [#168] Guard against Collection with None item_type in worker.py serialise_outputs (@claude, 2026-04-05, branch: fix/batch-b2/issues-166-169, session: 20260405-163539-fix-issues-166-169-lineagerecorder-zarrb)
- [#169] Replace silent except-continue in BlockRegistry with logged warnings (@claude, 2026-04-05, branch: fix/batch-b2/issues-166-169, session: 20260405-163539-fix-issues-166-169-lineagerecorder-zarrb)
- [#162] Replace blocking popen.communicate() with run_in_executor so asyncio event loop stays responsive during block execution (@claude, 2026-04-05, branch: fix/batch-b1/issues-162-163-164, session: 20260405-154742-fix-localrunner-async-blocking-dagschedu)
- [#163] Add PROCESS_EXITED subscription to DAGScheduler and align block_id between ProcessHandle and scheduler for crash detection (@claude, 2026-04-05, branch: fix/batch-b1/issues-162-163-164, session: 20260405-154742-fix-localrunner-async-blocking-dagschedu)
- [#164] Wire CheckpointManager into DAGScheduler pause/resume with auto-save on terminal events for crash recovery (@claude, 2026-04-05, branch: fix/batch-b1/issues-162-163-164, session: 20260405-154742-fix-localrunner-async-blocking-dagschedu)
- [#165] Fix Windows path assertions in test_adapters, test_data_object_persistence, and test_app_block after StorageReference POSIX normalization (@claude, 2026-04-05, branch: fix/issue-165/windows-test-paths, session: 20260405-155826-fix-windows-path-assertions-in-test-adap)
- [#120] Unwrap subprocess output envelope in LocalRunner so downstream sees port names at top level (@claude, 2026-04-05, branch: fix/batch-a3/issues-120-132-122, session: 20260405-014138-fix-subprocess-runner-output-pipeline-12)
- [#132] Preserve TypeSignature type_chain across subprocess boundary in worker serialization/reconstruction (@claude, 2026-04-05, branch: fix/batch-a3/issues-120-132-122, session: 20260405-014138-fix-subprocess-runner-output-pipeline-12)
- [#122] Fix unawaited async emit() in spawn_block_process by scheduling via create_task (@claude, 2026-04-05, branch: fix/batch-a3/issues-120-132-122, session: 20260405-014138-fix-subprocess-runner-output-pipeline-12)
- [#128] Remove self.transition() calls from Block.run() methods — state management is scheduler responsibility, not block (@claude, 2026-04-05, branch: fix/issue-128/remove-block-self-transition)
- [#119] Inject BlockRegistry into DAGScheduler — resolve NodeDef.block_type to Block instance before dispatch (@claude, 2026-04-05, branch: fix/batch-a2/issues-119-121, session: 20260405-003357-wave-a2-inject-blockregistry-into-dagsch)
- [#121] Pass BlockRegistry to CLI validate/run commands — enable type-compatibility and dangling-port checks (@claude, 2026-04-05, branch: fix/batch-a2/issues-119-121, session: 20260405-003357-wave-a2-inject-blockregistry-into-dagsch)
### Added

- [#216] Block package templates and `scieasy init-block-package` CLI scaffold command (ADR-026 Phase 3.2+3.3) (@claude, 2026-04-05, branch: feat/issue-216/block-package-templates, session: 20260405-223950-t3-2-3-3-block-package-templates-cli-sca)
- [#213] AdapterRegistry priority enforcement: external adapters cannot override built-in extensions (ADR-025 Phase 2.4) (@claude, 2026-04-05, branch: feat/issue-213/adapter-priority)
- [#212] TypeRegistry entry-points scanning for external type plugins (ADR-025 Phase 2.3) (@claude, 2026-04-05, branch: feat/issue-212/type-registry-entrypoints, session: 20260405-221125-typeregistry-entry-points-scanning-phase)
- [#211] PackageInfo dataclass and BlockRegistry callable entry-points protocol (ADR-025 Phase 2.1+2.2) (@claude, 2026-04-05, branch: feat/issue-211/package-info-registry)
- [#189] Frontend bundling, SPA serving, and `scieasy gui` command (ADR-024 Phase 1) (@claude, 2026-04-05, branch: feat/issue-189/frontend-bundling-gui, session: 20260405-194020-phase-1-frontend-bundling-and-scieasy-gu)
- [#64] AI generation templates and validation pipeline updated for Collection model (@claude, 2026-04-05, branch: feat/issue-64/ai-generation-templates, session: 20260405-014102-feat-ai-generation-templates-for-collect)
- [#127] Auto-flush data persistence pipeline: BackendRouter MRO resolution, flush_context, DataObject.save() with idempotency, _auto_flush() safety net (@claude, 2026-04-05, branch: fix/batch-a1/issues-127-49-52-67)
### Fixed

- [#125] Add AIBlock to _infer_category() so AIBlock subclasses get category "ai" instead of "unknown" (@claude, 2026-04-05, branch: fix/issue-125/aiblock-infer-category, session: 20260405-004900-issue-125-add-aiblock-to-infer-category)

### Removed

- [#59] Remove InputDelivery enum — MEMORY-only delivery via ADR-020 Collection auto-unpack (@claude, 2026-04-04, branch: fix/batch-1/issues-59-57-58-48, session: 20260404-192842-batch-1-remove-inputdelivery-postprocess)

### Changed

- [#55] Item-level hashing for Collection lineage — LineageRecord hash fields from list[str] to dict[str, list[str]], backward-compat store parsing, collection_hashes() utility (@claude, 2026-04-05, branch: feat/issue-55/collection-item-level-hashing, session: 20260405-004917-issue-55-item-level-hashing-for-collecti)
- [#123] Update Block.run() signature from dict[str, Any] to dict[str, Collection] across base + all subclasses, add architecture test; wrap MergeBlock/SplitBlock outputs in Collection (@claude, 2026-04-05, branch: fix/issue-123/block-run-collection-signature, session: 20260405-002441-issue-123-block-run-signature-dict-str-a)
- [#126] Sync ARCHITECTURE.md run() signature and ADR-017/018 status (@claude, 2026-04-05, branch: docs/issue-126/docs-sync-adr-architecture, session: 20260405-003356-docs-sync-architecture-md-and-adr-status)
- [#123] Update Block.run() signature from dict[str, Any] to dict[str, Collection] across base + all subclasses, add architecture test (@claude, 2026-04-05, branch: fix/issue-123/block-run-collection-signature, session: 20260405-002441-issue-123-block-run-signature-dict-str-a)
- [#57] Update Block.postprocess() type annotation to dict[str, Collection] (@claude, 2026-04-04, branch: fix/batch-1/issues-59-57-58-48, session: 20260404-192842-batch-1-remove-inputdelivery-postprocess)
- [#58] Document that port constraint functions receive Collection objects (@claude, 2026-04-04, branch: fix/batch-1/issues-59-57-58-48, session: 20260404-192842-batch-1-remove-inputdelivery-postprocess)
- [#124] Distinguish planned vs existing files in PROJECT_TREE.md (@claude, 2026-04-05, branch: docs/issue-124/project-tree-clarity, session: 20260405-003343-docs-project-tree-md-planned-vs-existing)

### Fixed

- [#51] Atomic write for FilesystemBackend; document Zarr/Composite write atomicity risks (@claude, 2026-04-05, branch: fix/issue-51/storage-write-atomicity, session: 20260405-004830-fix-storage-write-atomicity-on-cancel-cr)

### Fixed

- [#68] Move AppBlock exchange directory from system temp to project workspace (@claude, 2026-04-05, branch: fix/issue-68/appblock-exchange-dir, session: 20260405-004749-fix-appblock-exchange-dir-in-project-wor)

### Added

- [#159] Deliver Phase 7-8 project-first API and React workflow editor with live execution, previews, and frontend/backend test coverage (@Codex, 2026-04-05, branch: codex/phase7-8, session: 20260405-025125-phase-7-8-full-stack-delivery-api-layer)

- [#61] Selective re-run logic — reset_block() with dependency chain validation (@claude, 2026-04-05, branch: feat/issue-61/selective-rerun, session: 20260405-010832-feat-selective-re-run-reset-block-in-dag)
- [#60] SubWorkflowBlock nested subprocess cleanup — SIGTERM callback and Windows Job Object (@claude, 2026-04-05, branch: feat/issue-60/subworkflow-cleanup, session: 20260405-010910-feat-subworkflowblock-nested-subprocess)
- [#65] FastAPI lifespan shutdown terminates block subprocesses via ProcessRegistry (@claude, 2026-04-05, branch: feat/issue-65/fastapi-lifespan-shutdown, session: 20260405-010805-feat-fastapi-lifespan-shutdown-processre)
- [#54] Capture EnvironmentSnapshot inside subprocess for accurate lineage data (@claude, 2026-04-05, branch: feat/issue-54/env-snapshot-subprocess, session: 20260405-005852-feat-capture-environmentsnapshot-in-subp)
- [#62] Checkpoint intermediate_refs Collection serialization for resume support (@claude, 2026-04-05, branch: feat/issue-62/checkpoint-collection-refs, session: 20260405-005921-feat-checkpoint-intermediate-refs-collec)
- [#72] ResourceRequest max_internal_workers for accurate CPU accounting with parallel_map (@claude, 2026-04-05, branch: feat/issue-72/resource-request-workers, session: 20260405-005829-feat-resourcerequest-max-internal-worker)
- [#76] broadcast_apply memory guard, Array.__array__() protocol, in-memory scope docs (@claude, 2026-04-05, branch: feat/issue-76/broadcast-apply-improvements, session: 20260405-004843-feat-broadcast-apply-memory-guard-array)
- [#133] Add example workflow YAML files for CLI testing — raman_preprocessing, simple_merge, image_pipeline (@claude, 2026-04-05, branch: chore/issue-133/example-workflows, session: 20260405-002958-add-example-workflow-yaml-files-for-cli)
- [#48] Enforce JSON-serializable metadata on DataObject construction (@claude, 2026-04-04, branch: fix/batch-1/issues-59-57-58-48, session: 20260404-192842-batch-1-remove-inputdelivery-postprocess)

- [#113] Implement all ADR-017–022 TODO stubs, raise coverage threshold to 85% — resolve 38 TODOs across 32 files, implement WebSocket handler, ProcessExitedWithoutOutputError, create_reference(), Collection unpack/pack, CheckpointManager integration, ViewProxy.from_file(), add 24 new tests (@claude, 2026-04-04, branch: feat/issue-113/implement-all-todos-raise-coverage, session: 20260404-170726-implement-all-todo-stubs-adr-017-to-adr)
- [#109] Phase 6.2: Implement scieasy CLI commands — init, validate, run, blocks, serve with typer.testing smoke tests (@claude, 2026-04-04, branch: phase6/cli-commands)
- [#108] Phase 6.1: Workflow validator with type checking, cycle detection, dangling port detection — 6 ordered validation checks, 21 tests (@claude, 2026-04-04, branch: phase6/workflow-validator, session: 20260404-052508-phase-6-1-workflow-validator)
- [#107] Phase 6.1: YAML workflow serializer with Pydantic schema — load_yaml/save_yaml, schema validation, optional layout field, 10 tests (@claude, 2026-04-04, branch: phase6/workflow-serializer, session: 20260404-052427-phase-6-1-yaml-serializer-with-pydantic)
- [#105] Phase 5.8: Integration tests for execution engine — 23 tests exercising DAG+EventBus+Collection+Scheduler+cancellation+cycle detection end-to-end (@claude, 2026-04-04, branch: feat/issue-105/integration-tests, session: 20260404-051442-phase-5-8-integration-tests)
- [#102] Phase 5.7: SubWorkflowBlock scheduler factory injection and Collection passthrough — _scheduler_factory ClassVar for engine-layer injection (import-linter safe), fallback to _sequential_execute, Collections flow through unchanged, 3 new tests (@claude, 2026-04-04, branch: feat/issue-102/subworkflow-completion, session: 20260404-050108-phase-5-7-subworkflowblock-completion)
- [#101] Phase 5.4: Checkpoint serialization + CheckpointManager — ADR-018 JSON save/load with ISO-8601 timestamps, CheckpointManager directory-based storage with EventBus auto-subscription, skip_reasons for CANCELLED/SKIPPED states, 9 tests (@claude, 2026-04-04, branch: feat/issue-101/checkpoint-pause-resume, session: 20260404-050056-phase-5-4-checkpoint-serialization-check)
- [#98] Phase 5.1: DAG construction + event-driven DAGScheduler — ADR-018 DAG dataclass, build_dag, topological_sort (Kahn's), CycleError, skip propagation, pause/resume, input gathering, 38 tests (@claude, 2026-04-04, branch: feat/issue-8/dag-scheduler, session: 20260404-044439-phase-5-1-dag-construction-scheduling-ad)
- [#87] Phase 5.0c: IOBlock lazy Collection + adapter create_reference (ADR-020-Add2) -- FormatAdapter.create_reference() protocol, lazy StorageReference construction in IOBlock, Collection support in FileExchangeBridge.prepare(), ZarrAdapter scaffold (@claude, 2026-04-04, branch: feat/issue-87/ioblock-lazy-collection, session: 20260404-041549-phase-5-0c-ioblock-lazy-collection-adapt)
- [#96] Phase 5.2b: ProcessMonitor + LocalRunner + worker.py — ADR-017/019 async process death detection, subprocess-based block execution, worker entry point, RunHandle fields, 24 tests (@claude, 2026-04-04, branch: feat/issue-6/processmonitor-localrunner-worker, session: 20260404-043408-phase-5-2b-processmonitor-localrunner-wo)
- [#86] Phase 5.0b: LazyList + CodeBlock auto-unpack -- memory-safe lazy item loading, CodeBlock unpack/repack layer (@claude, 2026-04-04, branch: feat/issue-86/lazy-list-codeblock, session: 20260404-041450-phase-5-0b-lazylist-codeblock-auto-unpac)
- [#88] Phase 5.6: Collection operation blocks -- MergeCollection, SplitCollection, FilterCollection, SliceCollection (ADR-021) (@claude, 2026-04-04, branch: feat/issue-88/collection-operation-blocks, session: 20260404-041611-phase-5-6-collection-operation-blocks-ad)
- [#90] Phase 5.2a: PlatformOps + ProcessHandle + ProcessRegistry — ADR-017/019 cross-platform process lifecycle, PosixOps/WindowsOps, spawn_block_process factory, 29 tests (@claude, 2026-04-04, branch: feat/issue-90/platform-process-handle, session: 20260404-042159-phase-5-2a-platformops-processhandle-pro)
- [#91] Phase 5.3: ResourceManager with psutil watermark — ADR-022 OS-level memory monitoring, ADR-018 EventBus auto-release, GPU/CPU slot counting, 32 tests (@claude, 2026-04-04, branch: feat/issue-91/resource-management, session: 20260404-042212-phase-5-3-resource-management-adr-022)
- [#85] Phase 5.5: EventBus publish/subscribe dispatcher — ADR-018 runtime backbone with sync/async callback support, error isolation, 12 tests (@claude, 2026-04-04, branch: feat/issue-85/event-bus, session: 20260404-041317-phase-5-5-event-bus-implementation-adr-0)
- [#83] Phase 5.0a: Collection class + Block base utilities — ADR-020 Collection transport, pack/unpack/map_items/parallel_map, ProcessBlock Tier 1 process_item, port Collection transparency (@claude, 2026-04-04, branch: feat/issue-83/collection-block-utilities, session: 20260404-040318-phase-5-0a-collection-class-block-base-u)
- [#74] ADR-017-022 backbone scaffolding — TODO-annotated code stubs for subprocess isolation, event-driven scheduler, ProcessHandle, Collection transport, Collection operation blocks, psutil memory monitoring (@claude, 2026-04-04, branch: refactor/issue-74/adr-017-022-backbone, session: 20260404-024138-adr-017-022-backbone-scaffolding)
- [#42] Wave 3 tests: import coverage for Phase 5+ modules and extended block tests (@claude, 2026-04-03, branch: test/issue-42/wave3-import-coverage, session: 20260403-192429-wave-3-tests-import-coverage-and-extende)
- [#38] Wave 1 tests: 7 new test files for core and block coverage (~65% -> ~76%) (@claude, 2026-04-03, branch: test/issue-38/wave1-core-block-coverage, session: 20260403-191229-wave-1-tests-achieve-85-coverage-for-pha)
- [#35] Add AI PR review workflow with Codex agent (@claude, 2026-04-03, branch: feat/ai-pr-review, session: 20260403-162720-add-ai-pr-review-workflow-with-codex-age)
- [#32] Add code audit agent prompt for automated PR review (@claude, 2026-04-03, branch: feat/issue-32/code-audit-agent-prompt, session: 20260403-160517-add-code-audit-agent-prompt-for-automate)

- Phase 4 — Block system implementation:
  - Port system: type matching (isinstance-based, inheritance-aware), constraint validation, connection validation (source→target compatibility)
  - Block lifecycle: validate() with port type/constraint checking, postprocess() pass-through, state machine with transition()
  - IOBlock: read/write via AdapterRegistry with direction config
  - ProcessBlock: base with algorithm ClassVar; MergeBlock (Arrow concat), SplitBlock (head/ratio/filter)
  - CodeBlock: inline and script modes with MEMORY/PROXY/CHUNKED delivery
  - PythonRunner: exec() for inline, importlib for script with mtime-based hot-reload safety
  - introspect_script(): AST-based run() signature and configure() schema extraction
  - R/Julia runners: helpful NotImplementedError stubs
  - AppBlock: full lifecycle with RUNNING→PAUSED→RUNNING→DONE state transitions
  - FileExchangeBridge: prepare (JSON manifest), launch (subprocess), watch, collect
  - FileWatcher: polling-based output detection with timeout and glob patterns
  - SubWorkflowBlock: input/output mapping with sequential executor stub (real DAG scheduler in Phase 5)
  - BlockRegistry: Tier 1 (drop-in .py scan) + Tier 2 (entry_points) discovery, instantiate(), hot_reload()
  - AdapterRegistry: extension→adapter mapping with register_defaults() and entry_point scan
  - RunnerRegistry: language→runner mapping with register_defaults()
  - Format adapters: CSV (PyArrow), Parquet (PyArrow), TIFF (tifffile), generic binary (Artifact)
  - Stub adapters: mzXML, H5AD, FCS with NotImplementedError
  - 69 new tests across 7 test files covering ports, IO, process, code, app, registry, and subworkflow blocks
- CI: test coverage enforcement at 65% minimum via pytest-cov (will increase to 85% as test suite grows)
- CI: PR gate check requiring tests/ updates when src/ changes

- Phase 3 — Core data layer implementation:
  - DataObject metadata handling, TypeSignature auto-generation from class MRO
  - TypeSignature.matches() for inheritance-aware type compatibility
  - CompositeData slot management with type validation (get, set, slot_types)
  - TypeRegistry with register, resolve, scan_builtins, load_class, is_instance
  - ZarrBackend — write/read numpy arrays via Zarr, chunk-aware slicing
  - ArrowBackend — write/read PyArrow Tables via Parquet, column selection
  - FilesystemBackend — text and binary file storage with byte-range slicing
  - CompositeStore — directory-of-slots with manifest.json
  - ViewProxy — lazy loading with shape/axes metadata, size warnings (>2 GB)
  - LineageStore — SQLite-backed lineage records with ancestor tracing
  - EnvironmentSnapshot.capture() — Python version and key package versions
  - ProvenanceGraph — in-memory ancestry, descendant, diff, and audit queries
  - broadcast_apply() — named-axis-aware broadcasting utility
  - iter_axis_slices() — axis-aware slice generator for Array types
  - content_hash() — xxhash-based content hashing for lineage
  - 102 tests covering types, composites, storage round-trips, proxy lazy loading, lineage, and broadcast
- [#9] Scaffold repository structure and implement interface skeleton (Phases 0-2)
- [#7] Add mandatory branch and PR commit rules to CLAUDE.md
- Workflow gate system (`.workflow/gate.py`) for enforced development pipeline
- SpecKit integration (`.specify/`) for feature-level design pipeline
- GitHub Actions CI: lint, typecheck, test matrix, import contracts
- GitHub Actions workflow gate check for PR compliance
- Issue templates (feature, bug, refactor, architecture)
- PR template with checklist
- CLAUDE.md governance: branch discipline, merge conflict handling, branch cleanup rules
- CLAUDE.md Appendix C: bug fix and issue resolution workflow (ADR, spec, SpecKit, branch, PR/CI)
- Architecture documentation (`docs/architecture/`)
- ADR documentation (`docs/adr/`)

### Changed

- [#1] Bump actions/checkout from 4 to 6
- [#2] Bump astral-sh/setup-uv from 5 to 7
- [#3] Bump github/codeql-action from 3 to 4
- [#4] Bump actions/setup-python from 5 to 6

### Fixed

- [#70] AppBlock command injection guard + FileWatcher TOCTOU stability check (@claude, 2026-04-05, branch: fix/issue-70/appblock-security, session: 20260405-004432-fix-p1-appblock-command-injection-toctou)
- [#129] Fix port_accepts_type() Collection transparency bug in Block.validate() — pass Collection instance directly instead of type(value) (@claude, 2026-04-05, branch: fix/issue-129/port-accepts-type-collection, session: 20260405-004832-issue-129-fix-port-accepts-type-collecti)
- [#53] Normalize StorageReference.path to POSIX forward-slash format (@claude, 2026-04-05, branch: fix/issue-53/storage-ref-posix-paths, session: 20260405-004909-issue-53-storagereference-posix-path-nor)
- [#130] Filter original namespace keys and imported modules from PythonRunner.execute_inline() output (@claude, 2026-04-05, branch: fix/issue-130/python-runner-namespace-filter, session: 20260405-004852-issue-130-pythonrunner-execute-inline-fi)
- [#31] Deduplicate records in ProvenanceGraph descendants/ancestors traversals (@claude, 2026-04-04, branch: fix/issue-31/provenance-dedup, session: 20260404-034230-fix-provenancegraph-dedup-in-descendants)
- [#28] Make CompositeStore.slice() and iter_chunks() lazy -- load only requested slots (@claude, 2026-04-04, branch: fix/issue-28/composite-store-lazy, session: 20260404-034336-fix-compositestore-slice-and-iter-chunks)
- [#26] Persist axis metadata in ZarrBackend write/read for round-trip fidelity (@claude, 2026-04-04, branch: fix/issue-26/zarr-axes-metadata, session: 20260404-034314-fix-zarrbackend-to-persist-axis-metadata)
- [#27] Default LineageStore to persistent file path instead of in-memory (@claude, 2026-04-04, branch: fix/issue-27/lineage-default-path, session: 20260404-034315-fix-lineagestore-default-to-persistent-f)
- [#24] Enforce CompositeData slot contracts in TypeSignature matching and constructor (@claude, 2026-04-04, branch: fix/issue-24/composite-slot-contracts, session: 20260404-034408-fix-compositedata-slot-contracts-enforce)
- [#30] Include ndarray shape/dtype in content_hash to prevent lineage collisions (@claude, 2026-04-04, branch: fix/issue-30/content-hash-shape-dtype, session: 20260404-034204-fix-content-hash-to-include-ndarray-shap)
- [#16] Align BlockSpec and TypeRegistry with ADR-009 descriptor pattern
- [#14] Promote CHANGELOG CI check from warning to error
- CI: handle empty repo gracefully in workflows
- CI: disable `set -e` for pytest to capture exit code 5

### Removed
