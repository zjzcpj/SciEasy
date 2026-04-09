# SciEasy Audit Report (English)

Date: 2026-04-08
Repository: `C:\Users\jiazh\Desktop\workspace\SciEasy`
Audited commit: `e14dcb5` (`fix(#401): bump core package version to 0.2.1 (#402)`)

## Executive Summary

This audit found a consistent pattern: several roadmap/spec items were merged as skeletons or partial implementations, but the repository now exposes them as if they were finished. The highest-risk gaps are:

1. Stage 10.1 palette/API grouping is still a Part-1 skeleton, while the codebase and docs already talk about the finished package/category model.
2. `BlockTestHarness` does not implement the ADR-026 / issue-#215 contract that the docs advertise.
3. `scieasy-blocks-srs` is not discoverable as a plugin package.
4. `scieasy-blocks-lcms` is not discoverable as a plugin package, and its capstone packaging/integration tasks are still deferred on `main`.
5. The Phase 11 “full plugin set” test strategy is not executable from the repo root.
6. The architecture document promises a `docs/block-development/` documentation set that does not exist.

I did not modify any existing code or documentation. The only files added are this report and the Chinese translation.

## Methodology

- Read the architecture/spec/SDK docs in `README.md`, `docs/architecture/ARCHITECTURE.md`, `docs/guides/block-sdk.md`, and Phase 11 specs.
- Inspected the relevant implementation in `src/`, `frontend/`, and `packages/`.
- Ran targeted verification:
  - `pytest --no-cov tests/testing/test_harness.py tests/api/test_blocks.py tests/blocks/test_registry.py tests/architecture -q`
  - `pytest --no-cov packages/scieasy-blocks-imaging/tests/test_packaging.py packages/scieasy-blocks-srs/tests/test_types.py packages/scieasy-blocks-lcms/tests/test_types.py -q`
- Used `git blame` / `git log` to trace introducing commits and PRs.
- Queried GitHub issues for existing tracking items.

## Findings Overview

| ID | Severity | Area | Summary | Existing issue? |
|---|---|---|---|---|
| F1 | High | Docs / API / Frontend | Stage 10.1 palette grouping is still a skeleton but the repo exposes it as a finished contract | Yes: `#250`, `#251` |
| F2 | High | SDK / Testing | `BlockTestHarness` does not meet the documented ADR-026 contract | Partially: original feature issue `#215`; no separate bug issue found |
| F3 | High | SRS plugin | `scieasy-blocks-srs` lacks entry-point wiring and `get_blocks()` export, so discovery cannot succeed | No matching bug issue found |
| F4 | High | LC-MS plugin | `scieasy-blocks-lcms` still lacks entry-point wiring, `get_blocks()`, and the T-LCMS-020/021 capstone deliverables | Related deferred-work issue `#345`; no bug issue found |
| F5 | Medium | Test architecture | Phase 11 full-plugin test plan is not wired into the repo root and fails from the root workspace | No matching issue found |
| F6 | Medium | Documentation completeness | `ARCHITECTURE.md` promises a `docs/block-development/` set that does not exist | No matching issue found |

## Detailed Findings

### F1. Stage 10.1 palette/API grouping is still a skeleton, but the repository already documents the finished behavior

Severity: High
Category: architecture-doc consistency, incomplete refactor, code/design mismatch

Requirement / design lines:

- `docs/design/stage-10-1-palette.md:29-35` defines the required Stage 10.1 behavior: explicit category override, `source` exposure, Tier 1 “Custom”, and package/category/block tree rendering.
- `docs/design/stage-10-1-palette.md:44-49` says Part 2 must implement the real `_infer_category`, API exposure, and `BlockPalette.tsx` rewrite.
- `docs/guides/block-sdk.md:244-270` tells block authors that the GUI palette is grouped by package and category.

Actual implementation lines:

- `src/scieasy/api/schemas.py:95-101` defines `source` and `package_name`.
- `src/scieasy/api/routes/blocks.py:42-58` still contains a TODO and does not populate those fields in `_summary()`.
- `src/scieasy/blocks/registry.py:555-583` still ignores the `category` ClassVar override and still emits legacy source values elsewhere (`tier1`, `entry_point`).
- `frontend/src/components/BlockPalette.tsx:5-27` explicitly says the 3-level tree is TODO.
- `frontend/src/components/BlockPalette.tsx:39`, `frontend/src/components/BlockPalette.tsx:82-92`, and `frontend/src/components/BlockPalette.tsx:146-149` show the current implementation still groups only by flat category.
- `tests/api/test_blocks.py:89-105` and `tests/blocks/test_registry.py:439-480` keep the Stage 10.1 acceptance tests skipped.

Why this violates the design:

