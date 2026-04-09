# AI Agent System Testing Guide

> **Status**: Active
> **Audience**: AI coding/testing agents operating in the SciEasy repository
> **Last updated**: 2026-04-08
> **Owner**: SciEasy maintainers

---

## 1. Purpose

This guide defines the minimum system-test procedure that an AI agent must run
when validating SciEasy's real-world imaging workflows.

The goals are:

- verify that the core runtime can execute a real imaging workflow end-to-end
- verify that `pip install -> GUI -> backend -> runtime -> output files` works
- verify that hyperspectral/SRS data can participate in a real workflow
- verify that pause/resume/checkpoint behavior works at the system level
- verify that the same test intent can be executed on both Windows and macOS

This guide is intentionally written as an execution playbook, not a high-level
testing strategy memo.

---

## 2. System Overview

SciEasy is an AI-native scientific workflow platform built around a typed
workflow graph and a backend-owned runtime.

At a high level:

- the backend/runtime owns workflow truth, validation, execution state, and
  checkpoint semantics
- blocks provide typed inputs/outputs and execute domain logic
- plugins extend the system with domain-specific data types and blocks such as
  imaging and SRS processing
- the frontend is a workflow editor and execution surface, not the source of
  workflow truth
- system tests must therefore validate both execution correctness and
  cross-layer consistency

This guide focuses on four system-level risk areas that have already produced
real regressions:

- real plugin discovery after installation
- real typed-data flow across imaging and SRS blocks
- real frontend/backend/runtime coordination in the browser
- real runtime control behavior for pause, resume, and checkpoints

These are system tests, not unit tests, because they exercise multiple layers
at once:

- package installation
- block/type registry discovery
- workflow construction
- runtime execution
- output persistence
- browser-driven user interaction

---

## 3. Agent Rules

These rules are mandatory for any agent following this guide.

### 3.1 Use real tools, not hypothetical narration

When you claim a step was performed, you must have actually performed it with a
tool available in your environment.

Required mapping:

- terminal/shell actions: use the shell tool
- file inspection: use shell or file-reading tools
- browser interaction: use the available browser automation tool

### 3.2 GUI testing must use a browser tool

For any GUI/system test that says "open Chrome", the agent must call a browser
automation tool or browser connector.

Preferred examples:

- Chrome MCP / Chrome connector
- browser automation connector
- Playwright-driven browser session, if that is the available browser tool

Do not mark a GUI test as passed based on:

- reasoning alone
- reading source code alone
- API calls alone
- screenshots supplied by a human without interacting yourself

If no browser tool is available, stop and report:

`BLOCKED: GUI system test requires a browser automation tool.`

### 3.3 Record evidence while testing

For every system test, collect:

- exact commands executed
- environment details
- terminal logs
- output file paths
- screenshots for GUI checkpoints
- pass/fail verdict
- failure summary and reproduction point if the test fails

### 3.4 Preserve exact filenames

The four example image filenames contain spaces and parentheses. Do not rename
them. The tests in this guide intentionally exercise path handling with these
filenames.

---

## 4. Fixed Dataset

### 4.1 Windows canonical dataset path

The canonical Windows dataset directory is:

`C:\Users\jiazh\Desktop\workspace\Example\images`

It must contain exactly these four files:

- `K562_L_2845 (uV).tif`
- `K562_UL_2845 (uV).tif`
- `K562_L_spectra (uV).tif`
- `K562_UL_spectra (uV).tif`

Semantics:

- the two `*_2845*` images are used for segmentation
- the two `*_spectra*` images are used for hyperspectral/SRS tests

### 4.2 macOS dataset requirement

On macOS, place the same four files in any absolute directory, but preserve the
exact filenames.

Recommended example:

`/Users/<username>/Desktop/workspace/Example/images`

The agent must record the chosen macOS absolute dataset path in the test report.

---

## 5. Required Test Matrix

All four tests below are required.

| Test ID | Name | Primary Goal | Uses Browser Tool | Uses Real Dataset |
|---------|------|--------------|-------------------|-------------------|
| ST-001 | CLI Core Imaging Workflow | Validate headless runtime execution | No | Yes |
| ST-002 | GUI Full-Stack Imaging Workflow | Validate frontend-backend-core integration from install | Yes | Yes |
| ST-003 | Hyperspectral/SRS Workflow | Validate hyperspectral data path and cross-plugin flow | Optional for CLI authoring, yes if GUI variant is run | Yes |
| ST-004 | Pause/Resume/Checkpoint Workflow | Validate runtime control semantics and checkpoint persistence | Recommended yes, API variant acceptable | No special dataset required |

