# Phase 5–8: End-to-End Human Test Plan

> **Scope**: Manual verification procedures from execution engine (Phase 5) through
> frontend (Phase 8). Each test is self-contained and states prerequisites,
> steps, and expected results. Tests are ordered by dependency — complete earlier
> tests before attempting later ones.
>
> **Convention**: `[ ] PASS / [ ] FAIL` checkboxes are for the tester to mark.

---

## 0. Prerequisites

| Requirement | How to Check |
|-------------|-------------|
| Python 3.11+ | `python --version` |
| SciEasy installed (dev) | `pip install -e ".[dev]"` then `python -c "import scieasy"` |
| Phase 3+4 tests green | `pytest tests/core/ tests/blocks/ -q` |
| Node.js 18+ (Phase 8 only) | `node --version` |
| psutil | `python -c "import psutil"` |
| pyarrow 15+ | `python -c "import pyarrow"` |

```bash
cd SciEasy
git checkout main && git pull origin main
pip install -e ".[dev]"
pytest tests/core/ tests/blocks/ -q
```

---

# PHASE 5: Execution Engine

---

## P5-H01: Collection Construction and Homogeneity

**What**: Verify Collection enforces homogeneous types (ADR-020).

```python
python
```
```python
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy.core.types.array import Image

# 1. Create a valid Collection
items = [DataFrame(columns=["a", "b"]) for _ in range(3)]
coll = Collection(items)
print(f"Type: Collection[{coll.item_type.__name__}], len={len(coll)}")
# Expected: Collection[DataFrame], len=3

# 2. Reject mixed types
try:
    bad = Collection([DataFrame(columns=["a"]), Image()])
    print("ERROR: should have raised TypeError")
except TypeError as e:
    print(f"Mixed type rejected: {e}")
    # Expected: TypeError about mixing DataFrame and Image

# 3. Empty Collection requires explicit item_type (ADR-020 Addendum 6)
try:
    empty = Collection([])
    print("ERROR: should require item_type for empty collection")
except (TypeError, ValueError) as e:
    print(f"Empty collection rejected: {e}")

# 4. Empty Collection with explicit item_type
empty = Collection([], item_type=DataFrame)
print(f"Empty Collection item_type: {empty.item_type.__name__}")
# Expected: DataFrame
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H02: Block Base — process_item / map_items / pack (Three-Tier)

**What**: Verify the three-tier block authoring interface works (ADR-020).

```python
python
```
```python
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame
from scieasy.blocks.base.block import Block

# -- Tier 1: process_item --
# Block authors override process_item() for simple 1-in-1-out transforms.
# The base run() should iterate Collection and call process_item per item.
# (Verify via a concrete ProcessBlock subclass or test double)

# -- Tier 2: map_items --
items = [DataFrame(columns=["x"]) for _ in range(5)]
coll = Collection(items)

# map_items applies a function to each item in Collection
result = Block.map_items(lambda df: df, coll)
print(f"map_items result: Collection len={len(result)}")
# Expected: 5

# -- Tier 3: pack --
# pack() wraps loose items into a Collection (safety net)
loose = [DataFrame(columns=["y"]) for _ in range(3)]
packed = Block.pack(loose)
print(f"pack result: Collection len={len(packed)}")
# Expected: 3

# -- unpack round-trip --
unpacked = Block.unpack(packed)
repacked = Block.pack(unpacked)
print(f"Round-trip: {len(repacked)} items")
# Expected: 3
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H03: LazyList for CodeBlock

**What**: Verify LazyList loads items on demand, not eagerly (ADR-020 Addendum 4).

```python
python
```
```python
from scieasy.blocks.code.lazy_list import LazyList
from scieasy.core.types.dataframe import DataFrame
from scieasy.core.types.collection import Collection
from scieasy.core.storage.ref import StorageReference

# Create a Collection with StorageReferences
# (simulate stored items — actual loading depends on storage backend)
items = [DataFrame(columns=["a"]) for _ in range(10)]
coll = Collection(items)

# LazyList wraps a Collection — len() should NOT load all items
lazy = LazyList(coll)
print(f"len(lazy) = {len(lazy)}")
# Expected: 10 (no full load)

# Iteration loads items one at a time
for i, item in enumerate(lazy):
    if i >= 2:
        break
    print(f"  item[{i}]: {type(item).__name__}")
# Expected: prints item[0] and item[1] types

# Indexing loads single item
item = lazy[0]
print(f"lazy[0]: {type(item).__name__}")
# Expected: DataFrame
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H04: EventBus Publish/Subscribe

**What**: Verify EventBus delivers events to correct subscribers (ADR-018).

```python
python
```
```python
from scieasy.engine.events import EventBus, EngineEvent

bus = EventBus()
received = []

# Subscribe to specific event type
def on_block_done(event):
    received.append(event)

bus.subscribe("BLOCK_DONE", on_block_done)

# Emit matching event
bus.emit(EngineEvent(event_type="BLOCK_DONE", block_id="A", data={"status": "ok"}))

# Emit non-matching event — should NOT trigger handler
bus.emit(EngineEvent(event_type="BLOCK_ERROR", block_id="B", data={"error": "fail"}))

# Emit another matching event
bus.emit(EngineEvent(event_type="BLOCK_DONE", block_id="C", data={"status": "ok"}))

print(f"Received {len(received)} events")
# Expected: 2

print(f"Block IDs: {[e.block_id for e in received]}")
# Expected: ['A', 'C']

# Unsubscribe
bus.unsubscribe("BLOCK_DONE", on_block_done)
bus.emit(EngineEvent(event_type="BLOCK_DONE", block_id="D", data={}))
print(f"After unsubscribe: {len(received)} events")
# Expected: still 2

# Error isolation: one bad subscriber should not break others
good_results = []
def good_handler(event):
    good_results.append(event.block_id)

def bad_handler(event):
    raise RuntimeError("I crash")