- The design doc and SDK guide describe a package-aware palette contract, but the backend never exposes the required metadata and the frontend still renders a flat category list.
- This is not just “future work”: the schema fields exist, the tests exist, and the code comments explicitly say the implementation was deferred.

User-facing impact:

- Plugin packages cannot be grouped in the UI as documented.
- API consumers receive empty `source` / `package_name` fields despite the model claiming those fields exist.
- The documentation overstates actual product behavior.

Introducing PR source:

- PR `#159` introduced the flat Phase 7-8 editor/API baseline.
- PR `#251` (`6441de9d`, “Stage 10.1 Part 1 — design doc and skeleton”) explicitly merged only the skeleton/TODO version and left the real implementation for an unmerged Part 2.

Existing issue status:

- Already listed in issue `#250` (Stage 10.1 tracking) and issue `#251` (Part 1 skeleton).

Recommendation:

- Either finish Stage 10.1 immediately, or downgrade the user-facing docs so they describe the current flat-category behavior instead of the intended package/category tree.

### F2. `BlockTestHarness` does not implement the ADR-026 / issue-#215 contract advertised in the docs

Severity: High
Category: code/design mismatch, implementation insufficiency

Requirement / design lines:

- Issue `#215` requires:
  - `run(inputs, params) -> dict`
  - raw-data wrapping into `DataObject` / `Collection`
  - `BlockConfig` construction
  - output materialization helpers
- `docs/architecture/ARCHITECTURE.md:2653-2678` documents `BlockTestHarness.run(...)` and says it wraps raw data, creates a temp project structure, validates outputs, and materializes them.
- `docs/guides/block-sdk.md:1290-1310` repeats the same `harness.run(...)` contract and the same responsibilities.

Actual implementation lines:

- `src/scieasy/testing/harness.py:48-120` only performs shallow class/port/name checks.
- `src/scieasy/testing/harness.py:154-220` validates entry-point callable structure, but not the richer block execution contract described in the docs.
- `src/scieasy/testing/harness.py:226-267` only implements `smoke_test(...)`; there is no `run(...)` method at all.
- `src/scieasy/testing/harness.py:261-267` simply instantiates the block and forwards `inputs` directly to `instance.run(inputs, config)`; there is no raw-data wrapping, no temp-project creation, no output-type validation, and no materialization step.

Why this violates the design:

- The documented public API is `run(...)`; the implementation only provides `smoke_test(...)`.
- The documented responsibilities are mostly absent.
- This means external block authors reading the SDK guide will write tests against an API that does not exist.

User-facing impact:

- The SDK documentation is misleading.
- The public testing helper is substantially weaker than the architecture and issue contract claim.
- External block packages can pass “smoke tests” without any of the conversion/materialization guarantees the docs promise.

Introducing PR source:

- PR `#215` (`2f567799`, “add BlockTestHarness”) introduced the minimal implementation.
- PR `#217` (`056dda76`, “add comprehensive block SDK developer guide”) and later architecture doc updates documented a richer API than the code provides.

Existing issue status:

- The intended contract is listed in issue `#215`.
- I did not find a separate bug/regression issue stating that the shipped implementation still falls short of that contract.

Recommendation:

- Align the code and docs: either implement the missing `run()` / wrapping / materialization behavior, or rewrite the docs so they accurately describe `smoke_test(...)` as the real surface.

### F3. `scieasy-blocks-srs` is not discoverable as a plugin package

Severity: High
Category: Phase 11 incomplete implementation, packaging defect

Requirement / design lines:

- `docs/specs/phase11-srs-block-spec.md:516-519` requires SRS `pyproject.toml` to declare:
  - `scieasy.blocks`: `srs = "scieasy_blocks_srs:get_blocks"`
  - `scieasy.types`: `srs = "scieasy_blocks_srs.types:get_types"`
- `docs/specs/phase11-srs-block-spec.md:527-530` requires top-level `get_blocks()` / `get_types()`.
- `docs/specs/phase11-srs-block-spec.md:1600-1659` defines T-SRS-013: `get_blocks()` must return all 11 blocks, `get_types()` must return `[SRSImage]`, registry scans must find them, and entry-point tests must pass.
- `docs/specs/phase11-srs-block-spec.md:1675-1778` makes T-SRS-014 depend on that wiring for the cross-plugin E2E path.

Actual implementation lines:

