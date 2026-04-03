# MANDATORY: Source-First Documentation & Testing Policy

**This section is NON-NEGOTIABLE. Violations cause silent, hard-to-detect errors.**

---

## Rule 1: NEVER Write From Memory

When producing ANY document that references code (tests, specs, architecture docs, ADRs, roadmaps, changelogs), you MUST read the actual source files using tools BEFORE writing. Do NOT rely on training data, conversation context, or assumptions about API signatures.

Specifically, before writing any of the following, you MUST `cat` or `read` the relevant source file first:

- Class names, constructor parameters, or attribute names
- Function/method signatures (parameter names, types, defaults)
- Import paths (`scieasy.xxx.yyy`)
- File paths in the project tree
- Enum values, ClassVar definitions, dataclass fields
- Property vs method distinction (i.e., `obj.name` vs `obj.name()`)

---

## Rule 2: Cite What You Read

Every code snippet in a document MUST include a source comment:

```python
# Source: scieasy/data/types.py L23-35
img = Image(data=np.zeros((64, 64)))
```

If you cannot point to a specific source file and line range, you have not verified it — do NOT write it.

---

## Rule 3: Test Code Must Be Executable

- NEVER write Python code snippets in Markdown that have not been verified against actual source.
- Prefer writing `tests/test_*.py` files over Markdown code blocks. Pytest files are validated by CI; Markdown is not.
- If a Markdown test plan is required, separate it into:
  - **Machine-verifiable parts** → `tests/test_*.py` (API correctness, imports, signatures)
  - **Human-judgment parts** → `*-human-checklist.md` (UX, visual layout, workflow feel) with NO code snippets

---

## Rule 4: Commit Message Traceability

Any commit that adds or modifies documentation MUST list the source files that were read in the commit message body:

```
docs: update Phase 3 test plan

Verified against:
- scieasy/data/types.py
- scieasy/storage/backends.py
- scieasy/lineage/store.py
```

---

## CI Enforcement: doc-lint

The Workflow Gate CI runs `doc-lint` on every PR. It will:

1. Extract all Python code blocks from changed `.md` files
2. Run `ast.parse()` and import validation against the actual codebase
3. Scan all `scieasy.*` references and verify they resolve to real modules/classes/functions
4. **Fail the PR** if any reference is fabricated

Do not attempt to guess and fix later. Read first, write second. Always.

---

## Document-Type Specific Validation

| Document Type    | What Gets Validated                              | How                                        |
| ---------------- | ------------------------------------------------ | ------------------------------------------ |
| Test docs        | Code block syntax, imports, API signatures       | `pytest --collect-only` or `ast.parse()`   |
| ARCHITECTURE.md  | Module/file path references actually exist        | Script scans all `scieasy.*`, checks tree  |
| ROADMAP.md       | Referenced Issue numbers exist                   | GitHub API check                           |
| ADR.md           | Class/function names mentioned exist in codebase | AST scan + grep                            |
| PROJECT_TREE.md  | File tree matches actual repo structure          | `diff` against `find` output               |