bus.subscribe("BLOCK_DONE", bad_handler)
bus.subscribe("BLOCK_DONE", good_handler)

bus.emit(EngineEvent(event_type="BLOCK_DONE", block_id="E", data={}))
print(f"Good handler got: {good_results}")
# Expected: ['E'] — bad handler crash did not prevent good handler
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H05: DAG Build + Topological Sort

**What**: Verify DAG construction from WorkflowDefinition and topological ordering.

```python
python
```
```python
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.dag import build_dag, topological_sort

# Linear pipeline: Load → Process → Save
workflow = WorkflowDefinition(
    id="test-linear",
    nodes=[
        NodeDef(id="load", block_type="io_block", config={}),
        NodeDef(id="process", block_type="process_block", config={}),
        NodeDef(id="save", block_type="io_block", config={}),
    ],
    edges=[
        EdgeDef(source="load:data", target="process:input"),
        EdgeDef(source="process:output", target="save:data"),
    ],
)

dag = build_dag(workflow)
print(f"Nodes: {len(dag.nodes)}, Edges: {len(dag.edges)}")
# Expected: Nodes: 3, Edges: 2

order = topological_sort(dag)
ids = [n.id for n in order]
print(f"Order: {ids}")
# Expected: ['load', 'process', 'save']

# Verify load comes before process, process comes before save
assert ids.index("load") < ids.index("process") < ids.index("save")
print("Topological order correct")
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H06: Cycle Detection

**What**: Verify cycles are caught and reported.

```python
python
```
```python
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.dag import build_dag, topological_sort

workflow = WorkflowDefinition(
    id="test-cycle",
    nodes=[
        NodeDef(id="A", block_type="process_block", config={}),
        NodeDef(id="B", block_type="process_block", config={}),
        NodeDef(id="C", block_type="process_block", config={}),
    ],
    edges=[
        EdgeDef(source="A:out", target="B:in"),
        EdgeDef(source="B:out", target="C:in"),
        EdgeDef(source="C:out", target="A:in"),  # cycle!
    ],
)

dag = build_dag(workflow)

try:
    topological_sort(dag)
    print("ERROR: should have raised CycleError!")
except Exception as e:
    print(f"Cycle detected: {type(e).__name__}: {e}")
    # Expected: some form of cycle error
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H07: DAGScheduler — Linear Pipeline Execution

**What**: Execute a 3-block linear workflow end-to-end.

```python
python
```
```python
import asyncio
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.scheduler import DAGScheduler

# Build a minimal workflow
# (Adjust block_type names and config to match actual registered blocks)
workflow = WorkflowDefinition(
    id="test-execute",
    nodes=[
        NodeDef(id="load", block_type="io_block",
                config={"direction": "input", "path": "tests/fixtures/sample.csv", "format": "csv"}),
        NodeDef(id="process", block_type="process_block", config={}),
        NodeDef(id="save", block_type="io_block",
                config={"direction": "output", "path": "/tmp/scieasy_test/output.parquet", "format": "parquet"}),
    ],
    edges=[
        EdgeDef(source="load:data", target="process:input"),
        EdgeDef(source="process:output", target="save:data"),
    ],
)

scheduler = DAGScheduler(workflow)
result = asyncio.run(scheduler.execute())
print(f"Execution result: {result}")
# Expected: workflow completes successfully

import os
print(f"Output exists: {os.path.exists('/tmp/scieasy_test/output.parquet')}")
# Expected: True
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H08: DAGScheduler — Diamond DAG (Fan-out + Fan-in)

**What**: Verify correct execution of a diamond-shaped DAG where one block feeds
two branches that merge back.

```python
python
```
```python
import asyncio
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.scheduler import DAGScheduler

#       ┌─ B ─┐
#  A ──┤       ├── D
#       └─ C ─┘
workflow = WorkflowDefinition(
    id="test-diamond",
    nodes=[
        NodeDef(id="A", block_type="io_block", config={"direction": "input"}),
        NodeDef(id="B", block_type="process_block", config={}),
        NodeDef(id="C", block_type="process_block", config={}),
        NodeDef(id="D", block_type="process_block", config={}),
    ],
    edges=[
        EdgeDef(source="A:data", target="B:input"),
        EdgeDef(source="A:data", target="C:input"),
        EdgeDef(source="B:output", target="D:left"),
        EdgeDef(source="C:output", target="D:right"),
    ],
)

scheduler = DAGScheduler(workflow)
result = asyncio.run(scheduler.execute())
print(f"Diamond DAG result: {result}")
# Expected: A executes first, B and C concurrently, D last
# Verify: D received inputs from both B and C
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H09: Cancel Block → CANCELLED + SKIPPED Propagation (ADR-018)

**What**: Cancel a running block and verify downstream blocks become SKIPPED.

```python
python
```
```python
import asyncio
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.scheduler import DAGScheduler
from scieasy.engine.events import EventBus

# A (slow) → B → C
# Cancel A → A=CANCELLED, B=SKIPPED, C=SKIPPED
workflow = WorkflowDefinition(
    id="test-cancel",
    nodes=[
        NodeDef(id="slow_block", block_type="process_block",
                config={"sleep_seconds": 30}),  # intentionally slow
        NodeDef(id="downstream1", block_type="process_block", config={}),
        NodeDef(id="downstream2", block_type="process_block", config={}),
    ],
    edges=[
        EdgeDef(source="slow_block:output", target="downstream1:input"),
        EdgeDef(source="downstream1:output", target="downstream2:input"),
    ],
)

state_changes = []

async def run_and_cancel():
    scheduler = DAGScheduler(workflow)

    # Collect state change events
    scheduler.event_bus.subscribe("BLOCK_CANCELLED", lambda e: state_changes.append(("CANCELLED", e.block_id)))
    scheduler.event_bus.subscribe("BLOCK_SKIPPED", lambda e: state_changes.append(("SKIPPED", e.block_id)))

    # Start execution
    task = asyncio.create_task(scheduler.execute())

    # Wait for slow_block to start running
    await asyncio.sleep(1)

    # Cancel the slow block
    await scheduler.cancel_block("slow_block")

    # Wait for propagation
    result = await task
    return result

result = asyncio.run(run_and_cancel())
print(f"State changes: {state_changes}")
# Expected: [('CANCELLED', 'slow_block'), ('SKIPPED', 'downstream1'), ('SKIPPED', 'downstream2')]
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H10: Cancel Block — Independent Branch Continues

**What**: Cancel one branch of a parallel workflow; the other branch continues normally.

```python
python
```
```python
import asyncio
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.scheduler import DAGScheduler

