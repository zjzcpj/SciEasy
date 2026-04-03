# CLAUDE.md

This file defines the working rules, architectural boundaries, and engineering standards for AI assistants and human contributors in this repository.

The goal is to keep development standardized, traceable, extensible, and aligned with the project's long-term architecture.

---

# 1. Project Identity

## What this project is

This repository builds an **AI-native, inclusive workflow runtime for multimodal scientific data**.

The system is intended to support:

- multimodal scientific data in one workflow graph
- typed data objects and standardized block I/O
- Python, R, CLI, GUI software, and manual review in the same runtime
- serial, parallel, batch, and interactive execution
- extensibility through plugins
- AI-assisted orchestration, block generation, and workflow construction

## What this project is not

This project is **not**:

- a replacement for every existing scientific tool
- a monolithic end-user application without a formal runtime
- a collection of ad hoc scripts
- a no-code toy UI without execution semantics
- a place for architecture-free experimentation directly on main branches

---

# 2. Non-Negotiable Principles

The following principles are mandatory.

## 2.1 Workflow graph is the source of truth

The graph definition, runtime state, block contracts, lineage, and execution semantics belong to the backend/runtime layer.

The frontend is an editor and viewer, not the source of truth.

## 2.2 Data flows as references, not large in-memory payloads

Objects passed between blocks should usually be typed object references, lazy handles, or persisted artifacts.

Do not design the system assuming all data fits in memory.

## 2.3 Core must stay small and stable

The core should define minimal contracts, not solve every domain-specific problem.

Prefer:
- stable primitive object types
- stable block contracts
- stable execution semantics

Avoid:
- excessive domain logic in core
- deep inheritance trees
- premature specialization

## 2.4 Everything is connectable, not everything is native

We do not require users to migrate their entire existing workflow.

Instead, we support:
- code blocks
- external application blocks
- manual review blocks
- import/export bridges
- plugin-based extensions

## 2.5 Manual steps are first-class

Human review, editing, annotation, approval, or GUI-based intervention are not hacks.

They are part of the formal workflow model.

## 2.6 AI may propose, but runtime validates and executes

AI-generated graphs, blocks, parameters, or suggestions must always be validated against formal schemas and runtime rules.

AI must never bypass contracts, lineage, or execution policies.

---

# 3. Repository Working Model

All meaningful work should be traceable through the following chain:

**Idea -> Issue -> Spec/ADR -> Branch -> Commit -> PR -> Review -> CI/Test -> Merge -> Release**

If this chain is broken, traceability is broken.

---

# 4. Standard Development Workflow

## 4.1 Before coding

Before starting implementation:

1. confirm there is an issue
2. confirm the scope
3. confirm the acceptance criteria
4. determine whether a spec is required
5. determine whether an ADR is required

## 4.2 When a Spec is required

A spec is required when work changes any of the following:

- object model
- block protocol
- runtime execution behavior
- storage behavior
- API contracts
- plugin contracts
- major UI semantics
- AI orchestration behavior
- external app integration model

If in doubt, write the spec.

## 5.3 When an ADR is required

An ADR is required when making a decision that is:

- architectural
- hard to reverse
- likely to affect multiple modules
- likely to be questioned later
- a tradeoff between competing long-term options

Examples:
- choosing workflow graph ownership rules
- choosing storage model
- defining primitive object types
- choosing plugin strategy
- defining external app execution semantics

## 5.4 During coding

During implementation:

- keep changes scoped
- avoid unrelated refactors
- preserve backward compatibility when possible
- update tests with behavior changes
- update docs for user-facing or architecture-affecting changes
- leave the repo in a working state

## 5.5 Before opening a PR

Before opening a PR:

- run tests
- verify lint/formatting
- update or add docs if needed
- link the issue
- link spec/ADR if applicable
- clearly state risks and scope

---

# 6. Required Engineering Discipline

## 6.1 No direct push to main

Main branch must be protected.

