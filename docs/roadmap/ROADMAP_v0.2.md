# SciEasy — Roadmap v0.2

> **Scope**: ADR-024, ADR-025, ADR-026 — frontend bundling, entry-points protocol,
> and Block SDK.
>
> **Guiding rule**: each phase produces something testable. No phase is
> "write a bunch of code and hope it works at the end." Every phase ends with
> a green CI.
>
> **Prerequisite**: Roadmap v0.1 (Phases 0–2) completed. The interface skeleton,
> architecture tests, and CI pipeline are already in place. PR #160 (API runtime +
> frontend editor) is merged.

---

## Phase 1 — Frontend bundling and `scieasy gui` (ADR-024)

**Goal**: a user can `pip install scieasy` and run `scieasy gui` to open the full
GUI in their browser — no Node.js required. The frontend is pre-built and served
from the Python wheel.

### 1.1 SPA fallback middleware

- [ ] Create `src/scieasy/api/spa.py` — `SPAStaticFiles` subclass of `StaticFiles`
  - Returns `index.html` for any path not matching a real file
  - Required for deep SPA routes like `/projects/123/workflows`
  - ~30 lines
- [ ] Test: `/api/...` routes are NOT intercepted by SPA fallback
- [ ] Test: `/ws` is NOT intercepted by SPA fallback
- [ ] Test: unknown paths like `/projects/foo` return `index.html`
- [ ] Test: static assets (`/assets/main.js`) are served directly

### 1.2 API app static file mount

- [ ] Update `src/scieasy/api/app.py`:
  - Import `SPAStaticFiles` from `spa.py`
  - Mount static files at the END of `create_app()` (after all routers and WebSocket)
  - Conditional: only mount if `api/static/` directory exists (dev mode has no static dir)
- [ ] Test: `create_app()` does NOT mount static files when `api/static/` is absent (development mode)
- [ ] Test: `create_app()` mounts static files when `api/static/` exists

### 1.3 `scieasy gui` CLI command

- [ ] Add `gui` command to `src/scieasy/cli/main.py`:
  - `--port` option (default 8000)
  - `--no-browser` flag
  - Starts uvicorn with `create_app` factory
  - Opens browser via `threading.Timer(1.5, webbrowser.open, [url])`
- [ ] Update existing `serve` command: replace placeholder echo with actual uvicorn start
- [ ] Test: `scieasy gui --help` prints usage
- [ ] Test: `--no-browser` starts uvicorn (mock `uvicorn.run`, verify called with correct args)
- [ ] Test: default port is 8000

### 1.4 Vite configuration for relative paths

- [ ] Update `frontend/vite.config.ts`:
  - Set `base: "./"` to ensure all asset paths in built output are relative
  - Verify: `npm run build` produces `dist/index.html` with relative script/style references
- [ ] Update `frontend/package.json` if build script needs adjustment

### 1.5 Build and packaging configuration

- [ ] Update `pyproject.toml`:
  - Add `[tool.setuptools.package-data]` section: `scieasy = ["api/static/**/*"]`
  - Ensures pre-built frontend is included in the wheel
- [ ] Add `src/scieasy/api/static/` to `.gitignore`
  - Prevent committing build artifacts; developers use `npm run dev`
- [ ] Update `.github/workflows/ci.yml`:
  - Add `build-frontend` job (runs on release tags only): `cd frontend && npm ci && npm run build && cp -r dist/ ../src/scieasy/api/static/`
  - Add `needs: build-frontend` to wheel/publish job

### Verification gate

- [ ] In development (no `api/static/`): `scieasy serve` starts API without frontend errors
- [ ] With mock static dir: `scieasy gui --no-browser` starts server, `/` serves `index.html`, `/api/blocks` still works
- [ ] `make lint` passes
- [ ] `make typecheck` passes
- [ ] `make test` passes — all new tests green
- [ ] CI green ✅

### Deliverable

```
pip install scieasy
scieasy gui
→ Browser opens with full workflow editor.
No Node.js required. API and frontend served from the same process.
```

---