#       ┌─ B (slow, will be cancelled) → D (should be SKIPPED)
#  A ──┤
#       └─ C (fast, should complete normally) → E (should complete)
workflow = WorkflowDefinition(
    id="test-partial-cancel",
    nodes=[
        NodeDef(id="A", block_type="io_block", config={"direction": "input"}),
        NodeDef(id="B", block_type="process_block", config={"sleep_seconds": 30}),
        NodeDef(id="C", block_type="process_block", config={}),
        NodeDef(id="D", block_type="process_block", config={}),
        NodeDef(id="E", block_type="process_block", config={}),
    ],
    edges=[
        EdgeDef(source="A:data", target="B:input"),
        EdgeDef(source="A:data", target="C:input"),
        EdgeDef(source="B:output", target="D:input"),
        EdgeDef(source="C:output", target="E:input"),
    ],
)

final_states = {}

async def run_partial_cancel():
    scheduler = DAGScheduler(workflow)

    # Track final states
    for evt_type in ("BLOCK_DONE", "BLOCK_CANCELLED", "BLOCK_SKIPPED"):
        scheduler.event_bus.subscribe(evt_type,
            lambda e, t=evt_type: final_states.update({e.block_id: t}))

    task = asyncio.create_task(scheduler.execute())
    await asyncio.sleep(1)

    await scheduler.cancel_block("B")
    await task

asyncio.run(run_partial_cancel())
print(f"Final states: {final_states}")
# Expected:
#   A: BLOCK_DONE (already finished)
#   B: BLOCK_CANCELLED
#   C: BLOCK_DONE
#   D: BLOCK_SKIPPED  (downstream of cancelled B)
#   E: BLOCK_DONE     (independent branch)
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H11: ProcessHandle — Subprocess Lifecycle (ADR-019)

**What**: Verify ProcessHandle can spawn, monitor, terminate, and kill subprocesses.

```python
python
```
```python
import asyncio
import sys
from scieasy.engine.process_handle import ProcessHandle, spawn_block_process
from scieasy.engine.process_registry import ProcessRegistry

registry = ProcessRegistry()

async def test_process_lifecycle():
    # Spawn a long-running subprocess
    handle = await spawn_block_process(
        block_id="test_block",
        command=[sys.executable, "-c", "import time; time.sleep(60)"],
        registry=registry,
    )

    print(f"Process alive: {handle.is_alive()}")
    # Expected: True

    print(f"PID: {handle.pid}")
    # Expected: a valid PID number

    # Check registry
    found = registry.get_handle("test_block")
    print(f"Registry lookup: {found is not None}")
    # Expected: True

    # Graceful terminate
    await handle.terminate(timeout=5.0)
    print(f"After terminate, alive: {handle.is_alive()}")
    # Expected: False

    exit_info = handle.exit_info()
    print(f"Exit info: {exit_info}")
    # Expected: shows signal/return code indicating termination

    # Registry should auto-deregister
    found_after = registry.get_handle("test_block")
    print(f"Registry after terminate: {found_after}")
    # Expected: None

asyncio.run(test_process_lifecycle())
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H12: ProcessMonitor — Detect Unexpected Exit

**What**: Verify ProcessMonitor detects when a subprocess crashes unexpectedly.

```python
python
```
```python
import asyncio
import os
import signal
import sys
from scieasy.engine.process_handle import spawn_block_process
from scieasy.engine.process_monitor import ProcessMonitor
from scieasy.engine.process_registry import ProcessRegistry
from scieasy.engine.events import EventBus

bus = EventBus()
registry = ProcessRegistry()
exit_events = []

bus.subscribe("PROCESS_EXITED", lambda e: exit_events.append(e))

async def test_crash_detection():
    monitor = ProcessMonitor(registry=registry, event_bus=bus)
    monitor.start()

    # Spawn a subprocess
    handle = await spawn_block_process(
        block_id="crasher",
        command=[sys.executable, "-c", "import time; time.sleep(60)"],
        registry=registry,
    )

    # Kill it from outside (simulate crash)
    pid = handle.pid
    if sys.platform == "win32":
        os.kill(pid, signal.SIGTERM)
    else:
        os.kill(pid, signal.SIGKILL)

    # Wait for monitor to detect
    await asyncio.sleep(2)

    print(f"Exit events: {len(exit_events)}")
    # Expected: 1

    if exit_events:
        print(f"Block ID: {exit_events[0].block_id}")
        # Expected: 'crasher'

    await monitor.stop()

asyncio.run(test_crash_detection())
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H13: Resource Manager — psutil Memory + CPU/GPU Slots (ADR-022)

**What**: Verify ResourceManager checks OS memory and tracks discrete resources.