- `packages/scieasy-blocks-srs/pyproject.toml:5-23` contains no `[project.entry-points."scieasy.blocks"]` or `[project.entry-points."scieasy.types"]` section at all.
- `packages/scieasy-blocks-srs/src/scieasy_blocks_srs/__init__.py:5-8` re-exports only four preprocess blocks and `SRSImage`; it defines no `get_blocks()` function.
- `packages/scieasy-blocks-srs/src/scieasy_blocks_srs/types.py:98-104` does provide `get_types()`, but without the pyproject entry-point registration it is not discoverable through the packaging contract.
- `src/scieasy/blocks/registry.py:415-418` shows the monorepo fallback only recognizes `get_block_package()` or `get_blocks()`. The SRS package provides neither, so even the development fallback cannot discover its blocks.

Why this violates the design:

- T-SRS-013 is explicitly the plugin-registration capstone. On `main`, it has not been completed.
- Because `get_blocks()` is missing, neither the standard entry-point scan nor the monorepo fallback can register SRS blocks.

User-facing impact:

- Installing the SRS package does not make its blocks discoverable through the declared plugin mechanism.
- The cross-plugin E2E design in T-SRS-014 cannot succeed through normal registry discovery.

Introducing PR source:

- PR `#309` (`6a068f85`) created the skeleton pyproject without entry points.
- PR `#367` (`2ccec1d8`) added `SRSImage`.
- PR `#380` (`26aed247`) added preprocess exports, but still did not complete the packaging/registration step required by T-SRS-013.

Existing issue status:

- I found the SRS spec issue `#299`, which documents the intended behavior, but not a bug issue stating that `main` still lacks T-SRS-013.
- Related scaffold issue `#308` explains that entry points were intentionally absent in the skeleton, but no matching follow-up bug issue appears in search.

Recommendation:

- Implement T-SRS-013 before treating the SRS plugin as delivered: add entry points, add `get_blocks()`, add entry-point tests, and then wire the T-SRS-014 integration test.

### F4. `scieasy-blocks-lcms` still lacks entry-point wiring, `get_blocks()`, and the T-LCMS-020/021 capstone deliverables

Severity: High
Category: Phase 11 incomplete implementation, packaging defect

Requirement / design lines:

- `docs/specs/phase11-lcms-block-spec.md:806-810` requires LC-MS entry points:
  - `scieasy.blocks`: `lcms = "scieasy_blocks_lcms:get_blocks"`
  - `scieasy.types`: `lcms = "scieasy_blocks_lcms.types:get_types"`
- `docs/specs/phase11-lcms-block-spec.md:3326-3473` defines T-LCMS-020: finalize `get_blocks()`, verify entry points, and pass 8 smoke tests.
- `docs/specs/phase11-lcms-block-spec.md:3490-3536` defines T-LCMS-021: add the isotope-tracing integration fixtures and test.
- `docs/specs/phase11-implementation-standards.md:3172-3173` and `docs/specs/phase11-lcms-block-spec.md:3544` make T-LCMS-021 the final dependency gate.

Actual implementation lines:

- `packages/scieasy-blocks-lcms/pyproject.toml:5-15` has no entry-point sections.
- `packages/scieasy-blocks-lcms/src/scieasy_blocks_lcms/__init__.py:10-13` explicitly says entry-point registration is “the responsibility of the T-LCMS-021 impl agent”.
- `packages/scieasy-blocks-lcms/src/scieasy_blocks_lcms/__init__.py:24-30` exports only types plus `get_types`; there is no `get_blocks()`.
- There is no `packages/scieasy-blocks-lcms/tests/integration/` tree in the repo file inventory, even though T-LCMS-021 requires `tests/integration/fixtures/...` and `tests/integration/test_tracing_workflow.py`.

Why this violates the design:

- The spec says T-LCMS-020 and T-LCMS-021 are required capstones after the LC-MS implementation tickets.
- `main` still contains the deferred/skeleton state rather than the completed packaging/discovery/test state.

User-facing impact:

- The LC-MS package cannot be discovered by entry-point-based plugin loading.
- The promised isotope-tracing end-to-end validation is absent.
- The package still reads like a skeleton, not a completed Phase 11 plugin.

Introducing PR source:

- PR `#309` (`6a068f85`) created the minimal skeleton pyproject.
- PR `#348` (`0f9e6fdc`) explicitly deferred T-LCMS-020/021 in the LC-MS skeleton issue/commit.
- No later merged PR completes those capstone tasks on `main`.

Existing issue status:

- Issue `#345` explicitly says T-LCMS-020/021 were deferred.
- I did not find a separate issue tracking that these deferred tasks are still missing on `main`.

Recommendation:

- Treat LC-MS as incomplete until T-LCMS-020 and T-LCMS-021 are actually merged: add `get_blocks()`, add entry points, add smoke tests, and add the synthetic-fixture integration workflow.

### F5. The Phase 11 “full plugin set” test plan is not executable from the repository root

Severity: Medium
Category: test architecture, incomplete integration

Requirement / design lines:

