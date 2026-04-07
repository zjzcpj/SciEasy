# Stage 10.1 — Palette & Category Refinement: Design Document

> **Status**: Draft (Part 1 scaffolding). Part 2 implementation tracked separately.
>
> **Owner**: Phase 10 agents (A = Part 1 research + skeleton, B = Part 2 implementation)
>
> **References**:
> - Roadmap: `docs/roadmap/ROADMAP_v0.3.md` Stage 10.1
> - Tracking issue: #250
> - Part 1 issue: #251
> - ADR-009 (BlockRegistry)
> - ADR-025 (PackageInfo entry-point convention)
> - ADR-026 (Block SDK / 3-level palette)

---

## 1. Context & goals

### 1.1 Quoting the roadmap

From `docs/roadmap/ROADMAP_v0.3.md` Stage 10.1:

> **Goal**: the block palette supports 3-level grouping (Package > Category > Block)
> and user-written drop-in blocks are classified under "Custom" — separate from
> installed packages and base block classes.

The roadmap enumerates the required work:

1. Optional `category: ClassVar[str]` on `BlockBase` (explicit override)
2. `_infer_category()` prefers the ClassVar, falls back to hierarchy inference
3. Tier 1 drop-in blocks default to category `"Custom"` unless explicitly declared
4. Tier 2 (entry-points) blocks keep their declared/inferred category — NOT mixed into "Custom"
5. `BlockSpec.source` takes values `"builtin"`, `"package"`, or `"custom"`
6. `GET /api/blocks/` includes `source` and `category` fields
7. Frontend `BlockPalette.tsx` renders 3-level collapsible tree with "Custom" at the bottom

### 1.2 Why a 2-part split

Part 1 (this PR) produces:
- A design doc that documents **current state** and **proposed changes** with exact signatures
- Type-level scaffolding (field declarations, TODO markers) that compiles and does not change behavior
- Skipped test stubs defining the test matrix Agent B must satisfy

Part 2 (separate PR by Agent B) implements:
- The real `_infer_category` ClassVar check
- The `BlockSpec.source` value rename (with test and caller updates)
- The population of `source`/`package_name` in `_summary()`
- The `BlockPalette.tsx` 3-level rewrite

This split keeps the risky behavior changes in a single reviewable PR and lets
the scaffolding PR be low-risk (purely additive, type-only).

---

## 2. Current state analysis

This section documents the **actual code** Agent A inspected in the repository
as of 2026-04-06. All file paths are absolute to the repository root.

### 2.1 The base Block class

**Location**: `src/scieasy/blocks/base/block.py` (lines 35–267)

The base class is named `Block` (NOT `BlockBase`). The roadmap informally says
"BlockBase"; the real class is just `Block`. This naming is stable and should
not be changed — any API renaming would be out of scope for Stage 10.1.

Relevant existing ClassVars on `Block`:

```python
class Block(ABC):
    name: ClassVar[str] = "Unnamed Block"
    description: ClassVar[str] = ""
    version: ClassVar[str] = "0.1.0"
    input_ports: ClassVar[list[InputPort]] = []
    output_ports: ClassVar[list[OutputPort]] = []
    execution_mode: ClassVar[ExecutionMode] = ExecutionMode.AUTO
    terminate_grace_sec: ClassVar[float] = 5.0
    key_dependencies: ClassVar[list[str]] = []
    config_schema: ClassVar[dict[str, Any]] = {"type": "object", "properties": {}}
```

Adding `category: ClassVar[str] = ""` is a natural extension that follows the
existing class-metadata pattern.

### 2.2 Current `_infer_category` implementation

**Location**: `src/scieasy/blocks/registry.py` (lines 339–363)

```python
def _infer_category(cls: type) -> str:
    """Infer the block category from the class hierarchy."""
    # Lazy imports to avoid circular dependencies.
    from scieasy.blocks.ai.ai_block import AIBlock
    from scieasy.blocks.app.app_block import AppBlock
    from scieasy.blocks.code.code_block import CodeBlock
    from scieasy.blocks.io.io_block import IOBlock
    from scieasy.blocks.process.process_block import ProcessBlock
    from scieasy.blocks.subworkflow.subworkflow_block import SubWorkflowBlock

    if issubclass(cls, IOBlock):
        return "io"
    if issubclass(cls, ProcessBlock):
        return "process"
    if issubclass(cls, CodeBlock):
        return "code"
    if issubclass(cls, AppBlock):
        return "app"
    if issubclass(cls, AIBlock):
        return "ai"
    if issubclass(cls, SubWorkflowBlock):
        return "subworkflow"
    if issubclass(cls, AIBlock):  # duplicate line (pre-existing)
        return "ai"
    return "unknown"
```