## Phase 2 — Entry-points protocol and registry refactoring (ADR-025)

**Goal**: external block packages can register blocks, types, and adapters via
the callable entry-points protocol. The block palette displays two-level
categorization (package → category → block). `PackageInfo` metadata is
available to the GUI.

### 2.1 `PackageInfo` dataclass

- [ ] Create `src/scieasy/blocks/base/package_info.py`:
  - `PackageInfo` dataclass with fields: `name: str`, `description: str = ""`, `author: str = ""`, `version: str = "0.1.0"`
  - Kept in separate file to avoid circular imports when external packages import it
- [ ] Update `src/scieasy/blocks/base/__init__.py`:
  - Import and re-export `PackageInfo`
  - Add `"PackageInfo"` to `__all__`

### 2.2 BlockRegistry callable protocol

- [ ] Update `src/scieasy/blocks/registry.py`:
  - Add `package_name: str = ""` field to `BlockSpec` dataclass
  - Add `self._packages: dict[str, PackageInfo] = {}` to `BlockRegistry.__init__()`
  - Rewrite `_scan_tier2()`: load entry-point callable, invoke it, detect return type:
    - If `tuple(PackageInfo, list)`: extract package info, register each block with `spec.package_name = info.name`
    - If plain `list`: use `ep.name` as fallback package name
  - Add `logger.warning(...)` in all exception handlers
  - Add `packages() -> dict[str, PackageInfo]` method
  - Add `specs_by_package() -> dict[str, list[BlockSpec]]` method
- [ ] Test: `_scan_tier2` with `(PackageInfo, [BlockClass])` populates `package_name` on BlockSpec
- [ ] Test: `_scan_tier2` with plain `[BlockClass]` uses entry-point name as `package_name`
- [ ] Test: `specs_by_package()` returns correctly grouped dict
- [ ] Test: `packages()` returns registered PackageInfo instances

### 2.3 TypeRegistry entry-points scanning

- [ ] Update `src/scieasy/core/types/registry.py`:
  - Add `_scan_entrypoint_types()` method: iterates `entry_points(group="scieasy.types")`, calls each callable, registers returned type classes
  - Add `logger.warning(...)` on load failure
  - Call `_scan_entrypoint_types()` from `scan_all()` or at end of `scan_builtins()`
- [ ] Test: `_scan_entrypoint_types()` registers custom type subclass
- [ ] Test: entry-point load failure logs warning and does not crash

### 2.4 AdapterRegistry priority enforcement

- [ ] Update `src/scieasy/blocks/io/adapter_registry.py`:
  - Add priority enforcement in `scan_entry_points()`: external adapters cannot override extensions already claimed by `register_defaults()` (`.csv`, `.parquet`, `.tiff`, `.zarr`)
  - Add `logger.warning(...)` in exception handler
  - Add `logger.info(...)` on successful external adapter registration
- [ ] Test: external adapter cannot override built-in `.csv` extension
- [ ] Test: external adapter registers successfully for novel extension (e.g., `.srs`)
- [ ] Test: entry-point load failure logs warning and does not crash

### 2.5 API response updates for palette grouping

- [ ] Update `src/scieasy/api/routes/blocks.py`:
  - `GET /api/blocks` response includes `package_name` field per block
  - New endpoint or query parameter: return blocks grouped by package
- [ ] Update frontend `paletteSlice.ts` to support two-level grouping (package → category)
- [ ] Update `BlockPalette.tsx` to render package-grouped hierarchy

### Verification gate

- [ ] Mock external entry-point with `(PackageInfo, [Block])` return → appears in registry with correct package metadata
- [ ] Mock external entry-point with plain `[Block]` return → backward compatible registration
- [ ] Built-in `.csv` adapter not overridden by external package
- [ ] `make lint` passes
- [ ] `make typecheck` passes
- [ ] `make test` passes — all new tests green
- [ ] CI green ✅

### Deliverable

