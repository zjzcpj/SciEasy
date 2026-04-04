# Phase 5: Execution Engine — Human Test Plan

> **Status**: Phase 5 is PLANNED (not yet implemented).
> This document provides step-by-step manual verification procedures for humans
> to confirm the execution engine works correctly: DAG scheduling, Collection
> transport (ADR-020), subprocess isolation (ADR-017), cancellation (ADR-018),
> process lifecycle (ADR-019), resource management, checkpoint/resume, and event bus.

---

## 1. Prerequisites

| Requirement | Version | How to Check |
|-------------|---------|--------------|
| Python | 3.11+ | `python --version` |
| SciEasy installed | dev | `python -c "import scieasy"` |
| Phase 4 tests passing | All green | `pytest tests/blocks/ -q` |
| numpy | any | `python -c "import numpy"` |
| pyarrow | 15.0+ | `python -c "import pyarrow"` |

---

## 2. Environment Setup

```bash
cd SciEasy
git checkout main
git pull origin main
pip install -e ".[dev]"

# Verify prerequisites pass
pytest tests/core/ tests/blocks/ -q
```

**Expected**: All Phase 3 and 4 tests pass.

---

## 3. Manual Test Procedures

### Test 1: Run All Phase 5 Automated Tests

**Steps**:
```bash
pytest tests/engine/ -v --cov=scieasy.engine --cov-report=term-missing
```

**Expected**: All engine tests pass, coverage for `scieasy.engine` is visible.

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 2: Build a DAG from Workflow Definition

**Steps**:
```bash
python
```
```python
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.dag import build_dag, topological_sort

# Define a simple 3-block pipeline: Load -> Process -> Save
workflow = WorkflowDefinition(
    nodes=[
        NodeDef(id="loader", block_type="io_block", config={"direction": "input"}),
        NodeDef(id="processor", block_type="process_merge", config={}),
        NodeDef(id="saver", block_type="io_block", config={"direction": "output"}),
    ],
    edges=[
        EdgeDef(source_node="loader", source_port="data",
                target_node="processor", target_port="left"),
        EdgeDef(source_node="processor", source_port="merged",
                target_node="saver", target_port="data"),
    ],
)

dag = build_dag(workflow)
print(f"Nodes: {len(dag.nodes)}")
# Expected: 3
print(f"Edges: {len(dag.edges)}")
# Expected: 2

# Topological sort
order = topological_sort(dag)
print(f"Execution order: {[n.id for n in order]}")
# Expected: ['loader', 'processor', 'saver']

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 3: Detect Cycles in Workflow

**Steps**:
```bash
python
```
```python
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.dag import build_dag, topological_sort

# Define a workflow with a cycle: A -> B -> C -> A
workflow = WorkflowDefinition(
    nodes=[
        NodeDef(id="A", block_type="process_merge", config={}),
        NodeDef(id="B", block_type="process_merge", config={}),
        NodeDef(id="C", block_type="process_merge", config={}),
    ],
    edges=[
        EdgeDef(source_node="A", source_port="merged", target_node="B", target_port="left"),
        EdgeDef(source_node="B", source_port="merged", target_node="C", target_port="left"),
        EdgeDef(source_node="C", source_port="merged", target_node="A", target_port="left"),
    ],
)

dag = build_dag(workflow)

try:
    order = topological_sort(dag)
    print("ERROR: Should have raised CycleError!")
except Exception as e:
    print(f"Cycle detected: {e}")
    # Expected: CycleError or ValueError about cycle

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 4: Execute a Linear Pipeline

**Steps**:

1. Create test data:
```bash
mkdir -p /tmp/scieasy_engine_test
cat > /tmp/scieasy_engine_test/input.csv << 'EOF'
metabolite,mz,intensity
Glucose,180.063,1500
Lactate,89.024,2300
Pyruvate,87.008,890
EOF
```

2. Execute the pipeline:
```bash
python
```
```python
import asyncio
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef
from scieasy.engine.scheduler import DAGScheduler

# Build a Load -> Process -> Save workflow
workflow = WorkflowDefinition(
    nodes=[
        NodeDef(id="load", block_type="io_block",
                config={"direction": "input", "path": "/tmp/scieasy_engine_test/input.csv", "format": "csv"}),
        NodeDef(id="process", block_type="process_merge", config={}),
        NodeDef(id="save", block_type="io_block",
                config={"direction": "output", "path": "/tmp/scieasy_engine_test/output.parquet", "format": "parquet"}),
    ],
    edges=[
        EdgeDef(source_node="load", source_port="data",
                target_node="process", target_port="left"),
        EdgeDef(source_node="process", source_port="merged",
                target_node="save", target_port="data"),
    ],
)

scheduler = DAGScheduler(workflow)

# Execute
result = asyncio.run(scheduler.execute())
print(f"Workflow completed: {result}")

# Check output exists
import os
print(f"Output exists: {os.path.exists('/tmp/scieasy_engine_test/output.parquet')}")
# Expected: True

exit()
```