Notes:
- The function is a module-level helper, not a method.
- It is called from `_spec_from_class` (line 330).
- There is a duplicate `issubclass(cls, AIBlock)` check at the bottom. Agent A leaves this alone (not in scope; pre-existing issue).
- The fallback return is `"unknown"`, not `"custom"`. This becomes the key distinction Agent B must implement:
  - Override order: ClassVar (if set) > hierarchy inference > `"Custom"` (for Tier 1 only) > `"unknown"` (otherwise)

### 2.3 Current `BlockSpec.source` field values

**Location**: `src/scieasy/blocks/registry.py` (lines 26–47, 82–229)

```python
@dataclass
class BlockSpec:
    name: str
    description: str = ""
    version: str = "0.1.0"
    module_path: str = ""
    class_name: str = ""
    file_path: str | None = None
    file_mtime: float | None = None
    category: str = ""
    input_ports: list[Any] = field(default_factory=list)
    output_ports: list[Any] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    type_name: str = ""
    package_name: str = ""
```

**Current source values actually assigned** (verified by inspection):

| Scan tier | Method | Line | Value passed to `_spec_from_class(source=...)` |
|-----------|--------|------|------------------------------------------------|
| Built-ins | `_scan_builtins` | 111 | `"builtin"` |
| Tier 1 (drop-in) | `_scan_tier1` | 140 | `"tier1"` |
| Tier 2 (entry_points) | `_scan_tier2` | 225 | `"entry_point"` |

**Who depends on these values today**:

| File | Line | Usage | Effect of rename |
|------|------|-------|------------------|
| `src/scieasy/blocks/registry.py` | 290 | `if spec.source == "tier1"` (in `hot_reload`) | Must update to `"custom"` |
| `tests/blocks/test_registry.py` | 68 | `assert specs["My Custom"].source == "tier1"` | Must update to `"custom"` |
| `tests/blocks/test_registry.py` | 360 | `assert spec.source == "entry_point"` | Must update to `"package"` |
| `tests/integration/test_block_sdk_e2e.py` | 108 | `assert spec_a.source == "entry_point"` | Must update to `"package"` |
| `tests/integration/test_block_sdk_e2e.py` | 109 | `assert spec_b.source == "entry_point"` | Must update to `"package"` |
| `tests/integration/test_block_sdk_e2e.py` | 283 | `assert spec.source == "tier1"` | Must update to `"custom"` |
| `tests/integration/test_block_sdk_e2e.py` | 690 | `assert specs["Dropin Integ"].source == "tier1"` | Must update to `"custom"` |
| `tests/integration/test_block_sdk_e2e.py` | 692 | `assert specs["Tier2Integ"].source == "entry_point"` | Must update to `"package"` |

None of these are part of a published API schema. They are all internal
(registry internals + test assertions). The rename is safe but must be atomic.

**Design recommendation (for Agent B)**: Rename in a single commit touching
all 8 lines above plus the 3 assignment sites in `registry.py`. Do not
introduce any compatibility shim — the values were never exposed publicly.

### 2.4 Current frontend palette component

**Location**: `frontend/src/components/BlockPalette.tsx` (156 lines)

The component today is **flat** — it groups blocks by `category` only, using a
hard-coded ordering array:

```ts
const categoryOrder = ["io", "process", "code", "app", "ai", "subworkflow", "custom"];
```

It does NOT use a package level. The `grouped` computation:

```ts
const grouped = categoryOrder
  .map((category) => ({
    category,
    blocks: filtered.filter((block) => block.category === category),
  }))
  .filter((entry) => entry.blocks.length);
```

Each group is rendered as a `<section>` with the category name as its header.
There is no collapse/expand state. There is no notion of packages.

The component also expands `io_block` into two virtual entries ("Load Block"
and "Save Block") via `expandIOBlocks`. Agent B must preserve this expansion
when refactoring.

### 2.5 Current API type contract

**Backend Pydantic schema**: `src/scieasy/api/schemas.py` (lines 84–93)

```python
class BlockSummary(BaseModel):
    name: str
    type_name: str
    category: str
    description: str = ""
    version: str = "0.1.0"
    input_ports: list[BlockPortResponse] = Field(default_factory=list)
    output_ports: list[BlockPortResponse] = Field(default_factory=list)
```