```
pip install scieasy-blocks-srs
scieasy gui
→ "SRS Imaging" package appears in palette with correct categorization.
→ SRSImage type is registered and matches Array/Image ports.
→ .srs adapter is registered for file loading.
→ Built-in .csv adapter is unaffected.
```

---

## Phase 3 — Block SDK: scaffolding, test harness, and developer docs (ADR-026)

**Goal**: external developers can create a complete block package from scratch in
5 minutes using `scieasy init-block-package`, test it with `BlockTestHarness`, and
publish it to PyPI following the developer documentation.

### 3.1 `BlockTestHarness`

- [ ] Create `src/scieasy/testing/__init__.py`:
  - Re-export: `from scieasy.testing.harness import BlockTestHarness`
- [ ] Create `src/scieasy/testing/harness.py` (~150 lines):
  - Constructor: `BlockTestHarness(block_class: type[Block], work_dir: Path)`
  - `run(inputs: dict, params: dict) -> dict`: wraps raw data into DataObjects/Collections, constructs BlockConfig, calls `block.run()`, materializes outputs
  - `validate_contract(block_class)`: checks `input_ports`/`output_ports` declarations, verifies `run()` signature
  - Internal helpers:
    - `_wrap_input(raw_data) -> Collection`: dict → DataFrame, ndarray → Array, list → Collection
    - `_materialize_output(collection: Collection) -> Any`: Collection → native Python objects
- [ ] Test: `run()` wraps dict input as DataFrame, returns materialized output
- [ ] Test: `run()` wraps ndarray input as Array
- [ ] Test: `run()` wraps list input as Collection
- [ ] Test: `validate_contract()` catches block missing `output_ports`
- [ ] Test: error in block raises, not silently swallowed
- [ ] Test: `work_dir` cleanup

### 3.2 Scaffolding templates

- [ ] Create `src/scieasy/cli/templates/` directory
- [ ] Create template files:
  - `pyproject.toml.tpl` — pre-configured with entry-points, placeholders for `{{package_name}}`, `{{display_name}}`, `{{author}}`, `{{categories}}`
  - `__init__.py.tpl` — `PackageInfo` declaration + `get_blocks()` importing from each category
  - `example_block.py.tpl` — minimal working block with inline comments explaining the contract
  - `test_block.py.tpl` — working test using `BlockTestHarness`
  - `README.md.tpl` — quick-start instructions, development setup, publishing checklist
- [ ] Update `pyproject.toml`: add `[tool.setuptools.package-data]` entry: `scieasy = ["cli/templates/*.tpl", "api/static/**/*"]`

### 3.3 `scieasy init-block-package` CLI command

- [ ] Create `src/scieasy/cli/_scaffold.py` (~100 lines):
  - `scaffold_block_package(name, display_name, author, categories, target_dir)`: reads `.tpl` files, performs string substitution, writes output files
  - Per-category directory creation with example blocks
- [ ] Add `init-block-package` command to `src/scieasy/cli/main.py`:
  - `@app.command("init-block-package")`
  - Arguments: `name: str`, `--display-name`, `--author`, `--categories` (comma-separated, default "processing")
  - Calls `scaffold_block_package()` and prints summary
- [ ] Test: generates valid directory structure
- [ ] Test: generated `pyproject.toml` has correct entry-points
- [ ] Test: generated `__init__.py` has `PackageInfo` and `get_blocks()`
- [ ] Test: generated test file imports `BlockTestHarness`
- [ ] Test: multiple categories create per-category subdirectories

### 3.4 Developer documentation

- [ ] Create `docs/block-development/quickstart.md`:
  - 5-minute guide from `pip install scieasy` to running a custom block
  - Covers: `init-block-package`, editing example, running tests, `pip install -e .`, `scieasy blocks`
- [ ] Create `docs/block-development/architecture-for-block-devs.md`:
  - Execution model for external developers: subprocess isolation, Collection transport, block lifecycle
  - No ADR numbers in prose — concepts only
- [ ] Create `docs/block-development/block-contract.md`:
  - Input/output/params reference: `input_ports`/`output_ports`, `BlockConfig`, `process_item()` vs `run()`