```python
python
```
```python
import asyncio
from scieasy.engine.resources import ResourceManager, ResourceRequest

mgr = ResourceManager(cpu_workers=4, gpu_slots=1, memory_high_watermark=0.95)

async def test_resources():
    snapshot = mgr.available
    print(f"CPU workers: {snapshot.available_cpu_workers}")
    # Expected: 4
    print(f"GPU slots: {snapshot.available_gpu_slots}")
    # Expected: 1
    print(f"Memory usage: {snapshot.system_memory_percent:.1%}")
    # Expected: current OS memory (e.g. 45.2%)

    # Acquire CPU + GPU
    req = ResourceRequest(cpu_cores=2, requires_gpu=True)
    can_dispatch = await mgr.can_dispatch(req)
    print(f"Can dispatch (2 CPU + GPU): {can_dispatch}")
    # Expected: True (unless memory > 95%)

    token = await mgr.acquire(req)

    # Check remaining
    print(f"After acquire — CPU: {mgr.available.available_cpu_workers}")
    # Expected: 2
    print(f"After acquire — GPU: {mgr.available.available_gpu_slots}")
    # Expected: 0

    # GPU exhausted — next GPU request should fail
    req2 = ResourceRequest(cpu_cores=1, requires_gpu=True)
    can2 = await mgr.can_dispatch(req2)
    print(f"Can dispatch another GPU: {can2}")
    # Expected: False

    # Release
    await mgr.release(token)
    print(f"After release — CPU: {mgr.available.available_cpu_workers}, GPU: {mgr.available.available_gpu_slots}")
    # Expected: 4, 1

asyncio.run(test_resources())
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H14: Checkpoint Save/Load Round-Trip

**What**: Verify checkpoint serialization including CANCELLED/SKIPPED states.

```python
python
```
```python
from scieasy.engine.checkpoint import WorkflowCheckpoint
import json

# Create checkpoint with ADR-018 states
checkpoint = WorkflowCheckpoint(
    workflow_id="test-wf",
    block_states={
        "load": "DONE",
        "process": "CANCELLED",
        "downstream": "SKIPPED",
        "save": "IDLE",
    },
    skip_reasons={"downstream": "upstream block 'process' was cancelled"},
    intermediate_refs={"load:data": "ref://storage/load_output"},
    config_snapshot={"load": {"path": "/data/input.csv"}},
)

# Save
path = "/tmp/scieasy_test_checkpoint.json"
checkpoint.save(path)
print("Saved checkpoint")

# Load
loaded = WorkflowCheckpoint.load(path)
print(f"Block states: {loaded.block_states}")
# Expected: {'load': 'DONE', 'process': 'CANCELLED', 'downstream': 'SKIPPED', 'save': 'IDLE'}

print(f"Skip reasons: {loaded.skip_reasons}")
# Expected: {'downstream': "upstream block 'process' was cancelled"}

assert loaded.block_states == checkpoint.block_states
assert loaded.skip_reasons == checkpoint.skip_reasons
assert loaded.intermediate_refs == checkpoint.intermediate_refs
print("Checkpoint round-trip: OK")

# Cleanup
import os
os.remove(path)
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H15: Pause → Checkpoint → Resume

**What**: Pause a running workflow, save checkpoint, resume from checkpoint.

```python
python
```
```python
import asyncio
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.scheduler import DAGScheduler

# 3-block pipeline with a "slow" middle block
workflow = WorkflowDefinition(
    id="test-resume",
    nodes=[
        NodeDef(id="fast1", block_type="process_block", config={}),
        NodeDef(id="slow", block_type="process_block", config={"sleep_seconds": 10}),
        NodeDef(id="fast2", block_type="process_block", config={}),
    ],
    edges=[
        EdgeDef(source="fast1:output", target="slow:input"),
        EdgeDef(source="slow:output", target="fast2:input"),
    ],
)

async def test_pause_resume():
    scheduler = DAGScheduler(workflow)
    task = asyncio.create_task(scheduler.execute())

    # Wait for fast1 to complete, slow to start
    await asyncio.sleep(2)

    # Pause
    checkpoint = await scheduler.pause()
    print(f"Paused. States: {checkpoint.block_states}")
    # Expected: fast1=DONE, slow=PAUSED or similar, fast2=IDLE

    # Save checkpoint
    checkpoint.save("/tmp/scieasy_resume_test.json")

    # Resume with a new scheduler
    from scieasy.engine.checkpoint import WorkflowCheckpoint
    loaded = WorkflowCheckpoint.load("/tmp/scieasy_resume_test.json")
    scheduler2 = DAGScheduler(workflow)
    result = await scheduler2.resume(loaded)
    print(f"Resumed and completed: {result}")
    # Expected: completes successfully, fast1 not re-executed

asyncio.run(test_pause_resume())

import os
os.remove("/tmp/scieasy_resume_test.json")
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P5-H16: Collection Operation Blocks (ADR-021)

**What**: Verify MergeCollection, SplitCollection, FilterCollection, SliceCollection.

```python
python
```
```python
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

# Setup
items_a = [DataFrame(columns=["x"]) for _ in range(3)]
items_b = [DataFrame(columns=["x"]) for _ in range(2)]
coll_a = Collection(items_a)
coll_b = Collection(items_b)

# 1. MergeCollection — concatenate same-typed collections
from scieasy.blocks.collection.merge import MergeCollection
merged = MergeCollection().execute(left=coll_a, right=coll_b)
print(f"Merged: {len(merged)} items")
# Expected: 5

# 2. MergeCollection — reject mixed types (strict type()==)
from scieasy.core.types.dataframe import PeakTable
coll_peak = Collection([PeakTable(columns=["mz"])], item_type=PeakTable)
try:
    MergeCollection().execute(left=coll_a, right=coll_peak)
    print("ERROR: should have rejected DataFrame + PeakTable")
except TypeError as e:
    print(f"Mixed merge rejected: {e}")

# 3. SliceCollection
from scieasy.blocks.collection.slice import SliceCollection
sliced = SliceCollection().execute(collection=merged, start=1, end=3)
print(f"Sliced [1:3]: {len(sliced)} items")
# Expected: 2

# 4. FilterCollection
from scieasy.blocks.collection.filter import FilterCollection
filtered = FilterCollection().execute(
    collection=merged,
    predicate=lambda item: True  # keep all
)
print(f"Filtered (keep all): {len(filtered)} items")
# Expected: 5