Windows and macOS must both pass the same logical suite.

---

## 6. Environment Setup

### 6.1 Common prerequisites

- Python 3.11+ available
- Git available
- Chrome installed for GUI testing
- network access available for dependency installation if wheels are missing
- a clean virtual environment for each platform run

### 6.2 Required packages

At minimum, install:

- `scieasy`
- `scieasy-blocks-imaging`
- `scieasy-blocks-srs`
- `cellpose`

If testing from the local repository rather than PyPI, install from local paths.

### 6.3 Windows setup example

```powershell
cd C:\Users\jiazh\Desktop\workspace\SciEasy
python -m venv .venv-agent-test
.\.venv-agent-test\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install C:\Users\jiazh\Desktop\workspace\SciEasy
pip install C:\Users\jiazh\Desktop\workspace\SciEasy\packages\scieasy-blocks-imaging
pip install C:\Users\jiazh\Desktop\workspace\SciEasy\packages\scieasy-blocks-srs
pip install cellpose
```

### 6.4 macOS setup example

```bash
cd /Users/<username>/Desktop/workspace/SciEasy
python3 -m venv .venv-agent-test
source .venv-agent-test/bin/activate
python -m pip install --upgrade pip
pip install /Users/<username>/Desktop/workspace/SciEasy
pip install /Users/<username>/Desktop/workspace/SciEasy/packages/scieasy-blocks-imaging
pip install /Users/<username>/Desktop/workspace/SciEasy/packages/scieasy-blocks-srs
pip install cellpose
```

### 6.5 Installation smoke checks

Run:

```bash
scieasy --help
scieasy blocks
```

Minimum expectation:

- the `scieasy` CLI is available
- imaging and SRS-related blocks are discoverable
- no fatal registry/import error prevents block listing

---

## 7. Test Workspace Conventions

Create a dedicated workspace per run.

Recommended names:

- Windows CLI run: `system-test-cli-win`
- Windows GUI run: `system-test-gui-win`
- macOS CLI run: `system-test-cli-mac`
- macOS GUI run: `system-test-gui-mac`

Inside each workspace, preserve:

- the workflow definition file(s)
- generated outputs
- captured logs
- screenshots
- a short verdict summary

---

## 8. ST-001: CLI Core Imaging Workflow

### 8.1 Objective

Verify that the core runtime can execute a real imaging workflow using the two
`*_2845*` images and produce a single-cell intensity table.

### 8.2 Input files

Use:

- `K562_L_2845 (uV).tif`
- `K562_UL_2845 (uV).tif`

### 8.3 Workflow intent

The workflow must implement this logical pipeline:

1. load the two 2845 images
2. merge them into one collection
3. apply Gaussian denoise
4. run CellPose segmentation
5. compute single-cell intensity measurements
6. save a table to disk

Recommended block sequence:

`LoadImage x2 -> MergeCollection -> Denoise(method=gaussian) -> CellposeSegment -> RegionProps -> SaveData/SaveTable`

### 8.4 Authoring instructions

Create a temporary workflow YAML in the test workspace.

Before authoring, use `scieasy blocks` to confirm the current installed block
identifiers. The exact internal block type string may differ across builds; the
agent must use the installed identifiers, but preserve the logical flow above.

### 8.5 Execution steps

1. Create a test workspace.
2. Author the workflow YAML.
3. Point the two `LoadImage` blocks at the two `*_2845*` files.
4. Configure Gaussian denoise with a small sigma such as `1.0`.
5. Configure CellPose with a stable baseline profile such as:
   - model: `cyto`
   - diameter: `30`
6. Configure `RegionProps` to include intensity-bearing columns.
7. Save the output table as CSV.
8. Run validation.
9. Run the workflow via CLI.

### 8.6 Command pattern

```bash
scieasy validate <workflow-yaml>
scieasy run <workflow-yaml>
```

### 8.7 Required evidence

- full validation output
- full runtime output
- the workflow YAML used
- the output CSV path
- the output CSV header and row count

### 8.8 Pass criteria

All of the following must be true:

- validation succeeds
- workflow execution completes without an unhandled exception
- a CSV table is written to disk
- the CSV is non-empty
- the CSV contains at least one intensity-related column such as `mean_intensity`
- both 2845 images were processed, not only one image

### 8.9 Fail examples

Fail the test if any of the following occurs:

- block registry cannot find required plugin blocks
- workflow appears to run but produces no output file
- runtime stops without explicit error reporting
- output table exists but contains zero rows