**Frontend TS interface**: `frontend/src/types/api.ts` (lines 60–68)

```ts
export interface BlockSummary {
  name: string;
  type_name: string;
  category: string;
  description: string;
  version: string;
  input_ports: BlockPortResponse[];
  output_ports: BlockPortResponse[];
}
```

**Backend `_summary` helper**: `src/scieasy/api/routes/blocks.py` (lines 41–50)

```python
def _summary(spec: Any) -> BlockSummary:
    return BlockSummary(
        name=spec.name,
        type_name=spec.type_name,
        category=spec.category,
        description=spec.description,
        version=spec.version,
        input_ports=[_port_response(port, direction="input") for port in spec.input_ports],
        output_ports=[_port_response(port, direction="output") for port in spec.output_ports],
    )
```

The shape is symmetric (Pydantic model ↔ TS interface). `BlockSpec.source` and
`BlockSpec.package_name` already exist on the dataclass (lines 45, 47 of
`registry.py`) but are **not** exposed by the API today — they are dropped in
`_summary()`. Agent B adds the fields to the schema and populates them.

---

## 3. Proposed changes

### 3.1 Part 1 (Agent A, this PR) — exact signatures

All Part 1 changes are either **additive field declarations** or **TODO comments**.
Nothing changes runtime behavior.

#### 3.1.1 `src/scieasy/blocks/base/block.py`

Add one line inside the `Block` class, next to the existing ClassVars:

```python
# Part 1 adds (after line 47):
category: ClassVar[str] = ""
```

Rationale: declares the field so subclasses can override it. An empty string
means "no explicit category" — the same semantic as today's absent attribute.
`_infer_category` will check this ClassVar in Part 2.

#### 3.1.2 `src/scieasy/blocks/registry.py`

Add a TODO comment inside `_infer_category` but leave the body unchanged:

```python
def _infer_category(cls: type) -> str:
    """Infer the block category from the class hierarchy."""
    # TODO(agent-b, stage-10.1): check `cls.category` ClassVar override first.
    # If cls.category is a non-empty string, return it verbatim.
    # Then fall back to the existing hierarchy checks below.
    # See docs/design/stage-10-1-palette.md §3.2.1.
    from scieasy.blocks.ai.ai_block import AIBlock
    ...  # (existing body unchanged)
```

#### 3.1.3 `src/scieasy/api/schemas.py`

Extend `BlockSummary` with two optional fields:

```python
class BlockSummary(BaseModel):
    """Condensed block metadata for the palette."""

    name: str
    type_name: str
    category: str
    description: str = ""
    version: str = "0.1.0"
    input_ports: list[BlockPortResponse] = Field(default_factory=list)
    output_ports: list[BlockPortResponse] = Field(default_factory=list)
    # Stage 10.1: source/package_name surfaces palette grouping metadata.
    # Agent A declares; Agent B populates in _summary().
    source: str = ""
    package_name: str = ""
```

Safe defaults (`""`) mean existing API tests that construct `BlockSummary`
instances without these fields still validate.

#### 3.1.4 `src/scieasy/api/routes/blocks.py`

Add a TODO in `_summary()` but leave field construction unchanged:

```python
def _summary(spec: Any) -> BlockSummary:
    # TODO(agent-b, stage-10.1): populate source and package_name from spec.
    # After the BlockSpec.source value rename (tier1 -> custom, entry_point
    # -> package), pass `source=spec.source, package_name=spec.package_name`
    # here. Agent A left the call unchanged to preserve existing behavior.
    return BlockSummary(
        name=spec.name,
        type_name=spec.type_name,
        category=spec.category,
        description=spec.description,
        version=spec.version,
        input_ports=[_port_response(port, direction="input") for port in spec.input_ports],
        output_ports=[_port_response(port, direction="output") for port in spec.output_ports],
    )
```

#### 3.1.5 `frontend/src/types/api.ts`

Add two optional fields to the TS `BlockSummary` interface:

```ts
export interface BlockSummary {
  name: string;
  type_name: string;
  category: string;
  description: string;
  version: string;
  input_ports: BlockPortResponse[];
  output_ports: BlockPortResponse[];
  // Stage 10.1 Part 1: optional because Agent B populates them in Part 2.
  source?: string;
  package_name?: string;
}
```

Optional (`?`) because Part 1 does not populate them on the backend. Existing
consumers that don't read these fields are unaffected.

#### 3.1.6 `frontend/src/components/BlockPalette.tsx`

Add a clearly marked TODO comment block at the top of the file. **Do NOT change
the rendered output**. The component still flat-groups by category:

