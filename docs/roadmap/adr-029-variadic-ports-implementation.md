# ADR-029 Variadic Ports -- Implementation Roadmap

**ADR**: [ADR-029: Variadic port count and per-instance port editor](../adr/ADR.md#adr-029)
**Issue**: #297 (ADR-029 original), #569 (this roadmap)
**Date**: 2026-04-11
**Status**: Planning (ADR-029 promoted from draft to proposed)

---

## 1. Overview

ADR-029 defines variadic port architecture: blocks whose input and output port
count is determined per-instance at edit time rather than fixed at class
definition time. The first consumers are **AIBlock**, **CodeBlock**, and
**AppBlock**.

Key decisions from the promoted ADR-029:

| D# | Decision |
|----|----------|
| D1 | Port list stored in `self.config["input_ports"]` / `self.config["output_ports"]` as `[{"name": "...", "types": ["Image"]}]` |
| D2 | Canvas node `[+]` button + Bottom Panel port editor table; CodeBlock Python auto-inference; port deletion clears edges with confirmation |
| D3 | Validation treats variadic ports identically to static (standard type check) |
| D4 | No scheduler change |
| D5 | Worker reconstruction unchanged, payload self-describes via `type_chain` |
| D6 | No palette change |
| D7 | CodeBlock hybrid: Python auto-infer from signature, R/Julia/inline manual |
| D8 | `BlockSpec` gains `variadic_inputs: bool` + `variadic_outputs: bool` |
| D9 | `dynamic_ports` and variadic are independent, defer composition |
| D10 | Payload format unchanged |
| D11 | Block author declares `allowed_input_types` / `allowed_output_types` ClassVar, default `[DataObject]` |
| D12 | Port editor config schema injected via ADR-030 MRO merge pattern |
| D13 | Multiple same-type ports for parallel branch fan-in (natural, no extra work) |

---

## 2. Ticket Summary

| Ticket | Title | Layer | Estimated Complexity |
|--------|-------|-------|---------------------|
| **B1** | Block ABC + BlockSpec + Registry + API schema | Backend | L |
| **B2** | MRO injection -- port editor config_schema | Backend | S |
| **B3** | CodeBlock Python signature auto-inference | Backend | M |
| **F1** | Canvas node `[+]` button + port deletion with edge cleanup | Frontend | M |
| **F2** | Bottom Panel port editor table | Frontend | M |
| **C1** | AIBlock -- enable variadic, implement LLM multi-port run() | Consumer | M |
| **C2** | CodeBlock -- enable variadic, adapt runners | Consumer | L |
| **C3** | AppBlock -- enable variadic, adapt exchange serialization | Consumer | M |

---

## 3. Dependency Graph

```
            B2 (MRO injection)
           /                  \
  B1 (ABC+Spec+Registry) ------+-----> F1 (canvas [+] button)
           |                   |            |
           |                   |            v
           |                   +-----> F2 (bottom panel editor)
           |                                |
           v                                v
  B3 (CodeBlock introspect)       C1 (AIBlock consumer)
           |                      C2 (CodeBlock consumer)
           |                      C3 (AppBlock consumer)
           v
     C2 depends on B3 also
```

**Parallelization opportunities**:
- B1 and B2 can run in parallel (B2 only touches `config_schema`, B1 touches `BlockSpec`/ports)
- F1 and F2 can run in parallel once B1 is merged
- C1, C2, C3 can run in parallel once B1 + F1 are merged (C2 also needs B3)

**Critical path**: B1 -> F1 -> C1/C2/C3

---

## 4. Per-Ticket Detail

---

### B1: Block ABC + BlockSpec + Registry + API Schema

**Goal**: Add the 4 new ClassVars to Block, update `get_effective_*_ports()` to
read from `self.config`, update `BlockSpec` and `BlockSchemaResponse`, update
`_spec_from_class()`.

#### Files to modify

| File | Changes |
|------|---------|
| `src/scieasy/blocks/base/block.py` | Add 4 ClassVars (lines 55-56 area): `variadic_inputs: ClassVar[bool] = False`, `variadic_outputs: ClassVar[bool] = False`, `allowed_input_types: ClassVar[list[type]] = [DataObject]`, `allowed_output_types: ClassVar[list[type]] = [DataObject]`. Update `get_effective_input_ports()` (line 104-117) and `get_effective_output_ports()` (line 119-128) to check `self.config.get("input_ports")` / `self.config.get("output_ports")` when variadic is True and build port list from config dicts. |
| `src/scieasy/blocks/base/ports.py` | No structural changes needed. The existing `InputPort`/`OutputPort` dataclasses (lines 12-34) work as-is. Add a helper function `ports_from_config_dicts(dicts: list[dict], direction: str) -> list[InputPort] | list[OutputPort]` to convert `[{"name": "...", "types": ["Image"]}]` to port objects, resolving type names via the type registry. |
| `src/scieasy/blocks/registry.py` | **`BlockSpec` dataclass** (line 28-55): Add `variadic_inputs: bool = False` and `variadic_outputs: bool = False` fields. **`_spec_from_class()`** (line 575-602): Read new ClassVars and populate spec fields. No changes to `_merge_config_schema()` (that's B2). No changes to `_validate_dynamic_ports()`. |
| `src/scieasy/api/schemas.py` | **`BlockSummary`** (line 84-101): Add `variadic_inputs: bool = False` and `variadic_outputs: bool = False`. **`BlockSchemaResponse`** (line 110-123): Add `allowed_input_types: list[str] = Field(default_factory=list)` and `allowed_output_types: list[str] = Field(default_factory=list)` so the frontend knows which types to offer in the port-type dropdown. |
| `src/scieasy/api/routes.py` (or wherever `_summary()` / block schema endpoint lives) | Update the BlockSpec-to-response mapping to include new fields. Also pass `allowed_input_types` / `allowed_output_types` as string lists (class names). |
| `frontend/src/types/api.ts` | **`BlockSummary`** (line 60-74): Add `variadic_inputs?: boolean` and `variadic_outputs?: boolean`. **`BlockSchemaResponse`** (line 109-133): Add `allowed_input_types?: string[]` and `allowed_output_types?: string[]`. |

#### New files

| File | Purpose |
|------|---------|
| (none) | All changes fit in existing files |

#### Test files to modify/create

| File | Tests |
|------|-------|
| `tests/blocks/test_block_base.py` | Test `get_effective_input_ports()` reads from config when `variadic_inputs=True`. Test that static blocks are unaffected. |
| `tests/blocks/test_registry.py` | Test `_spec_from_class()` populates `variadic_inputs`/`variadic_outputs` from ClassVars. |
| `tests/blocks/test_ports.py` | Test `ports_from_config_dicts()` helper converts dict list to port objects, including type name resolution. |
| `tests/blocks/test_dynamic_ports.py` | Extend to verify variadic and `dynamic_ports` do not interfere (D9). |

#### Key implementation details

The `get_effective_input_ports()` override logic (block.py line 104-117):

```python
def get_effective_input_ports(self) -> list[InputPort]:
    if type(self).variadic_inputs:
        config_ports = self.config.get("input_ports")
        if config_ports and isinstance(config_ports, list):
            return ports_from_config_dicts(config_ports, "input")
    return list(type(self).input_ports)
```

The `ports_from_config_dicts()` helper must resolve type name strings
(e.g., `"Image"`) to actual Python classes via the core type registry.
This is the same resolution path used by `_reconstruct_one()` in the
worker subprocess (ADR-027 Addendum 1). Reuse
`scieasy.core.types.registry.resolve_type_name()` or equivalent.

Each config port dict shape: `{"name": str, "types": list[str]}`.
`types` maps to `accepted_types` on the `InputPort`/`OutputPort`.

**Complexity**: L -- touches 6+ files across backend and frontend types,
is the foundation for all other tickets.

---

### B2: MRO Injection -- Port Editor Config Schema

**Goal**: AIBlock, CodeBlock, and AppBlock base classes declare port-editor
fields in their `config_schema`. The ADR-030 `_merge_config_schema()` pattern
ensures leaf classes inherit them automatically.

#### Files to modify

| File | Changes |
|------|---------|
| `src/scieasy/blocks/ai/ai_block.py` | Add `input_ports` and `output_ports` properties to `config_schema["properties"]` (line 61-106 area). Schema shape: `"input_ports": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "types": {"type": "array", "items": {"type": "string"}}}}, "default": [], "title": "Input Ports", "ui_widget": "port_editor"}`. Same for `output_ports`. |
| `src/scieasy/blocks/code/code_block.py` | Same pattern as AIBlock -- add `input_ports` and `output_ports` to `config_schema["properties"]` (line 51-71 area). |
| `src/scieasy/blocks/app/app_block.py` | Same pattern -- add to `config_schema["properties"]` (line 68-87 area). |

No changes to `_merge_config_schema()` itself (it already handles MRO
merge correctly per ADR-030). The new port editor fields simply appear
in the merged schema because the base classes declare them.

#### New files

None.

#### Test files

| File | Tests |
|------|-------|
| `tests/blocks/test_block_config_schema.py` | Test that `_merge_config_schema(AIBlock)` includes `input_ports` and `output_ports` properties. Same for CodeBlock, AppBlock. |

**Complexity**: S -- repetitive schema declaration across 3 files.

---

### B3: CodeBlock Python Signature Auto-Inference

**Goal**: When a CodeBlock has `language="python"` and `mode="script"`, parse
the script's `run()` function signature to auto-populate the variadic port
config. Type annotations on parameters become port types; parameter names
become port names.

#### Files to modify

| File | Changes |
|------|---------|
| `src/scieasy/blocks/code/introspect.py` | **`introspect_script()`** (line 10-49): Extend the return dict to include `"input_ports": list[dict]` and `"output_ports": list[dict]` derived from `run()` parameters and return type annotation. **`_extract_params()`** (line 52-78): Already extracts param names and annotations. Add a new function `_params_to_port_dicts(params: list[dict]) -> list[dict]` that maps annotation strings (e.g., `"Name(id='Image')"` from `ast.dump`) to port dict format `{"name": "...", "types": ["Image"]}`. For return type, parse `-> dict[str, Image]` or `-> tuple[Image, DataFrame]` style annotations. |
| `src/scieasy/blocks/code/code_block.py` | Add a method or hook that calls `introspect_script()` when script_path changes and updates `self.config["input_ports"]`/`self.config["output_ports"]`. This could be triggered from the frontend via a "re-infer ports" button or automatically on config change. |

#### New helper

Consider adding `src/scieasy/blocks/code/port_inference.py` if the
inference logic grows large. Otherwise keep in `introspect.py`.

#### Annotation mapping rules

| Python annotation | Port type |
|-------------------|-----------|
| `image: Image` | `["Image"]` |
| `data: DataFrame` | `["DataFrame"]` |
| `x: DataObject` | `["DataObject"]` (any type) |
| `x` (no annotation) | `["DataObject"]` (fallback) |
| `-> dict[str, DataFrame]` | Single output port per dict key (requires runtime introspection -- defer) |
| `-> Image` | Single output port `result` with type `["Image"]` |

For the MVP, focus on **input** parameter inference. Output inference from
return-type annotations is useful but harder (dict keys are runtime values).
The user can always manually configure output ports via the port editor.

#### Test files

| File | Tests |
|------|-------|
| `tests/blocks/test_introspect.py` (new) | Test `introspect_script()` with annotated `run()` function returns correct `input_ports` dicts. Test unannotated params fall back to `DataObject`. Test `configure()` schema extraction still works. |

**Complexity**: M -- AST parsing is tricky, but the existing `introspect.py`
infrastructure handles most of it. The annotation-to-type-name mapping is the
novel part.

---

### F1: Canvas Node `[+]` Button + Port Deletion with Edge Cleanup

**Goal**: For blocks where `variadic_inputs` or `variadic_outputs` is true,
render a `[+]` button below the last port handle on each side. Clicking `[+]`
adds a new port with a default name and type. Each variadic port handle gets a
small `[x]` delete affordance. Deleting a port removes associated edges
(with confirmation dialog).

#### Files to modify

| File | Changes |
|------|---------|
| `frontend/src/components/nodes/BlockNode.tsx` | **Port handle rendering** (lines 715-762): After the existing `effectiveInputPorts.map(...)` and `effectiveOutputPorts.map(...)` blocks, conditionally render a `[+]` button when `data.schema?.variadic_inputs` / `data.schema?.variadic_outputs` is true. For each variadic port handle, render a small `[x]` button on hover. Wire `[+]` to call `data.onAddPort?.(direction)` and `[x]` to call `data.onRemovePort?.(direction, portName)`. These callbacks must propagate to the parent component which updates the node config and cleans up edges. |
| `frontend/src/types/ui.ts` | **`BlockNodeData`**: Add `onAddPort?: (direction: "input" \| "output") => void` and `onRemovePort?: (direction: "input" \| "output", portName: string) => void` callbacks. |
| `frontend/src/components/Canvas.tsx` (or wherever nodes are wired) | Implement `onAddPort` and `onRemovePort` handlers: update the node's `config.input_ports` / `config.output_ports` array, persist via `onUpdateConfig`, and for `onRemovePort` also filter edges that reference the deleted port name. Show a confirmation dialog before deleting a port that has connected edges. |

#### New files

None expected. If the port handle rendering grows complex, consider
extracting a `VariadicPortHandle.tsx` component.

#### Test files

| File | Tests |
|------|-------|
| Frontend unit tests (if framework supports) | Test that `[+]` button appears only for variadic blocks. Test that clicking `[+]` calls `onAddPort`. Test that `[x]` on a port with edges shows confirmation. |

#### Visual design notes

- The `[+]` button should match the existing port handle style (14px circle)
  but with a plus icon and slightly muted color.
- Position: below the last port handle on each side, offset by the same 20px
  spacing used between ports (see BlockNode.tsx line 734: `top: 80 + index * 20`).
- The `[x]` button appears on hover over a variadic port handle, positioned
  just inside the node boundary.

**Complexity**: M -- mostly React event wiring and visual polish, but edge
cleanup logic requires careful integration with React Flow's edge state.

---

### F2: Bottom Panel Port Editor Table

**Goal**: In the Bottom Panel Config tab, render a table for editing variadic
ports when the selected block has `variadic_inputs` or `variadic_outputs`.
Each row shows: port name (editable text), port type (dropdown from
`allowed_input_types` / `allowed_output_types`), and a delete button.

#### Files to modify

| File | Changes |
|------|---------|
| `frontend/src/components/BottomPanel.tsx` | **`ConfigPanel` component** (line 33-99): After the existing `ordered.map(...)` loop that renders config fields, check if the schema has `variadic_inputs` or `variadic_outputs`. If so, render a `PortEditorTable` component below the config fields. The table reads from `selectedNode.config.input_ports` / `selectedNode.config.output_ports` and writes back via `onUpdateConfig`. |
| `frontend/src/components/PortEditorTable.tsx` (new) | Extracted component for the port editor table. Props: `ports: {name: string, types: string[]}[]`, `allowedTypes: string[]`, `direction: "input" \| "output"`, `onChange: (ports) => void`. Renders: header row, one row per port (name input, type dropdown, delete button), footer row with "Add port" button. |
| `frontend/src/types/api.ts` | Already updated in B1 with `allowed_input_types` / `allowed_output_types`. |

#### New files

| File | Purpose |
|------|---------|
| `frontend/src/components/PortEditorTable.tsx` | Reusable port editor table component |

#### Test files

| File | Tests |
|------|-------|
| Frontend tests | Test table renders correct number of rows. Test adding a row. Test changing a port name. Test type dropdown options match `allowedTypes`. Test deleting a row. |

**Complexity**: M -- straightforward table UI, but needs to handle edge
cases (duplicate port names, empty names, type dropdown population).

---

### C1: AIBlock -- Enable Variadic + Multi-Port Run

**Goal**: Set `variadic_inputs = True` and `variadic_outputs = True` on
`AIBlock`. Update `run()` to iterate over all input ports, serialize each
into the prompt, and produce outputs for each declared output port.

#### Files to modify

| File | Changes |
|------|---------|
| `src/scieasy/blocks/ai/ai_block.py` | **ClassVars** (line 34-41 area): Add `variadic_inputs: ClassVar[bool] = True`, `variadic_outputs: ClassVar[bool] = True`, `allowed_input_types: ClassVar[list[type]] = [DataObject]`, `allowed_output_types: ClassVar[list[type]] = [Text, DataFrame, Array, Artifact]`. **`input_ports`** (line 43-51): Keep as default template ports (shown in palette per D6). **`run()`** (line 108-168): Rewrite to read `self.get_effective_input_ports()` for port names, iterate all input ports to serialize data, build prompt with all inputs, call LLM, parse response into multiple output ports. The response parsing needs a convention -- e.g., structured JSON output from LLM where keys match output port names. |
| `src/scieasy/blocks/ai/ai_block.py` | **`_serialize_input()`** (line 170-187): Update to accept a dict of named inputs (one per variadic port) and produce a structured representation where each input is labelled by port name for the LLM context. |

#### Key design question for run()

The current `run()` returns `{"result": text}` -- a single output. With
variadic outputs, the LLM response must be parsed into multiple named
outputs. Two approaches:

1. **Structured JSON output**: The prompt instructs the LLM to return JSON
   with keys matching output port names. `run()` parses JSON and wraps each
   value in the appropriate DataObject type.
2. **Single text output always**: Regardless of output port count, the LLM
   returns text. The block author must manually split into ports via
   post-processing.

Recommend approach 1 for MVP, with fallback to approach 2 (all text goes to
first output port) when JSON parsing fails.

#### Test files

| File | Tests |
|------|-------|
| `tests/blocks/test_ai_block.py` (new or extend existing) | Test `AIBlock` with variadic config produces correct effective ports. Test `run()` with multiple input ports serializes all. Test `run()` output is distributed to declared output ports. Mock LLM provider. |

**Complexity**: M -- the multi-port `run()` rewrite is the hard part; the
ClassVar additions are trivial.

---

### C2: CodeBlock -- Enable Variadic + Adapt Runners

**Goal**: Set `variadic_inputs = True` and `variadic_outputs = True` on
`CodeBlock`. Update `_unpack_inputs()` and `_repack_outputs()` to handle
arbitrary port names. For Python scripts, integrate B3 auto-inference.

#### Files to modify

| File | Changes |
|------|---------|
| `src/scieasy/blocks/code/code_block.py` | **ClassVars** (line 39-41 area): Add `variadic_inputs: ClassVar[bool] = True`, `variadic_outputs: ClassVar[bool] = True`, `allowed_input_types: ClassVar[list[type]] = [DataObject]`, `allowed_output_types: ClassVar[list[type]] = [DataObject]`. **`input_ports`/`output_ports`** (line 45-50): Keep as default template (one `data` input, one `result` output). **`_unpack_inputs()`** (line 75-95): Already handles arbitrary dict keys -- no change needed, works as-is for variadic ports. **`_repack_outputs()`** (line 97-116): Already handles arbitrary dict keys -- no change needed. **`run()`** (line 120-163): The `unpacked` dict will have keys matching variadic port names instead of just `"data"`. The runner receives this dict as-is, so `execute_inline()` and `execute_script()` already support arbitrary input names. No runner change needed. |
| `src/scieasy/blocks/code/runners/python_runner.py` | Verify `execute_inline()` and `execute_script()` pass arbitrary input dict keys to the user script namespace. The user script's `run()` function receives keyword arguments matching port names. |
| `src/scieasy/blocks/code/runners/r_runner.py` | Verify R runner passes arbitrary named inputs. Since R scripts receive named variables, this should work if the runner uses port names as R variable names. |
| `src/scieasy/blocks/code/code_block.py` | Add a `get_effective_input_ports()` override (or rely on B1's base class logic) that also calls `introspect_script()` from B3 when `language="python"` and `mode="script"` and `config["input_ports"]` is empty. This is the auto-inference trigger. |

#### Integration with B3

When a Python CodeBlock has `mode="script"` and the user has not manually
configured ports, `get_effective_input_ports()` can call
`introspect_script(config["script_path"])` and return the inferred ports.
This means the port list is derived from the script source, not from
`config["input_ports"]`. The user can override by manually editing ports
in the port editor (which writes to `config["input_ports"]` and takes
precedence over inference).

Priority order for port resolution:
1. `config["input_ports"]` (manual override via port editor)
2. `introspect_script()` result (Python auto-inference)
3. Class-level `input_ports` ClassVar (static default)

#### Test files

| File | Tests |
|------|-------|
| `tests/blocks/test_code_block.py` | Test CodeBlock with variadic config. Test `_unpack_inputs` with multi-port dict. Test `_repack_outputs` with multi-port dict. Test auto-inference from Python script signature. |
| `tests/blocks/test_runners_subprocess.py` | Test Python runner with multi-port inputs produces multi-port outputs. |

**Complexity**: L -- the runner integration and auto-inference fallback
chain add significant surface area. The `_unpack_inputs`/`_repack_outputs`
code is already generic, which helps.

---

### C3: AppBlock -- Enable Variadic + Adapt Exchange Serialization

**Goal**: Set `variadic_inputs = True` and `variadic_outputs = True` on
`AppBlock`. Update input serialization to write one file per input port in
the exchange directory. Update output collection to group output files into
named output ports.

#### Files to modify

| File | Changes |
|------|---------|
| `src/scieasy/blocks/app/app_block.py` | **ClassVars** (line 55-60 area): Add `variadic_inputs: ClassVar[bool] = True`, `variadic_outputs: ClassVar[bool] = True`, `allowed_input_types: ClassVar[list[type]] = [DataObject]`, `allowed_output_types: ClassVar[list[type]] = [Artifact]`. **`run()`** (line 89-180): The input unpacking loop (lines 118-123) already iterates `inputs.items()` with arbitrary keys -- this works for variadic ports. The output collection (lines 169-180) currently creates a single `"result"` key. Update to: (a) if the block has variadic output ports declared, attempt to match output files to port names by pattern or subdirectory convention; (b) fallback: all output files go to first output port. |
| `src/scieasy/blocks/app/bridge.py` | **`prepare()`**: Currently serializes inputs into the exchange directory. Verify it handles arbitrary port names as subdirectory names (e.g., `exchange/inputs/port_name/file.tif`). **`collect()`**: Update to return a dict keyed by output port name if subdirectories match port names. |
| `src/scieasy/blocks/app/watcher.py` | May need to watch multiple subdirectories (one per output port) if the exchange protocol uses per-port subdirectories. Alternatively, keep watching a single output directory and group files by naming convention. |

#### Exchange directory convention for variadic ports

Proposed layout:
```
exchange/
  inputs/
    image_1/
      data.tif
    image_2/
      data.tif
  outputs/
    denoised/
      result.tif
    stats/
      result.csv
```

Output port mapping: subdirectory name matches declared output port name.
If no subdirectories exist, all files map to the first output port (backward
compatible with existing single-port AppBlock behavior).

#### Test files

| File | Tests |
|------|-------|
| `tests/blocks/test_app_block.py` | Test AppBlock with variadic config produces correct effective ports. Test multi-port input serialization to exchange directory. Test multi-port output collection from subdirectories. Test backward compatibility (single-port still works). |

**Complexity**: M -- the exchange directory layout is the novel part; the
`run()` loop is already generic.

---

## 5. Risk Assessment

### High risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Port name collisions**: User creates two ports with the same name | Validation errors, edge routing confusion | Frontend port editor must enforce unique names per direction. Backend `ports_from_config_dicts()` validates uniqueness. |
| **Type name resolution failure**: User-typed port type string does not match any registered DataObject subclass | Port creation fails silently or with cryptic error | `ports_from_config_dicts()` must validate type names against the registry and return clear errors. Frontend dropdown should only offer registered types. |
| **Workflow YAML round-trip**: Port config stored in `self.config` may not serialize/deserialize cleanly through YAML | Ports lost on workflow reload | Explicit test: save workflow with variadic block, reload, verify ports preserved. The existing config serialization path (Pydantic + YAML) should handle `list[dict]` natively, but needs verification. |

### Medium risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Edge cleanup on port deletion**: Deleting a port must remove all edges connected to it | Orphan edges, validation failures | F1 must integrate with React Flow's edge state management. Use `getEdges().filter()` to find affected edges. |
| **CodeBlock auto-inference fragility**: AST parsing of annotations depends on user writing valid type hints | Inference fails silently, falls back to `DataObject` | Make fallback behavior explicit in UI ("inferred" vs "manual" badge). Log warnings on parse failure. |
| **AppBlock exchange directory convention**: External apps may not respect subdirectory layout | Outputs not matched to ports | Keep backward-compatible single-directory fallback. Document the convention for app developers. |

### Low risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Scheduler unchanged (D4)**: Assumption that scheduler reads effective ports dynamically | Works because scheduler already uses `get_effective_*_ports()` per Addendum 1 | Verify with integration test. |
| **Payload format unchanged (D10)**: Worker reconstruction uses `type_chain` from payload | Already works for dynamic-type blocks (LoadData/SaveData) | Verify with round-trip test. |

---

## 6. Suggested Execution Order

### Wave 1 (parallel)

| Agent | Ticket | Dependencies |
|-------|--------|-------------|
| Agent A | **B1**: Block ABC + BlockSpec + Registry + API | None |
| Agent B | **B2**: MRO injection -- config_schema | None (independent of B1) |

### Wave 2 (parallel, after B1 merges)

| Agent | Ticket | Dependencies |
|-------|--------|-------------|
| Agent C | **B3**: CodeBlock Python signature auto-inference | B1 (for port dict format) |
| Agent D | **F1**: Canvas node `[+]` button | B1 (for `variadic_inputs`/`variadic_outputs` on schema) |
| Agent E | **F2**: Bottom Panel port editor table | B1 (for `allowed_*_types` on schema) |

### Wave 3 (parallel, after B1 + F1 + F2 merge)

| Agent | Ticket | Dependencies |
|-------|--------|-------------|
| Agent F | **C1**: AIBlock consumer | B1, B2, F1, F2 |
| Agent G | **C2**: CodeBlock consumer | B1, B2, B3, F1, F2 |
| Agent H | **C3**: AppBlock consumer | B1, B2, F1, F2 |

### Estimated total duration

- Wave 1: 1 session (B1 is the longest, ~L complexity)
- Wave 2: 1 session (all M complexity, parallel)
- Wave 3: 1 session (all M-L complexity, parallel)
- **Total: 3 sequential sessions with maximum parallelization**

---

## 7. Post-Implementation Verification

After all tickets merge:

1. **E2E test**: Create a workflow with an AIBlock (3 inputs, 2 outputs),
   a CodeBlock (2 inputs from Python script, 3 outputs), and an AppBlock
   (2 inputs, 2 outputs via exchange directory). Connect them. Run the workflow.
   Verify all data flows correctly.

2. **Backward compatibility**: Existing workflows with static-port blocks
   must load and run identically. Run the existing test suite.

3. **ADR-029 promotion**: After E2E passes, update ADR-029 status from
   `proposed` to `accepted` in `docs/adr/ADR.md`.

4. **Documentation**: Update `docs/guides/block-sdk.md` with a "Writing a
   Variadic Block" section. Update `docs/architecture/ARCHITECTURE.md`
   with the variadic port architecture details.