---

## 9. ST-002: GUI Full-Stack Imaging Workflow

### 9.1 Objective

Verify the full user path:

`pip install -> scieasy gui -> browser interaction -> workflow run -> output files`

This test uses the same logical workflow as ST-001, but must be executed
through the frontend in a real browser session.

### 9.2 Special rule

This test is invalid unless the agent actually uses a browser automation tool.

### 9.3 Setup

Run this test from a fresh virtual environment, starting from package install.

### 9.4 Workflow intent

Use the same logical workflow as ST-001:

`LoadImage x2 -> MergeCollection -> Denoise(gaussian) -> CellposeSegment -> RegionProps -> SaveData/SaveTable`

### 9.5 Execution steps

1. Create and activate a fresh virtual environment.
2. Install `scieasy`, `scieasy-blocks-imaging`, `scieasy-blocks-srs`, and `cellpose`.
3. Start the GUI server:
   - `scieasy gui`
4. Confirm the backend serves the workflow editor, not only `/docs`.
5. Launch Chrome with the browser tool.
6. Navigate to the local SciEasy GUI URL.
7. Create a new project/workspace if required by the UI.
8. Drag the required blocks from the palette to the canvas.
9. Use the GUI to configure:
   - two 2845 image paths
   - Gaussian denoise
   - CellPose parameters
   - output CSV path
10. Connect the blocks in the canvas.
11. Run the workflow from the GUI.
12. Verify node states, logs, and output files.

### 9.6 Browser-tool requirements

The agent must use the browser tool to do all of the following:

- open the browser
- navigate to the GUI
- click buttons
- type into fields
- use file/path selection UI where available
- connect nodes
- trigger workflow execution
- inspect visible state after execution

At minimum, capture screenshots for:

- empty editor after load
- workflow assembled on canvas
- run in progress
- completed run with final node states

### 9.7 GUI-specific checks

The agent must explicitly verify these regression-prone behaviors:

- `LoadImage` path configuration exposes a usable `Browse` button or equivalent picker control
- node color/type visualization is not silently degraded to generic fallback styling
- clicking Run does not result in a silent no-op
- errors, if any, surface in logs/problems rather than disappearing

### 9.8 Required evidence

- installation commands
- GUI server startup log
- browser screenshots
- final output CSV path
- final output CSV row count
- a short note describing any GUI oddity even if the run passes

### 9.9 Pass criteria

All of the following must be true:

- the GUI is reachable from the installed environment
- the workflow can be created and configured in the browser
- the workflow runs from the GUI without silent failure
- the output CSV is written and non-empty
- GUI controls used for path selection and run execution behave correctly

---

## 10. ST-003: Hyperspectral/SRS Workflow

### 10.1 Objective

Verify that the system can process the two hyperspectral images and complete a
cross-plugin workflow that combines segmentation and spectral extraction.

### 10.2 Input files

Segmentation images:

- `K562_L_2845 (uV).tif`
- `K562_UL_2845 (uV).tif`

Hyperspectral images:

- `K562_L_spectra (uV).tif`
- `K562_UL_spectra (uV).tif`

### 10.3 Workflow intent

Run a two-arm workflow:

Segmentation arm:

`LoadImage(2845) x2 -> MergeCollection -> Denoise(gaussian) -> CellposeSegment`

Spectral arm:

`LoadImage(spectra) x2 -> MergeCollection -> Denoise(gaussian) -> SRSCalibrate`

Join point:

`Cellpose labels + calibrated spectra -> ExtractSpectrum -> SaveData/SaveTable`

### 10.4 Why this test exists

This test verifies more than simple file loading. It checks:

- hyperspectral file ingestion
- collection/type propagation across plugins
- cross-plugin compatibility between imaging and SRS outputs
- real output generation for spectral data

### 10.5 Execution notes

- If the current installed package names or block IDs differ, adjust the YAML or
  GUI selection to the installed identifiers.
- Preserve the logical topology above even if exact block names vary slightly.
- If the environment is too constrained for a GUI run, a CLI variant is
  acceptable, but the agent should prefer a GUI run when a browser tool exists.

### 10.6 Required evidence

- workflow definition
- runtime logs
- output table path
- output table schema/columns
- note of which plugin blocks were used for the spectral arm

### 10.7 Pass criteria

All of the following must be true:

- both `*_spectra*` files are successfully loaded
- the workflow reaches terminal success
- spectral output is produced as a table
- the resulting table is non-empty
- no type/port incompatibility prevents the imaging/SRS join