All changes go through PR.

## 6.2 Every meaningful change must be attributable

Every meaningful change should be traceable to:
- an issue
- a commit
- a PR
- a review
- a test outcome

## 6.3 Use focused commits

Do not create vague commits like:
- fix
- update
- misc
- changes
- final

Use meaningful, scoped commit messages.

Preferred style:
- feat(runtime): add pause state for manual block
- fix(storage): avoid eager loading of array preview
- docs(adr): record external app block design

## 6.4 Tests are part of the change

A bug fix should ideally include a regression test.

A new contract should include validation or integration tests.

A major runtime behavior change should include integration coverage.

## 6.5 Documentation is part of the product

Docs are not optional.

If behavior changes, documentation must be updated accordingly.

---

# 7. Coding Boundaries

## 7.1 Prefer explicit contracts over clever shortcuts

Prefer:
- typed models
- explicit schema validation
- clear interfaces
- deterministic behavior

Avoid:
- hidden magic
- implicit side effects
- dynamic behavior without contracts
- tight coupling across packages

## 7.2 Favor composition over deep inheritance

Primitive objects should remain stable.

Domain-specific behavior should usually be layered on top via wrappers, metadata, adapters, or plugins.

Avoid complex inheritance trees unless there is a compelling reason.

## 7.3 Keep modules narrow in responsibility

Each module/package should have a clear purpose.

Do not mix:
- core contracts with plugin logic
- frontend state with backend truth
- storage mechanics with UI assumptions
- AI prompting logic with runtime policy

## 7.4 No premature optimization at the expense of clarity

Performance matters, especially for large scientific data, but premature complexity without profiling should be avoided.

Choose clarity first for the initial implementation of a subsystem, unless performance is a known requirement of that subsystem.

## 7.5 No architecture drift through convenience hacks

Do not introduce temporary shortcuts that contradict the intended architecture unless they are explicitly documented as temporary and tracked by an issue.

---

# 9. AI Assistant Operating Rules

These rules apply specifically to Claude or other AI coding assistants working in this repository.

## 9.1 Claude must preserve project intent

Claude should optimize for:
- standardized process
- architectural consistency
- traceability
- maintainability
- clear boundaries

Claude must not optimize only for short-term implementation speed.

## 9.2 Claude must not silently broaden scope

If asked to implement a feature, Claude should not quietly redesign multiple subsystems unless explicitly asked or clearly required.

Prefer the smallest architecture-consistent change.

## 9.3 Claude should identify missing process artifacts

If a task appears to require:
- a spec
- an ADR
- a new issue
- a test plan
- a migration note

Claude should say so and, where appropriate, draft the missing artifact.

## 9.4 Claude should respect incomplete skeleton modules

This repository may intentionally include empty or partially implemented modules.

Claude should not assume every placeholder must be implemented immediately.

## 9.5 Claude should not collapse boundaries for convenience

Claude must not:
- move plugin logic into core for convenience
- place runtime truth in frontend state
- bypass schemas to “make things work”
- add hidden implicit behavior

## 9.6 Claude should produce structured outputs

When asked to design or change something significant, Claude should usually provide:

- summary
- affected modules
- assumptions
- implementation approach
- risks
- test implications
- doc implications

## 9.7 Claude should prefer traceable scaffolding

When generating code, Claude should prefer:
- explicit types
- clear file placement
- documented interfaces
- TODO markers for incomplete areas
- predictable naming

---

# 10. Required Documentation Updates

The following changes usually require documentation updates.

## Update a Spec when:
- adding a subsystem
- changing execution semantics
- changing schemas
- changing block behavior
- changing storage behavior
- changing API behavior

## Update an ADR when:
- making an architectural decision
- reversing a prior architectural decision
- replacing a foundational dependency or pattern

## Update the changelog when:
- adding user-visible functionality
- fixing significant bugs
- changing behavior
- adding or removing plugin capability
- making breaking changes

