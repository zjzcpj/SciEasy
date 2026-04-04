# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

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

- [#28] Make CompositeStore.slice() and iter_chunks() lazy -- load only requested slots (@claude, 2026-04-04, branch: fix/issue-28/composite-store-lazy, session: 20260404-034336-fix-compositestore-slice-and-iter-chunks)
- [#27] Default LineageStore to persistent file path instead of in-memory (@claude, 2026-04-04, branch: fix/issue-27/lineage-default-path, session: 20260404-034315-fix-lineagestore-default-to-persistent-f)
- [#24] Enforce CompositeData slot contracts in TypeSignature matching and constructor (@claude, 2026-04-04, branch: fix/issue-24/composite-slot-contracts, session: 20260404-034408-fix-compositedata-slot-contracts-enforce)
- [#30] Include ndarray shape/dtype in content_hash to prevent lineage collisions (@claude, 2026-04-04, branch: fix/issue-30/content-hash-shape-dtype, session: 20260404-034204-fix-content-hash-to-include-ndarray-shap)
- [#16] Align BlockSpec and TypeRegistry with ADR-009 descriptor pattern
- [#14] Promote CHANGELOG CI check from warning to error
- CI: handle empty repo gracefully in workflows
- CI: disable `set -e` for pytest to capture exit code 5

### Removed
