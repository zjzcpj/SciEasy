# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Removed

- [#59] Remove InputDelivery enum — MEMORY-only delivery via ADR-020 Collection auto-unpack (@claude, 2026-04-04, branch: fix/batch-1/issues-59-57-58-48, session: 20260404-192842-batch-1-remove-inputdelivery-postprocess)

### Changed

- [#123] Update Block.run() signature from dict[str, Any] to dict[str, Collection] across base + all subclasses, add architecture test (@claude, 2026-04-05, branch: fix/issue-123/block-run-collection-signature, session: 20260405-002441-issue-123-block-run-signature-dict-str-a)
- [#57] Update Block.postprocess() type annotation to dict[str, Collection] (@claude, 2026-04-04, branch: fix/batch-1/issues-59-57-58-48, session: 20260404-192842-batch-1-remove-inputdelivery-postprocess)
- [#58] Document that port constraint functions receive Collection objects (@claude, 2026-04-04, branch: fix/batch-1/issues-59-57-58-48, session: 20260404-192842-batch-1-remove-inputdelivery-postprocess)

### Added

- [#60] SubWorkflowBlock nested subprocess cleanup — SIGTERM callback and Windows Job Object (@claude, 2026-04-05, branch: feat/issue-60/subworkflow-cleanup, session: 20260405-010910-feat-subworkflowblock-nested-subprocess)
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
