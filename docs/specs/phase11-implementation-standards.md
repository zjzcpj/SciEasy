---
title: Phase 11 implementation standards (task decomposition)
status: in progress
issue: 306 (closes #305)
date: 2026-04-07
---

# Phase 11 implementation standards

## 1. Purpose

This document is the **master task-decomposition standard** for the
Phase 11 plugin cascade. It is the single source of truth that:

- The **skeleton agent** reads to know which files to delete, which
  to create as placeholders, and which directory layout to scaffold.
- Each **implementation agent** reads to know exactly which files
  it owns, what its acceptance criteria are, and where its work fits
  in the dependency graph.
- Each **code-audit agent** reads to verify that an implementation PR
  did not silently broaden scope, did not weaken type contracts, and
  satisfied the per-ticket acceptance criteria.

This document does **not** replace the source design documents. It is a
*decomposition layer* that breaks the source documents into
implementation-sized work units and records the dependencies between
them. The source documents remain authoritative for the *what* of each
ticket; this document is authoritative for the *how to dispatch* of the
overall cascade.

Source documents (already merged):

- ADR-028 — IOBlock architectural refactor (merged in PR #294).
- ADR-028 Addendum 1 — dynamic port override mechanism + GUI
  consequences.
- ADR-029 (preliminary, draft) — variadic port count, no
  decisions yet, namespace reservation only.
- ``docs/specs/phase11-imaging-block-spec.md`` — 38 T-IMG-* tickets,
  full per-block implementation details.
- ``docs/specs/phase11-srs-block-spec.md`` — 15 T-SRS-* tickets.
- ``docs/specs/phase11-lcms-block-spec.md`` — 21 T-LCMS-* tickets.
- ``CLAUDE.md`` — workflow gate (Appendix A), §6.7 (tests are part of
  the change), §9.2 (no silent scope expansion).

This standards document, like the Phase 10 standards before it, is the
checkpoint between *design* and *implementation*. After this document
merges, the skeleton agent and the per-ticket implementation agents
begin work; before this document merges, no implementation agent may
spawn.

---

## 2. Scope

### In scope

- **Track 1 — core block cleanup and ADR-028 implementation.** 15
  tickets, T-TRK-001 through T-TRK-015. Covers Phase 11 master-plan
  sub-tasks 1a (delete stubs + relocate ``transform.py``), 1b
  (ADR-028 implementation, broken into stacked PRs), 1c (CLAUDE.md +
  ARCHITECTURE.md ManualReview clarification), 1d (FilterCollection
  metadata query), 1e (CodeBlock R runner audit), 1f (CodeBlock
  Python runner audit), 1g (AppBlock functional audit). The
  full per-ticket details for Track 1 live **inside this document**.

- **Track 2 — imaging plugin implementation.** 38 tickets, T-IMG-001
  through T-IMG-038. Per-ticket implementation details live in
  ``docs/specs/phase11-imaging-block-spec.md``. This standards doc
  carries the *cross-ticket* metadata: dependency edges, sprint
  bucket, coupling notes.

- **Track 3 — SRS plugin implementation.** 15 tickets, T-SRS-000
  through T-SRS-014. Per-ticket details in
  ``docs/specs/phase11-srs-block-spec.md``.

- **Track 4 — LC-MS plugin implementation.** 21 tickets, T-LCMS-001
  through T-LCMS-021. Per-ticket details in
  ``docs/specs/phase11-lcms-block-spec.md``.

- **End-to-end test plan.** Two phases — post-Sprint-C (imaging done)
  and post-Sprint-E (full plugin set). Both phases described in §11.

### Out of scope

- **ADR-029 implementation.** The variadic-port-count work is hard
  frozen until ADR-029 is promoted from ``draft — scope pending`` to
  ``proposed``. No ticket in this document touches ``AIBlock`` variadic
  behaviour, ``CodeBlock`` variadic behaviour, or "add port" / "remove
  port" GUI controls. Implementation agents reading this document
  must reject any inline scope expansion in this direction.

- **Plugin packages beyond imaging / SRS / LC-MS.** ``scieasy-blocks-
  singlecell``, ``scieasy-blocks-flow``, and any future plugin remain
  out of scope. The corresponding bundled adapters (``h5ad_adapter``
  and ``fcs_adapter``) are deleted per ADR-028 §D2 but no replacement
  plugin work is scheduled.

- **ARCHITECTURE.md updates beyond Sprint A sub-1b PR-F.** Larger
  architectural docs revisions are deliberately deferred to a follow-up
  sprint. The Sprint A docs PR (T-TRK-010) covers only the §4.2 +
  §5.1 + ``PROJECT_TREE.md`` + ``block-sdk.md`` updates that ADR-028
  requires.

- **Frontend React refactoring beyond ``BlockNode.tsx`` hardcoding
  fixes.** No new React components, no new pages, no styling overhaul.
  Sprint A T-TRK-009 changes exactly the three lines ADR-028
  Addendum 1 §C identifies and adds the ``computeEffectivePorts()``
  helper plus matching TypeScript types — nothing more.

- **Cellpose / Napari / Fiji / R / ElMAVEN / GraphPad version pinning,
  installation scripts, or CI integration.** Marker-protected tests
  (``@pytest.mark.requires_*``) skip when the optional dependency is
  absent. Local-machine integration is the user's responsibility.

---

## 3. Cross-reference table

| Track | Total tickets | Source spec / doc                                  | Sprint(s)             |
|-------|---------------|----------------------------------------------------|-----------------------|
| 1     | 15            | This document §9 (T-TRK-* full format)             | Sprint A + Sprint B  |
| 2     | 38            | ``docs/specs/phase11-imaging-block-spec.md``       | Sprint C             |
| 3     | 15            | ``docs/specs/phase11-srs-block-spec.md``           | Sprint D             |
| 4     | 21            | ``docs/specs/phase11-lcms-block-spec.md``          | Sprint E             |
| **Total** | **89**    |                                                    |                       |

ADR cross-reference:

| Source | Authoritative for                                             |
|--------|---------------------------------------------------------------|
| ADR-028 + Addendum 1 | Track 1 sub-1b (IOBlock + dynamic ports), Block ABC migration, BlockSchemaResponse, frontend BlockNode |
| ADR-028 §D2 | Track 1 sub-1a + Track 2 ``LoadImage`` adapter migration   |
| ADR-027 (Phase 10) | Block class hierarchy, type registry, port system |
| ADR-029 (preliminary) | Documents what is **out of scope** for Phase 11 |

---

## 4. Dependency graph

The cascade is divided into five sprints. Within each sprint, tickets
are grouped by parallelism level: tickets at the same level can run
concurrently; tickets at level N+1 depend on level N completing.

```
Sprint A (Track 1 sub-1a + sub-1b + sub-1c)
├── Level A0 (parallel)
│   ├── T-TRK-001  delete process/contrib/                    [parallel]
│   ├── T-TRK-002  delete process/builtins/register.py        [parallel]
│   ├── T-TRK-003  move transform.py → tests/fixtures/        [parallel]
│   └── T-TRK-011  CLAUDE.md §2.5 + ARCHITECTURE.md MR        [parallel, independent]
├── Level A1 (after A0)
│   └── T-TRK-004  delete adapters/ + adapter_registry +
│                  rewrite io_block.py as ABC                  [bundles old PR-A]
├── Level A2 (after A1)
│   └── T-TRK-006  Block ABC dynamic-port hooks +
│                  BlockSpec + BlockSchemaResponse +
│                  framework read-path migration               [bundles PR-B-1/2/3]
├── Level A3 (after A2, parallel pair)
│   ├── T-TRK-007  LoadData + 6 _load_* private functions
│   └── T-TRK-008  SaveData + 6 _save_* private functions
├── Level A4 (after A3)
│   └── T-TRK-009  Frontend BlockNode.tsx fixes +
│                  computeEffectivePorts + types/api.ts
└── Level A5 (after A4)
    └── T-TRK-010  ARCHITECTURE.md §4.2 + §5.1 +
                   PROJECT_TREE.md + block-sdk.md updates

Sprint B (Track 1 sub-1d + sub-1e + sub-1f + sub-1g, parallel)
├── T-TRK-012  FilterCollection metadata query                [imaging dep]
├── T-TRK-013  CodeBlock R runner audit                        [lcms dep]
├── T-TRK-014  CodeBlock Python runner audit                   [lcms dep]
└── T-TRK-015  AppBlock functional audit                       [imaging dep]

Sprint C (Track 2 imaging) — depends on Sprint A merged, Sprint B in progress
├── Level C0
│   └── T-IMG-001  Types module
├── Level C1 (parallel after C0)
│   ├── T-IMG-002  LoadImage
│   ├── T-IMG-003  SaveImage
│   └── T-IMG-004..T-IMG-022  preprocess/morph/seg/cleanup blocks (parallel)
├── Level C2 (parallel after C1)
│   ├── T-IMG-019  CellposeSegment (FLAGSHIP — depends on T-IMG-001 + T-TRK-015)
│   ├── T-IMG-023..T-IMG-029  tracking/measurement/registration
│   ├── T-IMG-030..T-IMG-033  projection/math/visualization
│   └── T-IMG-034..T-IMG-037  AppBlocks (Fiji/Napari/CellProfiler/QuPath, depend on T-TRK-015)
└── Level C3
    └── T-IMG-038  Plugin packaging (pyproject.toml entry points, smoke test)

Sprint D (Track 3 SRS) — depends on Sprint C T-IMG-001/002/004/019 merged
├── Level D0
│   ├── T-SRS-000  Package skeleton + entry points
│   └── T-SRS-001  SRSImage type + Meta model
├── Level D1 (parallel after D0)
│   ├── T-SRS-002..T-SRS-005  preprocess (Calibrate/Baseline/Denoise/Normalize)
│   ├── T-SRS-006..T-SRS-010  component analysis (VCA/Unmix/PCA/ICA/KMeans)
│   └── T-SRS-011..T-SRS-012  spectral extraction (ExtractSpectrum/BandRatio)
└── Level D2
    ├── T-SRS-013  Plugin entry-point wiring + smoke test
    └── T-SRS-014  E2E integration test (cross-plugin)

Sprint E (Track 4 LC-MS) — depends on Sprint A + sub-1e/1f merged
├── Level E0
│   ├── T-LCMS-001  Plugin scaffold
│   └── T-LCMS-002  Types module
├── Level E1 (parallel after E0)
│   ├── T-LCMS-003..T-LCMS-006  IO loaders (RawFiles/PeakTable/MIDTable/SampleMetadata + SaveTable)
│   └── T-LCMS-007             ElMAVENBlock + AccuCorR (depends on T-TRK-013 R audit)
├── Level E2 (parallel after E1)
│   ├── T-LCMS-008..T-LCMS-012  isotope tracing (5 blocks)
│   ├── T-LCMS-013..T-LCMS-018  metabolomics analysis (6 blocks)
│   └── T-LCMS-019             GraphPadBlock
└── Level E3
    ├── T-LCMS-020  Entry-point registration + plugin smoke test
    └── T-LCMS-021  Isotope tracing integration test
```

---

## 5. Recommended chained PR order

The literal merge order, top to bottom. Items at the same indent level
may run in parallel (separate branches and PRs); items at deeper indent
are stacked on the previous level.

1. **Sprint A — Track 1 sub-1a parallel batch** (4 PRs in parallel,
   independent)
   - T-TRK-001 (delete ``process/contrib/``)
   - T-TRK-002 (delete ``process/builtins/register.py``)
   - T-TRK-003 (move ``transform.py`` → ``tests/fixtures/noop_block.py``)
   - T-TRK-011 (CLAUDE.md §2.5 + ARCHITECTURE.md ManualReview)
2. **Sprint A — Track 1 sub-1b stacked cascade** (sequential, each PR
   stacked on the previous)
   - T-TRK-004 (delete adapters + rewrite ``io_block.py`` as ABC)
   - T-TRK-006 (Block ABC dynamic-port hooks + BlockSpec + framework
     migration)
   - T-TRK-007 + T-TRK-008 in parallel (LoadData / SaveData) — both
     stacked on T-TRK-006
   - T-TRK-009 (frontend BlockNode.tsx + types/api.ts)
   - T-TRK-010 (ARCHITECTURE + PROJECT_TREE + block-sdk docs)
3. **Sprint B — Track 1 sub-1d/1e/1f/1g** (4 PRs in parallel,
   independent of each other but dependent on Sprint A complete)
   - T-TRK-012 (FilterCollection)
   - T-TRK-013 (CodeBlock R audit)
   - T-TRK-014 (CodeBlock Python audit)
   - T-TRK-015 (AppBlock audit)
4. **Sprint C — Track 2 imaging cascade** (T-IMG-001 first, then
   ~36 mostly-parallel block PRs, then T-IMG-038 packaging last)
5. **Sprint D — Track 3 SRS cascade** (T-SRS-000 / T-SRS-001 first,
   then ~13 parallel block PRs, then T-SRS-013 / T-SRS-014 last)
6. **Sprint E — Track 4 LC-MS cascade** (T-LCMS-001 / T-LCMS-002 first,
   then ~17 mostly-parallel block PRs, then T-LCMS-020 / T-LCMS-021
   last)

**Stacked-PR rule**: when a PR is stacked on a not-yet-merged base, set
``base`` in ``gh pr create`` to the previous PR's branch name. After
the previous PR merges, the next stacked PR's base auto-retargets to
``main``. Per Phase 10 cascade lessons, **the first destructive PR is
the highest-risk point** because the full CI pipeline only runs after
retarget to ``main`` (the stacked branch's CI runs against the
unstable base). For this cascade the first destructive PR is
**T-TRK-004** (delete adapters + rewrite ``io_block.py``).

---

## 6. Universal rules for all 89 implementation agents

These rules apply to **every** ticket in this document. Failure to
follow them is a workflow gate violation per ``CLAUDE.md`` §6.7 and
§9.2.

1. **Workflow gate is mandatory.** Every ticket follows the full
   6-stage workflow gate per ``CLAUDE.md`` Appendix A. No exceptions
   for "small" tickets, including pure file-deletion PRs and
   doc-only PRs. Each stage must show ``[DONE]`` in
   ``python .workflow/gate.py status <task_id>`` before the next stage
   begins.

2. **Branch naming.**
   - Track 1: ``feat/issue-N/T-TRK-NNN-short-name`` (replace ``feat``
     with ``fix`` or ``docs`` or ``refactor`` as appropriate). Example:
     ``refactor/issue-310/T-TRK-004-delete-adapters-rewrite-ioblock``.
   - Track 2: ``feat/issue-N/T-IMG-NNN-short-name``.
   - Track 3: ``feat/issue-N/T-SRS-NNN-short-name``.
   - Track 4: ``feat/issue-N/T-LCMS-NNN-short-name``.

3. **Stacked-PR base.** Each PR's base branch is the previous merged
   PR's branch (so the diffs compose cleanly). If the previous PR has
   already merged into ``main``, base off ``main`` directly. Mark
   stacked PRs with the previous PR number in the description.

4. **Out-of-scope changes are forbidden.** The PR's diff must contain
   only the files listed in the ticket's "Files to be created", "Files
   to be modified", "New tests", and "Existing tests to update"
   sections. Any other modified file is a scope violation per
   ``CLAUDE.md`` §6.7 and §9.2.

5. **Every check must be green before review.**
   - ``pytest -x --no-cov`` passes locally.
   - ``ruff check src/ tests/ packages/`` clean.
   - ``ruff format --check src/ tests/ packages/`` clean.
   - ``mypy src/scieasy --ignore-missing-imports`` clean for core
     changes; ``mypy packages/scieasy-blocks-<plugin>/src
     --ignore-missing-imports`` clean for plugin changes.
   - ``python -m importlinter --config pyproject.toml`` clean (the
     ``Core must not depend on blocks/engine/api/ai/workflow``
     contract is load-bearing for Track 1 sub-1b).

6. **CHANGELOG.md** must be updated under ``[Unreleased]`` in the
   appropriate section (``Added`` / ``Changed`` / ``Fixed`` /
   ``Removed``) with full attribution per ``CLAUDE.md`` Appendix A
   Stage 6:
   ``[#N] Description (@claude, YYYY-MM-DD, branch: ..., session: ...)``.

7. **PR body must reference**:
   - The ADR section the PR implements
     (e.g. "Implements ADR-028 §D2").
   - The ticket ID from this standards doc
     (e.g. "Per ``docs/specs/phase11-implementation-standards.md``
     T-TRK-006").
   - For Tracks 2/3/4, the source-spec ticket ID (e.g. "Per
     ``docs/specs/phase11-imaging-block-spec.md`` T-IMG-019").
   - The previous PR in the stack (if any).
   - A reproduction of the ticket's acceptance criteria as a checklist
     with each box ticked when satisfied.

8. **No silent scope expansion.** If implementing a ticket reveals a
   pre-existing bug or design ambiguity, open a *new issue* describing
   it. Do not fix it inline. Per ``CLAUDE.md`` §9.2 and Appendix C
   Step 3.

9. **Scope-violation red flags (the audit-agent checklist).** Audit
   agents will reject any PR that exhibits any of the following
   patterns. Implementation agents must therefore avoid them:

   1. **Type relaxation** — weakening a type annotation from specific
      to general (``list[InputPort]`` → ``Any``, ``dict[str, int]`` →
      ``dict``, ``Image`` → ``DataObject``,
      ``InputPort | None`` → ``InputPort | Any``).
   2. **Assertion removal** — deleting or weakening a runtime
      assertion or validation that was in the original code.
   3. **Test expectation rewrite** — changing a test expectation
      instead of fixing the code under test.
   4. **Scope argument shrinkage** — narrowing a function's scope to
      avoid implementing the full contract (the spec says "handle
      Array, DataFrame, Series" but the PR only handles Array).
   5. **Silent exception swallowing** — adding ``except Exception:
      pass`` or ``except Exception: return None`` where the original
      raised.
   6. **Default fallback abuse** — using ``getattr(x, 'foo', None)``
      where the original did ``x.foo`` and the attribute is
      load-bearing.
   7. **Commenting out code** — commenting out a code path instead of
      fixing it.
   8. **"TODO: fix in follow-up" placeholders** for things that were
      supposed to be fixed *now*.

10. **Doc-external changes are restricted.** The user has granted
    permission for doc-external changes when tests reveal missing
    things, but only when scoped to the feature being tested. Any such
    change must be called out explicitly in the PR body and must not
    expand the ticket's diff beyond what is strictly necessary.

11. **Branch base.** Each ticket starts from ``origin/main`` (or the
    previous merged stacked branch). Never branch from ``main-local``
    once Phase 11 implementation begins; ``main-local`` is frozen per
    the master plan §10.

12. **One ticket = one PR.** The Phase 11 master plan §4.3 explicitly
    states *"default: one agent = one ticket = one PR"*. Bundling is
    only permitted when the change spans files that **only make sense
    together** (see §8 Q3 below for the documented coupling).

---

## 7. Universal acceptance criteria

In addition to each ticket's own acceptance criteria, every ticket
must satisfy these 10 items:

1. The PR's diff includes ONLY files listed in the ticket's "Files to
   be created", "Files to be modified", "New tests", and "Existing
   tests to update" sections. Any other modified file is a scope
   violation.
2. ``pytest -x --no-cov`` passes locally before push.
3. ``ruff check src/ tests/ packages/`` clean.
4. ``ruff format --check src/ tests/ packages/`` clean.
5. ``mypy`` (per scope) clean.
6. ``CHANGELOG.md`` has an entry under ``[Unreleased]`` in the
   appropriate section with full attribution per ``CLAUDE.md``
   Appendix A Stage 6.
7. Workflow gate has all 6 stages ``[DONE]``.
8. PR body explicitly references which ADR section it implements and
   links to this standards doc by ticket ID.
9. PR body reproduces the ticket's per-ticket acceptance criteria as
   a checklist with each item ticked.
10. CI is green on the PR before requesting review.

---

## 8. Open questions resolved by this document

These are decisions made in this document that go *beyond* the ADR
text and the source spec text. The ADRs and the source specs deferred
them to the implementation phase; this section records the resolution
so subsequent agents do not have to re-litigate them.

### Q1. Branch and ticket numbering scheme

**Decision**: Branch names follow ``<type>/issue-N/T-XXX-NNN-short``
where:

- ``<type>`` is one of ``feat``, ``fix``, ``refactor``, ``docs``,
  matching the conventional-commit prefix used in the commit message.
- ``N`` is the GitHub issue number for that specific ticket (a new
  issue per ticket, not the standards-doc issue #306).
- ``T-XXX-NNN`` is the ticket ID exactly as it appears in §9 / source
  spec, where ``XXX`` is one of ``TRK`` / ``IMG`` / ``SRS`` / ``LCMS``
  and ``NNN`` is zero-padded to three digits.
- ``short`` is a 2-5 word kebab-case description.

Ticket IDs are stable: T-TRK-006 always means "Block ABC dynamic-port
hooks + BlockSpec + framework read-path migration", regardless of
which agent picks it up.

### Q2. Where Sprint A sub-1c lands

**Decision**: T-TRK-011 (sub-1c) lives in **Sprint A Level A0**, in
parallel with the sub-1a deletion tickets and independent of the
sub-1b stacked cascade. It touches only ``CLAUDE.md``,
``docs/architecture/ARCHITECTURE.md`` (the ManualReview clarification
paragraph), and ``docs/guides/block-sdk.md``. None of those files are
touched by any sub-1b ticket, so there is no merge conflict.

Sub-1c does NOT depend on sub-1b being complete: the ManualReview
clarification is independent of the IOBlock refactor. Sub-1c is in
Sprint A purely for bookkeeping (it's part of the same "core cleanup"
master plan section), not because of a technical dependency.

### Q3. PR-B coupling resolution (Block ABC dynamic-port migration)

The Phase 11 master plan §4.3 lists three sub-PRs for Block ABC
dynamic-port hooks: PR-B-1 (Block ABC hooks + BlockSpec +
BlockSchemaResponse), PR-B-2 (framework read-path migration:
``Block.validate``, ``ProcessBlock.run``, ``workflow/validator.py``,
``api/routes/blocks.py``), and PR-B-3 (LoadData class).

**Decision**: PR-B-1 and PR-B-2 are **bundled into a single ticket
T-TRK-006** because splitting them would leave the codebase in a
broken intermediate state. Specifically:

- After PR-B-1 alone, the ``Block`` ABC has the new
  ``get_effective_*_ports()`` methods, and ``BlockSpec``/
  ``BlockSchemaResponse`` carry the new fields, but the framework
  callsites (``Block.validate``, ``ProcessBlock.run``, etc.) still
  read ``self.input_ports`` directly. Static blocks would still work,
  but if any block in the test suite happened to set
  ``dynamic_ports`` (even speculatively) the validator would silently
  use the wrong ports.
- After PR-B-1 alone, the BlockSchemaResponse would have a
  ``dynamic_ports`` field that the frontend cannot consume yet
  (frontend work is T-TRK-009), but no test would catch the broken
  intermediate.
- PR-B-2 alone is unimplementable: the framework callsites would call
  methods that don't exist on ``Block`` yet.

PR-B-1 + PR-B-2 must merge atomically. They are bundled into
**T-TRK-006**.

PR-B-3 (LoadData) is split off into its own ticket **T-TRK-007**
because it depends on PR-B-1+PR-B-2 but is otherwise self-contained
and is parallel-independent of T-TRK-008 (SaveData). T-TRK-007 and
T-TRK-008 are stacked on T-TRK-006 and run in parallel with each
other.

This bundling decision is the only place in the cascade where two
master-plan PRs collapse into one ticket. Every other coupling rule
was satisfiable by one-ticket-per-PR.

### Q4. Skeleton agent PR strategy

**Decision**: **One large skeleton PR covering all 4 tracks** instead
of four smaller per-track skeleton PRs. Rationale:

- The skeleton agent only creates placeholder files with
  ``raise NotImplementedError("T-XXX-NNN: ...")`` bodies. There is no
  business logic to review.
- A single PR makes it easier to verify completeness ("does the
  skeleton create a placeholder for every ticket in this standards
  doc?") via a single diff against ``main``.
- Splitting into four PRs would create cross-package dependencies
  (e.g. SRS skeleton imports from imaging skeleton) that would force
  one of the splits to merge first, defeating the parallelism
  argument for splitting.
- The skeleton PR is reviewed by the design/plan/skeleton audit agent,
  not by per-track audit agents, because completeness against this
  standards doc is the primary check.

### Q5. Test fixture pattern for cross-plugin imports

SRS tests need types from the imaging plugin (``Image``, ``Mask``,
``Label``). The imaging plugin is an optional dependency from the
core repo's perspective.

**Decision**: SRS tests that touch imaging types use
``pytest.importorskip("scieasy_blocks_imaging")`` at module top, plus
a session-scoped fixture in ``packages/scieasy-blocks-srs/tests/
conftest.py``::

    import pytest

    @pytest.fixture(scope="session")
    def imaging_types():
        imaging = pytest.importorskip("scieasy_blocks_imaging")
        return imaging  # caller does imaging_types.Image, .Mask, .Label

Tests that do not touch imaging types skip the fixture entirely. The
fixture is the **only** sanctioned way to import imaging-plugin types
from SRS tests; ad-hoc ``import scieasy_blocks_imaging`` at module
top (without ``importorskip``) breaks the SRS test suite when imaging
is not installed.

The same pattern applies to LC-MS tests that touch external tools
(ElMAVEN, AccuCor R) — see Q7 for the marker discipline.

### Q6. E2E test image access pattern

The four test images live at ``C:\Users\jiazh\Desktop\workspace\
Example\images\``. Filenames contain spaces and parentheses.

**Decision**: Constants in ``tests/fixtures/test_images.py`` (a new
file owned by T-TRK-003 alongside the ``noop_block`` move):

    from pathlib import Path

    TEST_IMAGES_DIR = Path(r"C:\Users\jiazh\Desktop\workspace\Example\images")

    K562_L_2845_TIF = TEST_IMAGES_DIR / "K562_L_2845 (uV).tif"
    K562_L_SPECTRA_TIF = TEST_IMAGES_DIR / "K562_L_spectra (uV).tif"
    K562_UL_2845_TIF = TEST_IMAGES_DIR / "K562_UL_2845 (uV).tif"
    K562_UL_SPECTRA_TIF = TEST_IMAGES_DIR / "K562_UL_spectra (uV).tif"

    SEGMENTATION_IMAGES = [K562_L_2845_TIF, K562_UL_2845_TIF]
    SPECTRA_IMAGES = [K562_L_SPECTRA_TIF, K562_UL_SPECTRA_TIF]

E2E tests import the constants instead of hardcoding paths. The
filename encoding (raw string for Windows backslashes; literal spaces
and parens) is centralised so a single test-image directory move only
requires one file edit.

If the ``TEST_IMAGES_DIR`` does not exist (CI environment), tests
that import from this fixture skip via
``pytest.importorskip`` style: ``pytest.skip("test images unavailable", allow_module_level=True)``
at the top of the test module after the path-existence check.

### Q7. Pytest markers introduced in Phase 11

**Decision**: The following pytest markers are introduced. Each must
be registered in the relevant ``pyproject.toml`` under
``[tool.pytest.ini_options].markers`` so that ``--strict-markers``
does not error. The registration is part of the ticket that first
uses the marker.

| Marker                   | Registered in                                | First-use ticket          |
|--------------------------|----------------------------------------------|---------------------------|
| ``requires_cellpose``    | ``packages/scieasy-blocks-imaging/pyproject.toml`` | T-IMG-019            |
| ``requires_napari``      | ``packages/scieasy-blocks-imaging/pyproject.toml`` | T-IMG-035            |
| ``requires_fiji``        | ``packages/scieasy-blocks-imaging/pyproject.toml`` | T-IMG-034 + T-TRK-015 |
| ``requires_cellprofiler``| ``packages/scieasy-blocks-imaging/pyproject.toml`` | T-IMG-036            |
| ``requires_qupath``      | ``packages/scieasy-blocks-imaging/pyproject.toml`` | T-IMG-037            |
| ``requires_r``           | ``pyproject.toml`` (root, for sub-1e) AND ``packages/scieasy-blocks-lcms/pyproject.toml`` (for AccuCor) | T-TRK-013 + T-LCMS-007 |
| ``requires_elmaven``     | ``packages/scieasy-blocks-lcms/pyproject.toml`` | T-LCMS-007             |
| ``requires_graphpad``    | ``packages/scieasy-blocks-lcms/pyproject.toml`` | T-LCMS-019             |
| ``requires_imaging``     | ``pyproject.toml`` (root, used by SRS tests) | (already registered Phase 10) |
| ``requires_lcms``        | ``pyproject.toml`` (root, used by integration tests) | T-LCMS-021         |

### Q8. Where markers register

**Decision**: Each plugin package registers its own markers in its
own ``pyproject.toml``. The root ``pyproject.toml`` only registers
markers used by tests in the core repo (``tests/`` directory).
Cross-package markers (``requires_imaging``, ``requires_lcms``) are
registered in the root because they are consumed by core integration
tests.

The first ticket in each plugin that introduces a new marker is
responsible for adding the registration line. Subsequent tickets in
the same plugin reuse the existing registration without modifying
``pyproject.toml`` (so that ticket diffs stay narrow).

### Q9. ADR-028 §D3 supersession check

ADR-028 §D3 originally specified six concrete loader/saver pairs
(``LoadArray``, ``LoadDataFrame``, ``LoadSeries``, ``LoadText``,
``LoadArtifact``, ``LoadCompositeData``) and six savers. ADR-028
Addendum 1 explicitly **supersedes** that with two dynamic blocks:
``LoadData`` + ``SaveData`` dispatching internally via private
module-level functions.

**Decision (anti-drift flag)**: Implementation agents reading
``docs/specs/phase11-imaging-block-spec.md`` may encounter references
to the original six-loader structure if the imaging spec was drafted
before the addendum landed. **The addendum overrides.** The core
repo's IO surface is ``LoadData`` / ``SaveData`` (one block each),
period. Any imaging-spec ticket that references "LoadArray" or
"LoadDataFrame" as a separate class is referring to a now-removed
design and must be reinterpreted as ``LoadData`` with the appropriate
``core_type`` config value.

This document **flags** the potential drift but does **not** fix it.
The audit agent reviewing the imaging-spec PRs must check each
implementation against this rule and reject any new code that
introduces a separate ``LoadArray`` / ``LoadDataFrame`` / etc. class
in core or in the imaging plugin.

### Q10. SRS ticket count discrepancy

The Phase 11 master plan §2.4 says the SRS plugin has ``~8 blocks``.
The actual SRS spec (``docs/specs/phase11-srs-block-spec.md``)
contains **11 blocks** (T-SRS-001 type + T-SRS-002..T-SRS-012 = 11
implementation tickets, plus T-SRS-000 scaffold + T-SRS-013
entry-point + T-SRS-014 integration test = 15 tickets total).

**Decision**: The **canonical count is 11 implementation blocks**
(documented in the SRS spec and reflected in §3 of this document as
15 tickets total). The master plan §2.4's "~8" was a rough estimate
during the doc-phase planning conversation. This standards doc and
the SRS spec are now authoritative.

### Q11. ImageCalculator port count for Phase 11

The imaging spec T-IMG-032 specifies ``ImageCalculator`` with two
fixed input ports (``A``, ``B``) plus a configurable expression. The
user-facing motivation for variadic input is to support arbitrary
N-port arithmetic.

**Decision**: ``ImageCalculator`` is **2-port-fixed in 0.1.0**. The
variadic version is deferred to ADR-029. The 2-port version satisfies
the immediate use cases (``A+B``, ``A-B``, ``A*B``, ``A/B``, plus a
restricted user-defined expression on the two named inputs); the
variadic version requires the ADR-029 mechanism that does not exist
yet. Implementation agents must not "anticipate" variadic by adding
optional ``C``, ``D``, ``E`` input ports.

### Q12. Test runner discovery for monorepo

Phase 11 introduces ``packages/scieasy-blocks-imaging/`` and
``packages/scieasy-blocks-srs/`` and ``packages/scieasy-blocks-lcms/``
each with their own ``tests/`` directory.

**Decision**: The root ``pyproject.toml`` ``[tool.pytest.ini_options]``
section gains a ``testpaths`` key that includes both the core
``tests`` directory and each plugin's ``tests`` directory::

    [tool.pytest.ini_options]
    testpaths = [
        "tests",
        "packages/scieasy-blocks-imaging/tests",
        "packages/scieasy-blocks-srs/tests",
        "packages/scieasy-blocks-lcms/tests",
    ]
    rootdir = "."

Plugin-package tests run via the same ``pytest`` invocation as core
tests. Each plugin package also has its own ``pyproject.toml`` so
that ``pip install -e packages/scieasy-blocks-imaging`` works
standalone for downstream consumers.

This decision is implemented incrementally: T-IMG-038 / T-SRS-013 /
T-LCMS-020 each add their plugin's ``tests`` path to the root config
when the plugin first becomes installable. The first plugin
(imaging) lands the initial monorepo testpaths config; later plugins
extend it.

---
