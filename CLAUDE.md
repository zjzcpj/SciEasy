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

# 3. Architectural Boundaries

These boundaries must be respected unless a formal architecture decision explicitly changes them.

## 3.1 Backend / Runtime boundary

The backend/runtime owns:

- workflow definitions
- block registry
- state machine
- run history
- lineage and provenance
- object registry
- cache manifests
- plugin registration
- execution policies

The frontend must not become the place where execution truth is stored.

## 3.2 Frontend boundary

The frontend is responsible for:

- workflow editing
- parameter editing
- execution triggering
- state visualization
- object inspection
- artifact preview
- manual task handling

The frontend must not silently invent workflow semantics that do not exist in the backend.

## 3.3 Core boundary

Core should contain:

- primitive object contracts
- graph models
- block specifications
- runtime state definitions
- lineage/audit primitives
- serialization and validation

Core should not directly own:
- modality-specific analysis logic
- vendor-specific application logic
- heavy UI concerns
- experimental agent behavior

## 3.4 Plugin boundary

Plugin packages are the correct place for:

- modality-specific logic
- block families
- external app adapters
- specialized data types
- optional integrations

Do not push plugin/domain logic into core without strong reason and formal approval.

## 3.5 AI boundary

AI modules may:
- compile natural language into workflow proposals
- suggest blocks and parameters
- scaffold plugins
- propose workflow optimizations
- explain outputs

AI modules must not:
- execute uncontrolled code by default
- bypass schemas
- mutate user data silently
- modify architecture without documentation

---

# 4. Repository Working Model

All meaningful work should be traceable through the following chain:

**Idea -> Issue -> Spec/ADR -> Branch -> Commit -> PR -> Review -> CI/Test -> Merge -> Release**

If this chain is broken, traceability is broken.

---

# 5. Standard Development Workflow

## 5.1 Before coding

Before starting implementation:

1. confirm there is an issue
2. confirm the scope
3. confirm the acceptance criteria
4. determine whether a spec is required
5. determine whether an ADR is required

## 5.2 When a Spec is required

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

# 8. Data and Runtime Rules

## 8.1 Treat large data as normal

The system must assume that users may work with:
- 100GB+ imaging data
- chunked hyperspectral arrays
- large tables
- large collections of artifacts

Therefore:
- avoid eager loading
- prefer lazy references
- prefer chunked/persisted representations
- design previews separately from full payloads

## 8.2 Runtime states must remain explicit

Do not hide execution transitions.

Manual review, waiting for external apps, pause, retry, failure, and completion must all be represented clearly in runtime state.

## 8.3 External applications are formal runtime participants

Do not treat external tools as informal side paths.

If a block launches Fiji, ElMAVEN, napari, or another application, that behavior must be:
- explicit
- documented
- resumable if possible
- lineage-aware

## 8.4 Batch execution must remain mode-aware

Do not assume all batch work should be parallel.

Some blocks must support:
- serial single-item review
- parallel map execution
- hybrid behavior
- runtime barriers before manual intervention

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