## Update contributing or architecture docs when:
- changing developer workflow
- changing repo structure
- changing testing strategy
- changing plugin authoring expectations

---

# 11. Definition of Done

A task is not done just because code exists.

A task is done when:

- the scope matches the issue/spec
- code is committed in the correct module
- tests exist or the lack of tests is explicitly justified
- documentation is updated if needed
- architecture boundaries are respected
- the PR explains what changed and why
- CI passes
- reviewers can understand the change

---

# 12. Prohibited Shortcuts

The following are discouraged or forbidden unless explicitly justified:

- direct push to protected branches
- undocumented architecture changes
- silent behavior changes
- unreviewed breaking API changes
- plugin logic inserted into core without decision records
- frontend-only workflow semantics
- bypassing tests for convenience
- adding dependencies without justification
- massive refactors hidden inside feature PRs
- “temporary” hacks without tracking issues

---

# 13. Preferred Task Checklist for Claude

When asked to implement something non-trivial, Claude should mentally follow this checklist:

1. What problem is being solved?
2. Which module should own this?
3. Does this require a spec?
4. Does this require an ADR?
5. Is there already a contract this must fit into?
6. Does this change runtime truth, storage, or plugin boundaries?
7. What tests should exist?
8. What docs should be updated?
9. What is intentionally left unimplemented?
10. What risks or follow-up tasks should be recorded?

---

# 14. Preferred Response Style for Claude

When working on this repository, Claude should:

- be concrete
- be structured
- be conservative with architectural changes
- explain tradeoffs
- call out uncertainty
- distinguish implemented behavior from planned behavior
- avoid pretending placeholders are complete

Claude should not:
- over-promise
- obscure missing pieces
- silently make broad assumptions
- claim unsupported behavior exists

---

# 15. If You Are Unsure

If a request is ambiguous, prefer this order:

1. preserve architecture
2. preserve traceability
3. preserve small scoped change
4. preserve future extensibility
5. defer broad redesign unless explicitly asked

When in doubt, document the assumption.

---

# 16. Project Priorities

When tradeoffs arise, optimize in roughly this order:

1. correctness of architecture
2. traceability and maintainability
3. stable contracts
4. extensibility
5. clear developer experience
6. implementation speed
7. polish

---

# 17. Summary

This repository is building a long-lived scientific workflow platform, not a disposable prototype.

Therefore:

- process matters
- boundaries matter
- documentation matters
- contracts matter
- traceability matters

Claude and all contributors must work in a way that keeps the system understandable, extensible, and auditable over time.

---

# Appendix A: Mandatory Workflow Gate Protocol

> **This protocol is NON-NEGOTIABLE.** Every implementation task must pass through
> the gate system. Skipping steps is a protocol violation equivalent to pushing
> directly to main.

## The Gate System

This project uses `.workflow/gate.py` as a state machine that enforces the
development pipeline. The gate CLI is the **single source of truth** for whether
a step has been completed. You cannot self-attest completion — only the gate
records count.

## Required Execution Sequence

For **every** implementation task (feature, bugfix, refactor), execute these
steps **in exact order**. Each step requires the previous step's gate to be
recorded.

### Step 1: Start Workflow + Create Issue

```bash
# 1a. Initialize workflow tracking
python .workflow/gate.py start "Brief description of the task"
# Note the TASK_ID from output

# 1b. Create the GitHub issue
gh issue create --template feature.md --title "..." --body "..."
# Note the ISSUE_NUMBER and ISSUE_URL

# 1c. Record gate completion
python .workflow/gate.py advance $TASK_ID create_issue \
  --data '{"issue_number": 42, "issue_url": "https://github.com/.../issues/42"}'
```

**You CANNOT proceed to Step 2 until `create_issue` gate is recorded.**

### Step 2: Write Change Plan