```tsx
import { useRef } from "react";
import type { BlockSummary } from "../types/api";

/*
 * TODO(agent-b, stage-10.1): rewrite this component as a 3-level tree.
 *
 * Level 1: Package name (block.package_name, falling back to "SciEasy Core"
 *          for builtins and "Custom" for Tier 1 drop-in blocks).
 * Level 2: Category within the package (block.category).
 * Level 3: Individual blocks (existing card).
 *
 * Requirements:
 *   - Packages and categories are both collapsible (useState per section).
 *   - "Custom" package always sorts to the BOTTOM of the palette.
 *   - Other packages sort alphabetically.
 *   - Categories within a package sort alphabetically.
 *   - Blocks within a category sort alphabetically.
 *   - Empty categories/packages are hidden.
 *   - Search/filter still works across all levels — when a query matches,
 *     parent sections expand automatically.
 *   - IO block expansion (expandIOBlocks) must still apply.
 *
 * See docs/design/stage-10-1-palette.md §3.2.2 for the full spec.
 */

interface BlockPaletteProps { ... }
// ... rest of file unchanged.
```

### 3.2 Part 2 (Agent B, next PR) — scope reference

Documented here so Agent B has a definitive target. Agent A does NOT implement
any of this.

#### 3.2.1 Full `_infer_category` body (Agent B)

```python
def _infer_category(cls: type) -> str:
    """Infer the block category.

    Resolution order:
    1. Explicit `category` ClassVar on the class, if non-empty
    2. Class-hierarchy inference (IOBlock -> "io", etc.)
    3. Fallback "unknown"

    Note: Tier 1 "Custom" assignment is NOT done here. It is applied in
    `_scan_tier1` after `_spec_from_class` returns, because it depends on
    knowing the block came from a drop-in directory — information
    `_infer_category` does not have.
    """
    explicit = getattr(cls, "category", "")
    if isinstance(explicit, str) and explicit:
        return explicit

    from scieasy.blocks.ai.ai_block import AIBlock
    from scieasy.blocks.app.app_block import AppBlock
    from scieasy.blocks.code.code_block import CodeBlock
    from scieasy.blocks.io.io_block import IOBlock
    from scieasy.blocks.process.process_block import ProcessBlock
    from scieasy.blocks.subworkflow.subworkflow_block import SubWorkflowBlock

    if issubclass(cls, IOBlock):
        return "io"
    if issubclass(cls, ProcessBlock):
        return "process"
    if issubclass(cls, CodeBlock):
        return "code"
    if issubclass(cls, AppBlock):
        return "app"
    if issubclass(cls, AIBlock):
        return "ai"
    if issubclass(cls, SubWorkflowBlock):
        return "subworkflow"
    return "unknown"
```