# 5. SplitCollection
from scieasy.blocks.collection.split import SplitCollection
left, right = SplitCollection().execute(collection=merged, split_index=2)
print(f"Split at 2: left={len(left)}, right={len(right)}")
# Expected: left=2, right=3
```

**Verdict**: [ ] PASS / [ ] FAIL

---

# PHASE 6: Workflow Definition + CLI

---

## P6-H01: YAML Serialization Round-Trip

**What**: Verify workflow YAML save/load preserves all data.

```bash
mkdir -p /tmp/scieasy_test
python
```
```python
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.workflow.serializer import save_yaml, load_yaml

workflow = WorkflowDefinition(
    id="raman-pipeline",
    version="1.0.0",
    description="Raman preprocessing pipeline",
    nodes=[
        NodeDef(id="load", block_type="io_block",
                config={"direction": "input", "path": "data/spectra.csv", "format": "csv"}),
        NodeDef(id="baseline", block_type="process_block",
                config={"method": "als", "lam": 1e5}),
        NodeDef(id="normalize", block_type="process_block",
                config={"method": "snv"}),
        NodeDef(id="save", block_type="io_block",
                config={"direction": "output", "path": "results/processed.parquet"}),
    ],
    edges=[
        EdgeDef(source="load:data", target="baseline:input"),
        EdgeDef(source="baseline:output", target="normalize:input"),
        EdgeDef(source="normalize:output", target="save:data"),
    ],
    metadata={"author": "test", "created": "2026-04-04"},
)

# Save
save_yaml(workflow, "/tmp/scieasy_test/pipeline.yaml")
print("Saved YAML")

# Load
loaded = load_yaml("/tmp/scieasy_test/pipeline.yaml")
print(f"Loaded: {loaded.id}, {len(loaded.nodes)} nodes, {len(loaded.edges)} edges")
# Expected: raman-pipeline, 4 nodes, 3 edges

# Verify round-trip
assert loaded.id == workflow.id
assert loaded.description == workflow.description
assert len(loaded.nodes) == len(workflow.nodes)
assert len(loaded.edges) == len(workflow.edges)
assert loaded.nodes[1].config["method"] == "als"
print("YAML round-trip: OK")
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P6-H02: Workflow Validation — Type Mismatch + Dangling Port

**What**: Verify validate_workflow() catches type errors and structural issues.

```python
python
```
```python
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.workflow.validator import validate_workflow

# 1. Valid workflow — should pass
valid = WorkflowDefinition(
    id="valid",
    nodes=[
        NodeDef(id="A", block_type="process_block", config={}),
        NodeDef(id="B", block_type="process_block", config={}),
    ],
    edges=[EdgeDef(source="A:output", target="B:input")],
)

errors = validate_workflow(valid)
print(f"Valid workflow errors: {errors}")
# Expected: [] (no errors)

# 2. Dangling port — edge references non-existent node
bad_ref = WorkflowDefinition(
    id="bad-ref",
    nodes=[NodeDef(id="A", block_type="process_block", config={})],
    edges=[EdgeDef(source="A:output", target="MISSING:input")],
)

errors = validate_workflow(bad_ref)
print(f"Dangling port errors: {errors}")
# Expected: at least one error about 'MISSING' node not found

# 3. Cycle detection via validator
cycle_wf = WorkflowDefinition(
    id="cycle",
    nodes=[
        NodeDef(id="X", block_type="process_block", config={}),
        NodeDef(id="Y", block_type="process_block", config={}),
    ],
    edges=[
        EdgeDef(source="X:out", target="Y:in"),
        EdgeDef(source="Y:out", target="X:in"),
    ],
)

errors = validate_workflow(cycle_wf)
print(f"Cycle errors: {errors}")
# Expected: error about cycle detected
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P6-H03: CLI Smoke Tests

**What**: Verify all CLI commands work.

```bash
# Help
scieasy --help
# Expected: shows available commands

# Init project
scieasy init /tmp/scieasy_test_project
# Expected: creates directory structure
ls /tmp/scieasy_test_project/
# Expected: workflows/, data/, results/ or similar structure

# List blocks
scieasy blocks
# Expected: shows registered block types (io_block, process_block, code_block, etc.)

# Validate workflow (use the YAML from P6-H01)
scieasy validate /tmp/scieasy_test/pipeline.yaml
# Expected: "Valid ✓" or similar success message

# Validate invalid workflow
cat > /tmp/scieasy_test/bad.yaml << 'EOF'
id: bad-workflow
nodes:
  - id: A
    block_type: process_block
edges:
  - source: "A:output"
    target: "MISSING:input"
EOF

scieasy validate /tmp/scieasy_test/bad.yaml
# Expected: validation error about MISSING node

# Run workflow (headless)
scieasy run /tmp/scieasy_test/pipeline.yaml
# Expected: executes the pipeline and prints result summary
```

**Verdict**: [ ] PASS / [ ] FAIL

---

# PHASE 7: API Layer

---

## P7-H01: FastAPI Server Starts

**What**: Verify the API server starts and responds.

```bash
# Start server
scieasy serve &
SERVER_PID=$!
sleep 2

# Health check
curl -s http://localhost:8000/docs | head -20
# Expected: OpenAPI docs HTML

# List blocks
curl -s http://localhost:8000/api/blocks/ | python -m json.tool
# Expected: JSON with block list

kill $SERVER_PID
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P7-H02: Workflow CRUD via REST

**What**: Verify create, read, update, delete workflow endpoints.