- `docs/specs/phase11-implementation-standards.md:3271-3279` requires, after T-LCMS-021, that `pytest -x --no-cov` across the entire monorepo pass.
- `docs/specs/phase11-lcms-block-spec.md:234-238` and `docs/specs/phase11-lcms-block-spec.md:283-287` require plugin-local pytest to pass as part of ticket acceptance.
- `docs/specs/phase11-lcms-block-spec.md:3536` requires the LC-MS integration test to pass under `pytest packages/scieasy-blocks-lcms/tests/integration/`.

Actual implementation lines:

- `pyproject.toml:127-129` sets `testpaths = ["tests"]`, so the default root pytest run ignores all `packages/*/tests`.
- `packages/scieasy-blocks-imaging/tests/conftest.py:1-20`, `packages/scieasy-blocks-srs/tests/conftest.py:1-30`, and `packages/scieasy-blocks-lcms/tests/conftest.py:1-29` each create plugin-local `tests.conftest` modules.

Observed verification failure:

- Running
  `pytest --no-cov packages/scieasy-blocks-imaging/tests/test_packaging.py packages/scieasy-blocks-srs/tests/test_types.py packages/scieasy-blocks-lcms/tests/test_types.py -q`
  from the repo root failed with:
  `ImportPathMismatchError: ('tests.conftest', ...imaging..., ...srs...)`

Why this violates the design:

- The root test configuration does not include the plugin packages.
- Attempting to compensate by invoking multiple package test trees from the repo root triggers Python package-name collisions.
- Therefore the “full monorepo” test strategy described in the standards is not currently runnable from the main workspace.

User-facing impact:

- CI/root verification can miss plugin regressions.
- The repository does not have a single authoritative test entry point for the full Phase 11 plugin set.

Introducing PR source:

- The root pytest scoping traces back to the core repo configuration (`pyproject.toml`).
- The package-local test scaffolds that create the conflicting `tests.conftest` layout were added in the Phase 11 scaffold/implementation PRs, starting with PR `#309` and extended by later plugin PRs.

Existing issue status:

- I did not find a matching GitHub issue for this repo-root test topology problem.

Recommendation:

- Decide on one supported strategy and enforce it:
  - either include package tests in the root pytest configuration with unique package names,
  - or require per-package isolated test runs and document that the root suite is intentionally core-only.

### F6. `ARCHITECTURE.md` promises a `docs/block-development/` document set that does not exist

Severity: Medium
Category: documentation completeness

Requirement / design lines:

- `docs/architecture/ARCHITECTURE.md:2682-2695` promises a structured `docs/block-development/` set containing `quickstart.md`, `architecture-for-block-devs.md`, `block-contract.md`, `data-types.md`, `custom-types.md`, `memory-safety.md`, `collection-guide.md`, `testing.md`, `publishing.md`, and `examples/`.

Actual repository state:

- The repository contains `docs/guides/block-sdk.md`, but no `docs/block-development/` directory is present in the tracked file inventory.

Why this violates the design:

- The architecture document points readers to a documentation subtree that does not exist.
- This is a direct documentation completeness problem and weakens the “Block SDK” onboarding story.

User-facing impact:

- New plugin authors cannot follow the architecture doc references literally.
- The architecture document overstates the completeness of the developer-doc set.

Introducing PR source:

- This promise appears in the architecture-doc update stream; the nearest relevant merged doc update is PR `#330` (`81c821e`, T-TRK-010 architecture doc updates).

Existing issue status:

- I did not find a matching issue specifically tracking the missing `docs/block-development/` subtree.

Recommendation:

- Either add the referenced directory and documents, or rewrite `ARCHITECTURE.md` to point at the real `docs/guides/block-sdk.md` surface.

## Verification Notes

- Targeted core tests passed with `--no-cov`:
  - `tests/testing/test_harness.py`
  - `tests/api/test_blocks.py`
  - `tests/blocks/test_registry.py`
  - `tests/architecture`
- Those runs also confirmed the Stage 10.1 tests remain skipped, which is itself part of Finding F1.
- A normal subset run without `--no-cov` hit the repository-wide `--cov-fail-under=85` gate, so I used `--no-cov` for focused verification.

## Recommended Next Actions

1. Finish or revert Stage 10.1 Part 2 so the API, frontend, tests, and docs all describe the same palette contract.
2. Bring `BlockTestHarness` into conformance with ADR-026 / issue `#215`, or downgrade the docs immediately.
3. Complete SRS T-SRS-013/T-SRS-014 and LC-MS T-LCMS-020/T-LCMS-021 before treating those plugins as shipped.
4. Establish one supported full-repo plugin test strategy and wire it into CI.
5. Remove architecture-doc promises that do not correspond to real files.