(Note: the duplicate `AIBlock` check in the current code is removed in
Agent B's version — dead code cleanup.)

#### 3.2.2 `_scan_tier1` Custom classification (Agent B)

Agent B applies Custom category after the class-based inference:

```python
# Inside _scan_tier1, after _spec_from_class:
block_spec = _spec_from_class(obj, source="custom")  # NB: value renamed in same commit
if not getattr(obj, "category", ""):
    # Only override when the block did not explicitly declare its category.
    block_spec.category = "Custom"
```

This preserves explicit category declarations (a drop-in block with
`category = "segmentation"` still shows under "segmentation", not "Custom").

#### 3.2.3 Source value rename (Agent B)

Atomic edit across:

- `src/scieasy/blocks/registry.py` (3 assignment sites + 1 comparison in `hot_reload`)
- `tests/blocks/test_registry.py` (2 assertions)
- `tests/integration/test_block_sdk_e2e.py` (5 assertions)

| Old | New |
|-----|-----|
| `"tier1"` | `"custom"` |
| `"entry_point"` | `"package"` |
| `"builtin"` | `"builtin"` (unchanged) |

#### 3.2.4 `_summary` population (Agent B)

```python
def _summary(spec: Any) -> BlockSummary:
    return BlockSummary(
        name=spec.name,
        type_name=spec.type_name,
        category=spec.category,
        description=spec.description,
        version=spec.version,
        input_ports=[_port_response(port, direction="input") for port in spec.input_ports],
        output_ports=[_port_response(port, direction="output") for port in spec.output_ports],
        source=spec.source,
        package_name=spec.package_name,
    )
```

#### 3.2.5 `BlockPalette.tsx` rewrite (Agent B)

- Two layers of `useState<Record<string, boolean>>` for expanded/collapsed state (packages and categories).
- A grouping function that produces `Array<{ packageName, categories: Array<{ category, blocks: BlockSummary[] }> }>`.
- Sort logic: `"Custom"` pinned last; other packages alphabetical; categories alphabetical; blocks alphabetical.
- Search filter that walks all three levels and auto-expands matching branches.
- Preserves `expandIOBlocks` behavior.

Package name derivation (frontend):

```ts
function derivePackageName(block: BlockSummary): string {
  if (block.source === "custom") return "Custom";
  if (block.package_name) return block.package_name;
  return "SciEasy Core"; // fallback for builtins and missing package_name
}
```

---

## 4. Test plan

### 4.1 Backend tests

**File**: `tests/blocks/test_registry.py`

Agent A adds skipped stubs. Agent B implements them (removing the skip marker).

| Test name | Assertion | Agent |
|-----------|-----------|-------|
| `test_explicit_category_classvar_wins` | A block class with `category = "segmentation"` registered via Tier 1 has `spec.category == "segmentation"` (explicit wins over Custom default) | B |
| `test_tier1_block_without_category_defaults_to_custom` | A Tier 1 drop-in block without a `category` ClassVar has `spec.category == "Custom"` | B |
| `test_tier2_block_without_category_uses_hierarchy_inference` | A Tier 2 entry-point block (no ClassVar) inherits the hierarchy category (e.g., ProcessBlock subclass -> `"process"`), NOT `"Custom"` | B |
| `test_spec_source_values` | `_scan_builtins` -> `"builtin"`, `_scan_tier1` -> `"custom"`, `_scan_tier2` -> `"package"` | B |
| `test_hot_reload_still_recognizes_custom_source` | `hot_reload` prunes stale Tier 1 specs (comparison updated to `spec.source == "custom"`) | B |

**File**: `tests/api/test_blocks.py`

| Test name | Assertion | Agent |
|-----------|-----------|-------|
| `test_list_blocks_includes_source_and_package_name` | `GET /api/blocks/` response items contain non-null `source` and `package_name` keys | B |
| `test_list_blocks_source_values_enumerated` | Response items have `source` in `{"builtin", "package", "custom"}` | B |

### 4.2 Frontend tests

**File**: `frontend/src/components/BlockPalette.test.tsx` (created in Part 1)

| Test name | Assertion | Agent |
|-----------|-----------|-------|
| `renders_three_level_tree` | When given mixed builtin/package/custom blocks, output contains package headers > category headers > block cards | B |
| `custom_package_sorts_last` | A block with `source === "custom"` appears below all other package sections | B |
| `packages_collapse_and_expand` | Clicking a package header toggles visibility of its child categories | B |
| `search_expands_matching_branches` | Searching for a block name auto-expands its parent package and category | B |
| `empty_categories_are_hidden` | If a category has no matching blocks (after filter), its header is not rendered | B |

### 4.3 Unit tests NOT required in Part 2

These are covered by the existing test suite and don't need new tests:

- Existing `test_scan_discovers_dropin` in `test_registry.py` already verifies the scan mechanism — Agent B only updates its assertions, not its structure.
- Existing `test_list_blocks_and_schema_alias_endpoints` in `test_blocks.py` already exercises the blocks API happy path.

---

## 5. Migration / compat notes

### 5.1 Source value rename

The rename from `"tier1"` -> `"custom"` and `"entry_point"` -> `"package"` is
**breaking** for any code that compared `BlockSpec.source` against the old
string literals. A search of the codebase (see §2.3 table) confirms all
consumers are internal:

- `registry.py::hot_reload` (1 site)
- `tests/blocks/test_registry.py` (2 sites)
- `tests/integration/test_block_sdk_e2e.py` (5 sites)

There is **no published API contract** that exposes these strings. The API
`BlockSummary` schema does not include `source` today (Agent A adds it in
Part 1; Agent B populates it with the new values in Part 2).

**No compatibility shim is needed.** Agent B will do an atomic rename in a
single commit. If any future caller appears after Part 2 lands, it should use
the new vocabulary from the start.

### 5.2 `BlockSummary` schema expansion

Adding `source: str = ""` and `package_name: str = ""` to the Pydantic model
is **additive and backward compatible**:

- Existing test constructors that don't pass these fields still validate (defaults)
- Existing TS consumers that don't read these fields still type-check (fields are optional `?`)
- Existing API consumers that parse `BlockSummary` JSON responses get the new fields as empty strings in Part 1 (before Agent B populates them)

### 5.3 `_infer_category` ClassVar check

Adding the ClassVar check at the top of `_infer_category` is a **pure
refinement**: any block that did NOT declare `category` falls through to the
existing hierarchy checks, matching today's behavior exactly.

### 5.4 `BlockPalette.tsx` 3-level rewrite

This is the highest-risk change in Part 2 because it rewrites rendered output.
Mitigation:

- Agent B adds component tests **before** the rewrite (they start as skipped stubs in Part 1)
- The existing flat grouping code is used as the reference for search/filter semantics
- The `expandIOBlocks` transformation is preserved verbatim

---

## 6. Out of scope (Part 1)

Agent A does NOT do any of the following in this PR. Agent B does them in Part 2.

| Work item | Scope | Why deferred |
|-----------|-------|--------------|
| Real `_infer_category` ClassVar check | Part 2 | Behavior change; needs new tests |
| Tier 1 "Custom" default assignment | Part 2 | Behavior change in `_scan_tier1` |
| `BlockSpec.source` value rename | Part 2 | Atomic rename touches registry + 7 test sites |
| Populating `source`/`package_name` in `_summary()` | Part 2 | Depends on rename landing first |
| Removing duplicate `AIBlock` check in `_infer_category` | Part 2 | Cleanup bundled with ClassVar refinement |
| `BlockPalette.tsx` 3-level tree rendering | Part 2 | Full rewrite; highest-risk diff |
| Unskipping the new test stubs | Part 2 | They target behavior Part 2 implements |
| Marking Stage 10.1 complete in ROADMAP_v0.3.md | Part 2 (end) | Only after all tests pass |
| CHANGELOG entry for Part 2 | Part 2 | Separate changelog entry per PR |

---

## 7. Acceptance criteria for Part 1

Part 1 (this PR) is done when:

1. `docs/design/stage-10-1-palette.md` exists and covers all sections above (≥ 200 lines, measurable)
2. `src/scieasy/blocks/base/block.py` has `category: ClassVar[str] = ""`
3. `src/scieasy/blocks/registry.py::_infer_category` has a TODO marker (body unchanged)
4. `src/scieasy/api/schemas.py::BlockSummary` has `source: str = ""` and `package_name: str = ""` fields
5. `src/scieasy/api/routes/blocks.py::_summary` has a TODO marker (body unchanged)
6. `frontend/src/types/api.ts::BlockSummary` has optional `source?`/`package_name?` fields
7. `frontend/src/components/BlockPalette.tsx` has a TODO comment block at the top (rendered output unchanged)
8. Skipped test stubs exist in `tests/blocks/test_registry.py`, `tests/api/test_blocks.py`, and `frontend/src/components/BlockPalette.test.tsx`
9. `pytest` runs green with skipped tests reported
10. `ruff check` and `ruff format --check` clean
11. `mypy src/scieasy/ --ignore-missing-imports` clean
12. `cd frontend && npx tsc -b --noEmit` clean
13. CI all green on the PR
14. Part 1 entry in CHANGELOG under `## [Unreleased]`

## 8. Acceptance criteria for Part 2

Documented here so Agent B has a clear target (Agent B will not change this
doc, only implement against it):

1. All skipped tests added in Part 1 pass (not skipped)
2. `_infer_category` honors `category` ClassVar override
3. `_scan_tier1` sets `spec.category = "Custom"` when the class did not declare one
4. `BlockSpec.source` values are `"builtin"`, `"custom"`, `"package"` — all old callers updated
5. `GET /api/blocks/` response items include populated `source` and `package_name` fields
6. `BlockPalette.tsx` renders the 3-level tree with Custom pinned at the bottom
7. Search/filter still works
8. CI green
9. ROADMAP_v0.3.md Stage 10.1 checkboxes marked complete
10. Part 2 CHANGELOG entry

---

## 9. Open questions

None blocking. The following are minor and can be resolved during Part 2:

1. Should package-name fallback for builtins be `"SciEasy Core"` literally, or configurable? (Recommendation: literal; Agent B can expose a constant at the top of `BlockPalette.tsx`.)
2. Should the duplicate `AIBlock` check in `_infer_category` be cleaned up as part of Part 2 or tracked as a separate issue? (Recommendation: clean up in Part 2 since the function is already being edited.)
3. Are there any entry-point packages installed in CI whose tests would exercise the `"package"` source value? (Not critical; existing mock-based tests in `tests/integration/test_block_sdk_e2e.py` cover this path.)