```bash
# Start server (if not running)
scieasy serve &
sleep 2

# CREATE
curl -s -X POST http://localhost:8000/api/workflows/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-wf-1",
    "description": "Test workflow",
    "nodes": [{"id": "A", "block_type": "process_block", "config": {}}],
    "edges": []
  }' | python -m json.tool
# Expected: 200 with WorkflowResponse

# READ
curl -s http://localhost:8000/api/workflows/test-wf-1 | python -m json.tool
# Expected: returns the workflow we just created

# UPDATE
curl -s -X PUT http://localhost:8000/api/workflows/test-wf-1 \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-wf-1",
    "description": "Updated description",
    "nodes": [{"id": "A", "block_type": "process_block", "config": {}}],
    "edges": []
  }' | python -m json.tool
# Expected: 200 with updated description

# DELETE
curl -s -X DELETE http://localhost:8000/api/workflows/test-wf-1 -w "%{http_code}"
# Expected: 204

# Verify deleted
curl -s http://localhost:8000/api/workflows/test-wf-1 -w "\n%{http_code}"
# Expected: 404
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P7-H03: Execute Workflow via REST + Cancel (ADR-018)

**What**: Start a workflow, then cancel a block via REST.

```bash
# Create a workflow with a slow block
curl -s -X POST http://localhost:8000/api/workflows/ \
  -H "Content-Type: application/json" \
  -d '{
    "id": "cancel-test",
    "nodes": [
      {"id": "slow", "block_type": "process_block", "config": {"sleep_seconds": 30}},
      {"id": "next", "block_type": "process_block", "config": {}}
    ],
    "edges": [{"source": "slow:output", "target": "next:input"}]
  }'

# Execute
curl -s -X POST http://localhost:8000/api/workflows/cancel-test/execute
# Expected: 200, execution started

sleep 2

# Cancel the slow block
curl -s -X POST http://localhost:8000/api/workflows/cancel-test/blocks/slow/cancel \
  | python -m json.tool
# Expected: CancelPropagationResponse:
#   cancelled_blocks: ["slow"]
#   skipped_blocks: ["next"]
#   skip_reasons: {"next": "upstream block 'slow' was cancelled"}

# Cancel entire workflow
curl -s -X POST http://localhost:8000/api/workflows/cancel-test/cancel \
  | python -m json.tool
# Expected: CancelPropagationResponse with all blocks
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P7-H04: WebSocket — Live Block State Updates

**What**: Connect via WebSocket and receive real-time state changes.

```python
python
```
```python
import asyncio
import json
import websockets

async def test_websocket():
    # First, create and execute a workflow via REST
    import httpx
    async with httpx.AsyncClient() as client:
        await client.post("http://localhost:8000/api/workflows/", json={
            "id": "ws-test",
            "nodes": [
                {"id": "A", "block_type": "process_block", "config": {}},
                {"id": "B", "block_type": "process_block", "config": {}},
            ],
            "edges": [{"source": "A:output", "target": "B:input"}],
        })

    # Connect WebSocket
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        # Execute workflow
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8000/api/workflows/ws-test/execute")

        # Collect events for up to 10 seconds
        events = []
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                event = json.loads(msg)
                events.append(event)
                print(f"  WS event: {event['type']} block={event.get('block_id', '?')}")

                if event["type"] == "workflow_completed":
                    break
        except asyncio.TimeoutError:
            pass

    print(f"\nTotal events: {len(events)}")
    # Expected: BLOCK_READY, BLOCK_RUNNING, BLOCK_DONE for each block,
    #           then WORKFLOW_COMPLETED

    event_types = [e["type"] for e in events]
    print(f"Event types: {event_types}")

asyncio.run(test_websocket())
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P7-H05: WebSocket — Cancel via WebSocket (ADR-018 Bidirectional)

**What**: Send cancel command through WebSocket and verify response.

```python
python
```
```python
import asyncio
import json
import websockets
import httpx

async def test_ws_cancel():
    # Create workflow with slow block
    async with httpx.AsyncClient() as client:
        await client.post("http://localhost:8000/api/workflows/", json={
            "id": "ws-cancel",
            "nodes": [
                {"id": "slow", "block_type": "process_block", "config": {"sleep_seconds": 30}},
                {"id": "next", "block_type": "process_block", "config": {}},
            ],
            "edges": [{"source": "slow:output", "target": "next:input"}],
        })

    async with websockets.connect("ws://localhost:8000/ws") as ws:
        # Start execution
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8000/api/workflows/ws-cancel/execute")

        await asyncio.sleep(1)

        # Send cancel via WebSocket
        await ws.send(json.dumps({
            "type": "cancel_block",
            "workflow_id": "ws-cancel",
            "block_id": "slow",
        }))

        # Collect events
        events = []
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                event = json.loads(msg)
                events.append(event)
                print(f"  WS: {event['type']} block={event.get('block_id', '?')}")
        except asyncio.TimeoutError:
            pass

    # Should see BLOCK_CANCELLED for slow, BLOCK_SKIPPED for next
    types = [(e.get("block_id"), e["type"]) for e in events]
    print(f"\nEvents: {types}")

asyncio.run(test_ws_cancel())
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P7-H06: Connection Validation Endpoint

**What**: Verify port compatibility check.

```bash
curl -s -X POST http://localhost:8000/api/blocks/validate-connection \
  -H "Content-Type: application/json" \
  -d '{
    "source_block": "io_block",
    "source_port": "data",
    "target_block": "process_block",
    "target_port": "input"
  }' | python -m json.tool
# Expected: {"compatible": true} or {"compatible": false, "reason": "..."}
```

**Verdict**: [ ] PASS / [ ] FAIL

---

# PHASE 8: Frontend

---

## P8-H01: Frontend Dev Server Starts

**What**: Verify the React frontend starts and loads.