```bash
# 2a. Write the change plan as an issue comment
gh issue comment $ISSUE_NUMBER --body "## Change Plan for #$ISSUE_NUMBER
### Approach
...
### Files to Modify
| File | Action | Rationale |
|------|--------|-----------|
| ... | ... | ... |
### Risk Assessment
..."

# 2b. Record gate completion
python .workflow/gate.py advance $TASK_ID write_change_plan \
  --data '{"change_plan_comment_url": "https://...", "files_to_modify": ["src/..."]}'
```

**You CANNOT proceed to Step 3 until `write_change_plan` gate is recorded.**

### Step 3: Create Branch + Implement

```bash
# 3a. Create the branch
git checkout -b feat/issue-$ISSUE_NUMBER/short-description

# 3b. Implement changes (scoped to change plan!)

# 3c. Commit with conventional format
git add .
git commit -m "feat(#$ISSUE_NUMBER): description of change"

# 3d. Record gate completion
python .workflow/gate.py advance $TASK_ID create_branch \
  --data '{"branch_name": "feat/issue-42/...", "commit_shas": ["abc1234"]}'
```

**You CANNOT proceed to Step 4 until `create_branch` gate is recorded.**

### Step 4: Submit PR

```bash
# 4a. Push and create PR
git push -u origin HEAD
gh pr create --title "feat(#$ISSUE_NUMBER): ..." \
  --body "## Summary\n...\n## Related Issues\nCloses #$ISSUE_NUMBER"

# 4b. Record gate completion
python .workflow/gate.py advance $TASK_ID submit_pr \
  --data '{"pr_number": 48, "pr_url": "https://github.com/.../pull/48"}'
```

**You CANNOT proceed to Step 5 until `submit_pr` gate is recorded.**

### Step 5: Update Documentation

```bash
# 5a. Update relevant docs
# - If new public API: update API reference in docs/
# - If behavior change: update relevant spec in docs/specs/
# - If architectural decision: write/update ADR in docs/adr/

# 5b. Commit docs changes
git add docs/
git commit -m "docs(#$ISSUE_NUMBER): update documentation for ..."
git push

# 5c. Record gate completion
python .workflow/gate.py advance $TASK_ID update_docs \
  --data '{"docs_updated": ["docs/specs/pipeline.md"]}'
```

**You CANNOT proceed to Step 6 until `update_docs` gate is recorded.**

### Step 6: Update Changelog

```bash
# 6a. Add changelog entry under [Unreleased]
# Format: - [#ISSUE_NUMBER] Brief description (@agent-name)

# 6b. Commit
git add CHANGELOG.md
git commit -m "chore(#$ISSUE_NUMBER): update changelog"
git push

# 6c. Record gate completion
python .workflow/gate.py advance $TASK_ID update_changelog \
  --data '{"changelog_entry": "[#42] Add TIFF loader to pipeline (@claude)"}'
```

---

## Self-Check Protocol

Before executing **any** step, run:

```bash
python .workflow/gate.py status $TASK_ID
```

Verify that the **previous stage shows [DONE]** before attempting the current one.
If you see [LOCK] on the stage you are about to attempt, STOP and complete
the prerequisites first.

## What To Do When Blocked

If `gate.py advance` returns `WORKFLOW GATE: ADVANCEMENT BLOCKED`:

1. **Do not attempt to work around it.**
2. Run `python .workflow/gate.py status $TASK_ID` to see what is missing.
3. Complete the missing prerequisite stage.
4. Then retry.

## Scope Discipline

During implementation (Step 3):

- **Only modify files listed in the Change Plan** (Step 2).
- If you discover additional files need changing, **update the Change Plan comment first**.
- Do not smuggle unrelated changes into the PR.

## Small Changes Still Use Gates

If the task seems too small for the full workflow (e.g., a typo fix):

1. Still create an issue.
2. The change plan can be a single sentence.
3. Docs update can note "N/A — no docs affected".
4. Changelog can note "N/A — trivial fix".
5. **But you still must go through all 6 gates.**