3. Verify the output:
```bash
python -c "
import pyarrow.parquet as pq
table = pq.read_table('/tmp/scieasy_engine_test/output.parquet')
print(f'Rows: {table.num_rows}')
print(f'Columns: {table.column_names}')
print(table.to_pandas())
"
```

**Expected**: Output Parquet file contains the same data as input CSV.

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 5: Pause and Resume Workflow

**Steps**:
```bash
python
```
```python
import asyncio
from scieasy.engine.scheduler import DAGScheduler
from scieasy.engine.checkpoint import WorkflowCheckpoint

# Build a 3-block workflow
# (Use same workflow as Test 4, or a mock workflow)

scheduler = DAGScheduler(workflow)

# Start execution, then pause after first block
# (Implementation may vary — adjust based on actual API)
async def run_with_pause():
    # Start
    task = asyncio.create_task(scheduler.execute())

    # Wait briefly for first block to complete
    await asyncio.sleep(1)

    # Pause
    checkpoint = await scheduler.pause()
    print(f"Paused. Checkpoint block states: {checkpoint.block_states}")

    # Save checkpoint
    checkpoint.save("/tmp/scieasy_engine_test/checkpoint.json")
    print("Checkpoint saved.")

    # Resume from checkpoint
    loaded = WorkflowCheckpoint.load("/tmp/scieasy_engine_test/checkpoint.json")
    scheduler2 = DAGScheduler(workflow)
    result = await scheduler2.resume(loaded)
    print(f"Resumed and completed: {result}")

asyncio.run(run_with_pause())
exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 6: Checkpoint Save/Load Round-Trip

**Steps**:
```bash
python
```
```python
from scieasy.engine.checkpoint import WorkflowCheckpoint

# Create a checkpoint
checkpoint = WorkflowCheckpoint(
    block_states={"load": "DONE", "process": "RUNNING", "save": "IDLE"},
    intermediate_refs={"load_output": "ref://storage/load_result"},
    pending_block="process",
    config_snapshot={"load": {"path": "/data/input.csv"}, "process": {}, "save": {}},
)

# Save to disk
checkpoint.save("/tmp/scieasy_engine_test/test_checkpoint.json")
print("Saved checkpoint")

# Load back
loaded = WorkflowCheckpoint.load("/tmp/scieasy_engine_test/test_checkpoint.json")
print(f"Block states: {loaded.block_states}")
# Expected: {'load': 'DONE', 'process': 'RUNNING', 'save': 'IDLE'}

print(f"Pending block: {loaded.pending_block}")
# Expected: process

print(f"Intermediate refs: {loaded.intermediate_refs}")
# Expected: {'load_output': 'ref://storage/load_result'}

# Verify data integrity
assert loaded.block_states == checkpoint.block_states
assert loaded.pending_block == checkpoint.pending_block
print("Checkpoint round-trip: OK")

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 7: Event Bus

**Steps**:
```bash
python
```
```python
from scieasy.engine.events import EventBus, EngineEvent

bus = EventBus()
received_events = []

# Subscribe to block_state_changed events
def on_state_change(event):
    received_events.append(event)
    print(f"  Event: {event.type} -> {event.data}")

bus.subscribe("block_state_changed", on_state_change)

# Emit some events
bus.emit(EngineEvent(type="block_state_changed", data={"block": "A", "state": "RUNNING"}))
bus.emit(EngineEvent(type="block_state_changed", data={"block": "A", "state": "DONE"}))
bus.emit(EngineEvent(type="workflow_complete", data={}))  # Different type, should NOT trigger

print(f"\nReceived {len(received_events)} events")
# Expected: 2 (only block_state_changed, not workflow_complete)

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 8: Resource Manager

**Steps**:
```bash
python
```
```python
from scieasy.engine.resources import ResourceManager, ResourceRequest

# Create a resource manager with limited resources
mgr = ResourceManager(cpu_workers=4, gpu_slots=1, memory_mb=4096)

print(f"Available CPU: {mgr.available_cpu}")
# Expected: 4
print(f"Available GPU: {mgr.available_gpu}")
# Expected: 1

# Acquire some resources
req = ResourceRequest(cpu=2, gpu=1, memory_mb=2048)
token = mgr.acquire(req)
print(f"After acquire — CPU: {mgr.available_cpu}, GPU: {mgr.available_gpu}")
# Expected: CPU: 2, GPU: 0

# Release
mgr.release(token)
print(f"After release — CPU: {mgr.available_cpu}, GPU: {mgr.available_gpu}")
# Expected: CPU: 4, GPU: 1

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 9: Collection Transport and Block-Internal Iteration (ADR-020)

**Steps**:

1. Create multiple input files:
```bash
for i in 1 2 3 4 5; do
  cat > /tmp/scieasy_engine_test/item_${i}.csv << EOF
id,value
${i},$(( i * 10 ))
EOF
done
ls /tmp/scieasy_engine_test/item_*.csv
```

2. Test Collection-based data transport:
```bash
python
```
```python
from scieasy.core.types.collection import Collection
from scieasy.core.types.dataframe import DataFrame

# Load 5 items into a Collection
items = [DataFrame(columns=["id", "value"]) for _ in range(5)]
coll = Collection(items)
print(f"Collection[{coll.item_type.__name__}] length={len(coll)}")
# Expected: Collection[DataFrame] length=5

# Test pack/unpack round-trip
from scieasy.blocks.base.block import Block
unpacked = Block.unpack(coll)
repacked = Block.pack(unpacked)
print(f"Round-trip: {len(repacked)} items")
# Expected: 5 items

# Test map_items
transformed = Block.map_items(lambda x: x, coll)
print(f"Mapped: {len(transformed)} items")
# Expected: 5 items

# Test homogeneity enforcement
from scieasy.core.types.array import Image
try:
    bad = Collection([items[0], Image()])
    print("ERROR: should have raised TypeError")
except TypeError as e:
    print(f"Correctly rejected mixed types: {e}")

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

### Test 10: Integration — Full Pipeline with Lineage

**Steps**:
```bash
python
```
```python
import asyncio
from scieasy.engine.scheduler import DAGScheduler
from scieasy.core.lineage.store import LineageStore

# Build and execute a pipeline
# (Use workflow from Test 4)

# After execution, check lineage
# store = LineageStore("/tmp/scieasy_engine_test/lineage.db")
# records = store.query_all("process")
# print(f"Lineage records: {len(records)}")
# Expected: >= 1

# Trace provenance
# ancestors = store.ancestors("final_output_hash")
# print(f"Ancestors: {len(ancestors)}")
# Expected: traces back through all blocks

exit()
```

**Verdict**: [ ] PASS / [ ] FAIL

---

## 4. Exploratory Test Scenarios

### Scenario A: Large Collection Processing (ADR-020)
Create a Collection[Image] with 100+ items. Pass through a 3-block pipeline where
the block uses `parallel_map()` internally. Measure:
- Total execution time
- Memory usage (does Collection + lazy loading keep it bounded?)
- Are all results correct?

### Scenario B: Cancel Block Mid-Execution (ADR-018)
1. Start a pipeline with a slow block (e.g., sleep 60s in a ProcessBlock)
2. Cancel the block via API or WebSocket
3. Verify: block → CANCELLED, downstream → SKIPPED, unrelated branches → continue
4. Verify: ProcessHandle.terminate() killed the subprocess

### Scenario C: External App Crash Detection (ADR-019)
1. Start an AppBlock that launches an external process
2. Kill the external process via OS task manager
3. Verify: ProcessMonitor detects exit, block → ERROR, downstream → SKIPPED
4. Verify: no orphan processes left

### Scenario D: Concurrent Workflows
Start two workflows simultaneously. Do they interfere with each other?
Do resource limits prevent over-allocation?

### Scenario E: Long-Running Workflow with Checkpoint
1. Start a pipeline with 10+ blocks
2. Pause mid-way through
3. Close terminal / restart Python
4. Resume from checkpoint
5. Verify final results match a full uninterrupted execution

---

## 5. Verification Checklist

| # | Check | Result |
|---|-------|--------|
| 1 | `pytest tests/engine/` all pass | [ ] |
| 2 | DAG builds correctly from WorkflowDefinition | [ ] |
| 3 | Topological sort produces correct execution order | [ ] |
| 4 | Cycle detection catches circular dependencies | [ ] |
| 5 | Linear pipeline executes end-to-end | [ ] |
| 6 | Branching pipeline (fan-out) works | [ ] |
| 7 | Diamond pipeline (fan-in) works | [ ] |
| 8 | Checkpoint saves and loads correctly | [ ] |
| 9 | Pause + resume produces correct results | [ ] |
| 10 | Event bus delivers events to subscribers | [ ] |
| 11 | Resource manager tracks CPU/GPU/memory | [ ] |
| 12 | Collection transport: pack/unpack/map_items work (ADR-020) | [ ] |
| 13 | Collection homogeneity enforced (mixed types rejected) | [ ] |
| 14 | Cancel block → CANCELLED + downstream SKIPPED (ADR-018) | [ ] |
| 15 | Lineage recorded for all block executions | [ ] |
| 16 | Integration test: full pipeline with lineage | [ ] |

---

## 6. Cleanup

```bash
# Remove test data
rm -rf /tmp/scieasy_engine_test

# Remove any leftover checkpoint files
rm -f /tmp/*.json
```