```bash
cd frontend
npm install
npm run dev &
sleep 5

# Check it's serving
curl -s http://localhost:5173/ | head -5
# Expected: HTML with React app root div

# Or open browser:
# http://localhost:5173/
# Expected: SciEasy workflow editor canvas loads
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## P8-H02: Block Palette — Load from Backend

**Steps**:
1. Start backend: `scieasy serve` (or `uvicorn scieasy.api.app:create_app --factory`)
2. Start frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173/ in browser

**Verify**:
- [ ] Block palette panel is visible (sidebar or drawer)
- [ ] Palette shows block categories (IO, Process, Code, App, AI, SubWorkflow)
- [ ] Clicking a category expands to show individual blocks
- [ ] Search box filters blocks by name
- [ ] "Reload blocks" button refreshes the list

**Verdict**: [ ] PASS / [ ] FAIL

---

## P8-H03: Drag-Drop Block onto Canvas

**Steps**:
1. From the block palette, drag an "IO Block" onto the canvas
2. Drag a "Process Block" next to it
3. Drag a second "Process Block"

**Verify**:
- [ ] Each block appears as a node on the canvas
- [ ] Each node shows the block type name
- [ ] Input and output ports are visible on the node
- [ ] Nodes can be repositioned by dragging

**Verdict**: [ ] PASS / [ ] FAIL

---

## P8-H04: Connect Blocks — Wire Drawing + Validation

**Steps**:
1. Place an IO Block (output port) and a Process Block (input port) on canvas
2. Click-drag from the IO Block's output port to the Process Block's input port
3. Try connecting two output ports together (invalid)

**Verify**:
- [ ] Valid connection draws a typed edge (may be color-coded by data type)
- [ ] Invalid connection is rejected (edge snaps back, error indicator, or toast)
- [ ] Backend validation is triggered (check Network tab for `/api/blocks/validate-connection`)

**Verdict**: [ ] PASS / [ ] FAIL

---

## P8-H05: Config Panel — Edit Block Parameters

**Steps**:
1. Click on a Process Block node on the canvas
2. A config panel should appear (right sidebar or modal)

**Verify**:
- [ ] Config panel shows block parameters as form fields
- [ ] Fields are auto-generated from JSON Schema (text inputs, dropdowns, numbers)
- [ ] Changing a value updates the block's config
- [ ] Port inspector shows input/output types and connection status

**Verdict**: [ ] PASS / [ ] FAIL

---

## P8-H06: Execute Workflow from Frontend

**Steps**:
1. Build a simple 2-block workflow on canvas (IO Block → Process Block)
2. Click "Run" button

**Verify**:
- [ ] Run button is visible and enabled
- [ ] After clicking Run, block state badges update in real-time:
  - First block: IDLE → RUNNING → DONE
  - Second block: IDLE → RUNNING → DONE
- [ ] A "workflow completed" indication appears
- [ ] Log stream viewer shows execution logs (check SSE connection)

**Verdict**: [ ] PASS / [ ] FAIL

---

## P8-H07: Cancel from Frontend (ADR-018)

**Steps**:
1. Build a workflow with a slow block (configure sleep or heavy computation)
2. Click "Run"
3. While the slow block is RUNNING, click its "Cancel" button

**Verify**:
- [ ] Cancel button appears on RUNNING blocks
- [ ] Cancelled block shows CANCELLED state (distinct visual: e.g., orange badge)
- [ ] Downstream blocks show SKIPPED state (distinct visual: e.g., grey badge)
- [ ] Independent branches continue execution normally
- [ ] Cancel propagation message shows which blocks were skipped and why

**Verdict**: [ ] PASS / [ ] FAIL

---

## P8-H08: Pause / Resume from Frontend

**Steps**:
1. Run a multi-block workflow
2. Click "Pause" while execution is in progress
3. Verify blocks stop after current block completes
4. Click "Resume"

**Verify**:
- [ ] Pause button is available during execution
- [ ] After pause: completed blocks show DONE, pending blocks stay IDLE
- [ ] Resume button appears after pause
- [ ] After resume: remaining blocks execute in correct order
- [ ] Final result is the same as uninterrupted execution

**Verdict**: [ ] PASS / [ ] FAIL

---

# CROSS-PHASE INTEGRATION TESTS

---

## INT-H01: Full Stack — YAML → CLI → API → Frontend Round-Trip

**What**: Verify a workflow defined in YAML can be used across all layers.

**Steps**:

```bash
# 1. Create YAML workflow
cat > /tmp/scieasy_integration/pipeline.yaml << 'EOF'
id: integration-test
description: "End-to-end integration test"
nodes:
  - id: load
    block_type: io_block
    config:
      direction: input
      path: /tmp/scieasy_integration/input.csv
      format: csv
  - id: process
    block_type: process_block
    config: {}
  - id: save
    block_type: io_block
    config:
      direction: output
      path: /tmp/scieasy_integration/output.parquet
      format: parquet
edges:
  - source: "load:data"
    target: "process:input"
  - source: "process:output"
    target: "save:data"
EOF

# 2. Validate via CLI
scieasy validate /tmp/scieasy_integration/pipeline.yaml
# Expected: Valid ✓

# 3. Run via CLI
scieasy run /tmp/scieasy_integration/pipeline.yaml
# Expected: Completes, output file created

# 4. Verify output
python -c "
import pyarrow.parquet as pq
t = pq.read_table('/tmp/scieasy_integration/output.parquet')
print(f'Rows: {t.num_rows}, Cols: {t.column_names}')
"

# 5. Start API server, import same YAML via REST
scieasy serve &
sleep 2
# POST the workflow via REST or load in frontend
# Execute via API
curl -s -X POST http://localhost:8000/api/workflows/integration-test/execute

# 6. Open frontend, verify same workflow is visible and executable
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## INT-H02: Collection Transport End-to-End (ADR-020 Scenario)

**What**: The Appendix A multimodal scenario — Load multiple files → Process →
Merge → Export, all using Collection transport.