The overhead is intentional. It ensures traceability even for small changes.

## Gate CLI Quick Reference

| Command | Purpose |
|---------|---------|
| `python .workflow/gate.py start "title"` | Start new workflow |
| `python .workflow/gate.py advance TASK STAGE --data '{...}'` | Advance one stage |
| `python .workflow/gate.py status TASK` | Show progress |
| `python .workflow/gate.py list` | List all workflows |
| `python .workflow/gate.py validate TASK STAGE` | Check if stage is reachable |
| `python .workflow/gate.py abort TASK --reason "..."` | Abort workflow |


---

# Appendix B: SpecKit Integration

## What SpecKit Is

This project uses [SpecKit](https://github.com/spec-kit) (`.specify/` directory) as the
**feature-level design pipeline**. SpecKit converts a natural language feature
description into structured artifacts (spec, plan, tasks) through a series of
slash commands in Claude Code.

SpecKit skills are auto-discovered from `.claude/skills/speckit-*`. You do NOT
need to memorize their internals — just use the slash commands.

## SpecKit vs Workflow Gate: When to Use Which

These two systems operate at **different granularities** and are complementary.

### SpecKit = Feature-level design pipeline

Use SpecKit when starting a **new feature, subsystem, or significant change**
that needs requirements analysis, design decisions, and task decomposition.

```
/speckit.specify "Add OME-TIFF support to pipeline loader"
  → generates spec.md (what & why)
/speckit.clarify
  → resolves ambiguities in spec
/speckit.plan
  → generates plan.md, data-model.md, contracts/ (how)
/speckit.tasks
  → generates tasks.md (ordered, dependency-aware task list)
/speckit.analyze
  → cross-artifact consistency check (read-only)
```

### Workflow Gate = Per-task execution pipeline

Use the Workflow Gate when **executing each individual task** from the task
list. Every task that touches code must go through the 6-stage gate:

```
gate.py start → create_issue → write_change_plan → create_branch
  → submit_pr → update_docs → update_changelog
```

### Combined Workflow (Standard Operating Procedure)

For any significant feature:

```
Phase 1: Design (SpecKit)
  /speckit.specify "..."     → spec.md
  /speckit.clarify           → refined spec.md
  /speckit.plan              → plan.md + design artifacts
  /speckit.tasks             → tasks.md with T001, T002, T003...

Phase 2: Execute (Workflow Gate, per task)
  For each task in tasks.md:
    gate.py start "T001: ..."
    gate.py advance ... create_issue
    gate.py advance ... write_change_plan
    gate.py advance ... create_branch
    [implement the task]
    gate.py advance ... submit_pr
    gate.py advance ... update_docs
    gate.py advance ... update_changelog
```

### When to Skip SpecKit

For **small, well-understood changes** (typo fixes, config tweaks, simple bug
fixes), you may skip SpecKit and go directly to the Workflow Gate. The decision
rule:

- If the change requires **design decisions** → use SpecKit first
- If the change is **obvious and scoped** → go straight to Workflow Gate

## SpecKit Quick Reference

| Command | Purpose | Output |
|---------|---------|--------|
| `/speckit.constitution` | Define project principles | `.specify/memory/constitution.md` |
| `/speckit.specify "..."` | Generate requirements spec | `specs/<branch>/spec.md` |
| `/speckit.clarify` | Resolve ambiguities (max 5 questions) | Updated `spec.md` |
| `/speckit.plan` | Generate implementation plan | `plan.md`, `data-model.md`, `contracts/` |
| `/speckit.checklist <domain>` | Requirements quality checklist | `checklists/<domain>.md` |
| `/speckit.tasks` | Generate ordered task list | `tasks.md` |
| `/speckit.analyze` | Cross-artifact consistency check | Report (read-only) |
| `/speckit.implement` | Execute tasks from tasks.md | Code changes |
| `/speckit.taskstoissues` | Convert tasks to GitHub Issues | GitHub Issues |
