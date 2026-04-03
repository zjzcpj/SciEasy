# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

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
- Architecture documentation (`docs/architecture/`)
- ADR documentation (`docs/adr/`)

### Changed

- [#1] Bump actions/checkout from 4 to 6
- [#2] Bump astral-sh/setup-uv from 5 to 7
- [#3] Bump github/codeql-action from 3 to 4
- [#4] Bump actions/setup-python from 5 to 6

### Fixed

- [#16] Align BlockSpec and TypeRegistry with ADR-009 descriptor pattern
- [#14] Promote CHANGELOG CI check from warning to error
- CI: handle empty repo gracefully in workflows
- CI: disable `set -e` for pytest to capture exit code 5

### Removed