```python
python
```
```python
import asyncio
import os

# 1. Create test input files
os.makedirs("/tmp/scieasy_collection_test", exist_ok=True)
for i in range(5):
    with open(f"/tmp/scieasy_collection_test/sample_{i}.csv", "w") as f:
        f.write("id,value\n")
        f.write(f"{i},{i * 10}\n")

# 2. Build workflow
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.scheduler import DAGScheduler

workflow = WorkflowDefinition(
    id="collection-e2e",
    nodes=[
        NodeDef(id="load", block_type="io_block",
                config={"direction": "input",
                        "path": "/tmp/scieasy_collection_test/",
                        "format": "csv", "glob": "*.csv"}),
        NodeDef(id="process", block_type="process_block", config={}),
        NodeDef(id="save", block_type="io_block",
                config={"direction": "output",
                        "path": "/tmp/scieasy_collection_test/merged.parquet"}),
    ],
    edges=[
        EdgeDef(source="load:data", target="process:input"),
        EdgeDef(source="process:output", target="save:data"),
    ],
)

# 3. Execute
scheduler = DAGScheduler(workflow)
result = asyncio.run(scheduler.execute())
print(f"Result: {result}")

# 4. Verify
#  - load should produce a Collection[DataFrame] with 5 items
#  - process should receive entire Collection, process internally
#  - save should write output
print(f"Output exists: {os.path.exists('/tmp/scieasy_collection_test/merged.parquet')}")
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## INT-H03: Subprocess Isolation — Block Crash Does Not Kill Engine

**What**: A block that crashes (segfault, OOM, uncaught exception) should not
bring down the engine process.

```python
python
```
```python
import asyncio
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.scheduler import DAGScheduler

# Block that deliberately crashes
workflow = WorkflowDefinition(
    id="crash-test",
    nodes=[
        NodeDef(id="good", block_type="process_block", config={}),
        NodeDef(id="crasher", block_type="code_block",
                config={"language": "python", "mode": "inline",
                        "code": "import sys; sys.exit(1)"}),
        NodeDef(id="after_crash", block_type="process_block", config={}),
    ],
    edges=[
        EdgeDef(source="good:output", target="crasher:input"),
        EdgeDef(source="crasher:output", target="after_crash:input"),
    ],
)

scheduler = DAGScheduler(workflow)
result = asyncio.run(scheduler.execute())

# Engine should still be alive!
print(f"Engine survived crash: True")
print(f"Result: {result}")
# Expected: crasher=ERROR, after_crash=SKIPPED, workflow completed with partial failure
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## INT-H04: Cross-Platform Process Termination

**What**: Verify subprocess termination works on current OS.

```python
python
```
```python
import asyncio
import sys
import platform
from scieasy.engine.process_handle import spawn_block_process
from scieasy.engine.process_registry import ProcessRegistry

registry = ProcessRegistry()
print(f"Platform: {platform.system()}")

async def test_terminate():
    # Spawn a stubborn process
    handle = await spawn_block_process(
        block_id="stubborn",
        command=[sys.executable, "-c",
                 "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(999)"],
        registry=registry,
    )

    print(f"PID {handle.pid} alive: {handle.is_alive()}")

    # Graceful terminate (should escalate to kill on timeout)
    await handle.terminate(timeout=3.0)
    print(f"After terminate: alive={handle.is_alive()}")
    # Expected: False — should have been killed after grace period

asyncio.run(test_terminate())
```

**Verdict (Windows)**: [ ] PASS / [ ] FAIL
**Verdict (macOS)**: [ ] PASS / [ ] FAIL
**Verdict (Linux)**: [ ] PASS / [ ] FAIL

---

# VERIFICATION CHECKLIST

| # | Phase | Check | Result |
|---|-------|-------|--------|
| 1 | 5 | Collection homogeneity enforced | [ ] |
| 2 | 5 | Three-tier block authoring works | [ ] |
| 3 | 5 | LazyList loads on demand | [ ] |
| 4 | 5 | EventBus pub/sub + error isolation | [ ] |
| 5 | 5 | DAG builds from WorkflowDefinition | [ ] |
| 6 | 5 | Cycle detection works | [ ] |
| 7 | 5 | Linear pipeline executes end-to-end | [ ] |
| 8 | 5 | Diamond DAG executes correctly | [ ] |
| 9 | 5 | Cancel block → CANCELLED + SKIPPED | [ ] |
| 10 | 5 | Cancel one branch, other continues | [ ] |
| 11 | 5 | ProcessHandle spawn/terminate/kill | [ ] |
| 12 | 5 | ProcessMonitor detects crash | [ ] |
| 13 | 5 | ResourceManager psutil + slots | [ ] |
| 14 | 5 | Checkpoint save/load round-trip | [ ] |
| 15 | 5 | Pause → checkpoint → resume | [ ] |
| 16 | 5 | Collection operation blocks | [ ] |
| 17 | 6 | YAML round-trip | [ ] |
| 18 | 6 | Workflow validation catches errors | [ ] |
| 19 | 6 | CLI commands work | [ ] |
| 20 | 7 | API server starts | [ ] |
| 21 | 7 | Workflow CRUD REST | [ ] |
| 22 | 7 | Execute + cancel via REST | [ ] |
| 23 | 7 | WebSocket state updates | [ ] |
| 24 | 7 | WebSocket cancel (bidirectional) | [ ] |
| 25 | 7 | Connection validation endpoint | [ ] |
| 26 | 8 | Frontend dev server starts | [ ] |
| 27 | 8 | Block palette loads from backend | [ ] |
| 28 | 8 | Drag-drop block onto canvas | [ ] |
| 29 | 8 | Wire drawing + validation | [ ] |
| 30 | 8 | Config panel auto-form | [ ] |
| 31 | 8 | Execute workflow from frontend | [ ] |
| 32 | 8 | Cancel from frontend (ADR-018) | [ ] |
| 33 | 8 | Pause/resume from frontend | [ ] |
| 34 | INT | YAML → CLI → API → Frontend | [ ] |
| 35 | INT | Collection transport end-to-end | [ ] |
| 36 | INT | Block crash doesn't kill engine | [ ] |
| 37 | INT | Cross-platform process termination | [ ] |

---

# CLEANUP

```bash
rm -rf /tmp/scieasy_test
rm -rf /tmp/scieasy_test_project
rm -rf /tmp/scieasy_collection_test
rm -rf /tmp/scieasy_integration
rm -f /tmp/scieasy_test_checkpoint.json
rm -f /tmp/scieasy_resume_test.json
```