### 10.8 Fail examples

Fail the test if any of the following occurs:

- spectra files load but later blocks reject their types unexpectedly
- the workflow only processes the 2845 arm and silently drops the spectra arm
- `ExtractSpectrum` or equivalent output table is empty without explanation

---

## 11. ST-004: Pause/Resume/Checkpoint Workflow

### 11.1 Objective

Verify runtime control behavior:

- pause blocks downstream dispatch
- resume continues execution
- checkpoint state is materialized and can be inspected

This test validates runtime semantics rather than imaging math.

### 11.2 Preferred execution mode

Preferred:

- GUI + API-backed workflow execution, with browser evidence

Acceptable fallback:

- API/system-level execution against the workflow endpoints

### 11.3 Recommended test workflow

Use a simple three-node linear workflow with an intentionally slow middle block
so that pause can be asserted while work is in progress.

Logical shape:

`LoadData -> ProcessBlock(sleep) -> ProcessBlock(final)`

Recommended timing:

- middle block sleep: about `0.8` seconds
- final block sleep: `0.0` to `0.2` seconds

This mirrors the runtime semantics covered in the API/system tests and is a
good system-level control probe.

### 11.4 Execution steps

1. Create a workflow whose middle block takes long enough to observe `RUNNING`.
2. Start execution.
3. Wait until the middle block is visibly or programmatically `RUNNING`.
4. Pause the workflow.
5. Verify the downstream block stays `READY` and is not dispatched while paused.
6. Verify checkpoint artifacts or checkpoint state exist for the workflow run.
7. Resume the workflow.
8. Verify the workflow reaches terminal success.

### 11.5 Evidence to collect

- command or API call used to execute
- command or API call used to pause
- command or API call used to resume
- visible state or API evidence that downstream dispatch was held
- checkpoint path or checkpoint metadata
- final terminal workflow state

### 11.6 Pass criteria

All of the following must be true:

- pause is accepted while a block is running
- new downstream work does not dispatch while paused
- checkpoint data exists for the workflow run
- resume unblocks the workflow
- the workflow reaches successful completion after resume

### 11.7 Fail examples

Fail the test if any of the following occurs:

- pause returns success but downstream work keeps dispatching
- resume returns success but the workflow remains stuck
- no checkpoint artifact/state is observable after pause or block completion

---

## 12. Cross-Platform Expectations

### 12.1 Windows

Windows is mandatory because the current dataset and several desktop-tool paths
have been exercised primarily on Windows.

Windows-specific checks:

- paths with spaces and parentheses work
- file pickers handle Windows absolute paths correctly
- output directories are created correctly

### 12.2 macOS

macOS is mandatory because the suite must not be Windows-only.

macOS-specific checks:

- POSIX absolute paths work cleanly
- browser-based GUI workflow still behaves correctly
- output and checkpoint paths are created under the macOS workspace

### 12.3 Requirement

A test suite run is incomplete unless the agent reports results for both:

- Windows
- macOS

The same logical test IDs must be used on both platforms.

---

## 13. Test Report Format

For each platform, the agent should return results in this shape:

### 13.1 Environment

- OS
- Python version
- install mode (`pip install` from local path or package index)
- dataset root

### 13.2 Results

- `ST-001`: PASS/FAIL
- `ST-002`: PASS/FAIL
- `ST-003`: PASS/FAIL
- `ST-004`: PASS/FAIL

### 13.3 Evidence

- commands executed
- output file paths
- screenshot paths or attachments
- checkpoint path or metadata

### 13.4 Failures

For each failure, include:

- first failing step
- error message
- whether the failure is reproducible
- whether a new GitHub issue should be opened

---

## 14. Escalation Rules

Open or update a GitHub issue if any of the following occurs:

- the workflow silently does nothing
- GUI and runtime disagree about block behavior
- type colors or accepted types are visibly inconsistent
- path picker / Browse behavior is missing or wrong
- hyperspectral files cannot complete the documented flow
- pause/resume/checkpoint semantics regress
- Windows passes but macOS fails, or vice versa

If the failure is clearly a regression, label it as a blocker for release
confidence.

---

## 15. Future Recommended Additions

These are not optional forever; they are the next tests to formalize after the
four required tests above.

- browser-automated regression test for `execute-from` / restart-from-node
- save/load round-trip test for workflow YAML plus output artifacts
- long-running workflow stability test with repeated pause/resume cycles
- fresh-install smoke test on CI runners for both Windows and macOS
- automated browser E2E coverage for the exact ST-002 flow

---

*End of guide.*