- [ ] Create `docs/block-development/data-types.md`:
  - Core type hierarchy, Collection as transport, when to use each type
- [ ] Create `docs/block-development/custom-types.md`:
  - Subclassing rules, `axes` as `ClassVar`, metadata in `_metadata` dict, max depth 3
  - Registration via `scieasy.types` entry-point
- [ ] Create `docs/block-development/memory-safety.md`:
  - Three-tier processing model, when to use each tier
- [ ] Create `docs/block-development/collection-guide.md`:
  - `pack()`/`unpack()`/`unpack_single()`, `map_items()`, `parallel_map()`
- [ ] Create `docs/block-development/testing.md`:
  - BlockTestHarness API reference, example patterns
- [ ] Create `docs/block-development/publishing.md`:
  - PyPI packaging guide, version constraints, testing in clean virtualenv
- [ ] Create `docs/block-development/examples/`:
  - `simple-transform.md` — single-input single-output, `process_item()` pattern
  - `collection-processing.md` — multi-item, `map_items()` and `parallel_map()`
  - `custom-io-adapter.md` — FormatAdapter for domain-specific formats
  - `multi-block-package.md` — full package: multiple categories, custom type, PackageInfo

### 3.5 Integration verification

- [ ] End-to-end test: `scieasy init-block-package test-pkg` → `cd test-pkg` → `pip install -e .` → `pytest` passes → blocks appear in `scieasy blocks` list
- [ ] Verify `BlockTestHarness` works with all three processing tiers (Tier 1 process_item, Tier 2 map_items, Tier 3 manual)

### Verification gate

- [ ] `scieasy init-block-package test-pkg` generates a valid, installable package
- [ ] Generated package tests pass with `pytest`
- [ ] `BlockTestHarness` catches contract violations in test blocks
- [ ] All 13 documentation files exist and are non-empty
- [ ] `make lint` passes
- [ ] `make typecheck` passes
- [ ] `make test` passes — all new tests green
- [ ] CI green ✅

### Deliverable

```
scieasy init-block-package scieasy-blocks-srs
cd scieasy-blocks-srs
# Edit example block...
pip install -e ".[dev]"
pytest                          # BlockTestHarness validates contract
pip install -e .
scieasy gui                     # "SRS Imaging" appears in palette
# Ready to publish:
python -m build && twine upload dist/*
```

---

## Cross-phase dependencies

```
Phase 1 (ADR-024)          Phase 2 (ADR-025)          Phase 3 (ADR-026)
Frontend bundling          Entry-points protocol      Block SDK
scieasy gui                PackageInfo                BlockTestHarness
SPA fallback               Registry refactoring       Scaffolding CLI
                           Adapter priority           Developer docs
      │                           │                          │
      └───── no dependency ───────┘                          │
                                  │                          │
                                  └── Phase 3 depends on ────┘
                                       Phase 2 (PackageInfo,
                                       entry-points protocol)
```

- **Phase 1 is independent** — can be implemented in parallel with Phase 2.
- **Phase 2 is independent of Phase 1** — entry-points protocol does not require frontend bundling.
- **Phase 3 depends on Phase 2** — `init-block-package` generates `PackageInfo` and entry-points configurations defined by ADR-025. `BlockTestHarness` tests blocks against the contract that Phase 2 establishes.

## Risk assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Vite `base: "./"` breaks some asset loading | Phase 1 unusable | Test with actual build output before merging; CI integration test |
| Entry-point load order differs across Python versions | Phase 2 adapter priority failure | Test with Python 3.11, 3.12, 3.13; use deterministic ordering in `register_defaults()` |
| `BlockTestHarness` hides contract violations | Phase 3 gives false confidence | Test the harness itself with deliberately broken blocks |
| Template files not included in wheel | Phase 3 `init-block-package` fails after pip install | CI test: install wheel in clean virtualenv, run `scieasy init-block-package` |
| External developer confusion about `process_item` vs `run` | Ecosystem fragmentation | Clear decision tree in `block-contract.md`; default template uses `process_item` |
