# Phase 5: Execution Engine — AI Test Plan

> **Status**: Phase 5 is PLANNED (not yet implemented).
> This document specifies the automated tests that must be written when
> Phase 5 is implemented: DAG scheduling, Collection transport (ADR-020),
> subprocess isolation (ADR-017), cancellation (ADR-018), process lifecycle
> (ADR-019), resource management, checkpoint/resume, and event bus.

---

## 1. Overview

| Component | Source Module | Test File (to create) |
|-----------|-------------|-----------|
| DAG construction | `src/scieasy/engine/dag.py` | `tests/engine/test_dag.py` |
| Scheduler | `src/scieasy/engine/scheduler.py` | `tests/engine/test_scheduler.py` |
| Collection transport | `src/scieasy/core/types/collection.py` | `tests/core/test_collection.py` |
| Process lifecycle | `src/scieasy/engine/runners/process_handle.py` | `tests/engine/test_process_handle.py` |
| Resource manager | `src/scieasy/engine/resources.py` | `tests/engine/test_resources.py` |
| Checkpoint | `src/scieasy/engine/checkpoint.py` | `tests/engine/test_checkpoint.py` |
| Event bus | `src/scieasy/engine/events.py` | `tests/engine/test_events.py` |
| Block runner | `src/scieasy/engine/runners/` | `tests/engine/test_runners.py` |
| Integration | N/A | `tests/integration/test_multimodal_workflow.py` |

---

## 2. Unit Tests

### 2.1 `tests/engine/test_dag.py`

```python
# --- DAG Construction ---

def test_build_dag_linear():
    """Three blocks A -> B -> C produce a DAG with 3 nodes, 2 edges."""
    from scieasy.engine.dag import build_dag
    from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef

    workflow = WorkflowDefinition(
        nodes=[
            NodeDef(id="A", block_type="io_block", config={}),
            NodeDef(id="B", block_type="process_merge", config={}),
            NodeDef(id="C", block_type="io_block", config={}),
        ],
        edges=[
            EdgeDef(source_node="A", source_port="data", target_node="B", target_port="left"),
            EdgeDef(source_node="B", source_port="merged", target_node="C", target_port="data"),
        ],
    )
    dag = build_dag(workflow)
    assert len(dag.nodes) == 3
    assert len(dag.edges) == 2

def test_build_dag_branching():
    """A -> B and A -> C (fan-out)."""
    # Verify DAG has 3 nodes with A having 2 successors

def test_build_dag_diamond():
    """A -> B, A -> C, B -> D, C -> D (diamond merge)."""
    # Verify DAG has 4 nodes with D having 2 predecessors

def test_build_dag_single_node():
    """Single node, no edges."""
    # Verify DAG has 1 node, 0 edges

def test_build_dag_empty():
    """Empty workflow produces empty DAG."""
    # Verify DAG has 0 nodes, 0 edges

# --- Topological Sort ---

def test_topological_sort_linear():
    """A -> B -> C sorted as [A, B, C]."""
    from scieasy.engine.dag import topological_sort
    # Build DAG, sort, assert order

def test_topological_sort_branching():
    """A -> B, A -> C: A comes first, B and C in any order."""
    # Assert A is before both B and C

def test_topological_sort_diamond():
    """A -> B, A -> C, B -> D, C -> D: A first, D last."""
    # Assert A is first, D is last

def test_topological_sort_cycle_detected():
    """A -> B -> C -> A raises CycleError."""
    from scieasy.engine.dag import topological_sort, CycleError
    # Build cyclic DAG, assert raises CycleError

def test_topological_sort_self_loop():
    """A -> A raises CycleError."""
    # Build self-loop, assert raises CycleError

# --- DAG Queries ---

def test_dag_predecessors():
    """Query predecessors of a node."""
    # A -> B -> C: predecessors(C) = [B]

def test_dag_successors():
    """Query successors of a node."""
    # A -> B -> C: successors(A) = [B]

def test_dag_root_nodes():
    """Nodes with no predecessors are root nodes."""
    # A -> B, C -> B: roots = [A, C]

def test_dag_leaf_nodes():
    """Nodes with no successors are leaf nodes."""
    # A -> B, A -> C: leaves = [B, C]
```

### 2.2 `tests/engine/test_scheduler.py`

```python
# --- DAGScheduler ---

@pytest.mark.asyncio
async def test_scheduler_linear_pipeline():
    """Execute A -> B -> C: all blocks reach DONE."""
    from scieasy.engine.scheduler import DAGScheduler
    # Build workflow, create scheduler, execute
    # Assert all blocks in DONE state
    # Assert outputs of C match expected

@pytest.mark.asyncio
async def test_scheduler_branching_pipeline():
    """A -> B, A -> C: B and C both execute after A."""
    # Assert B and C both receive A's output
    # Assert both reach DONE

@pytest.mark.asyncio
async def test_scheduler_diamond_pipeline():
    """A -> B, A -> C, B -> D, C -> D: D receives from both B and C."""
    # Assert D receives both inputs
    # Assert all 4 blocks reach DONE

@pytest.mark.asyncio
async def test_scheduler_block_error_propagation():
    """If B fails, downstream blocks should not execute."""
    # A -> B -> C, B raises exception
    # Assert B is in ERROR state
    # Assert C is NOT in DONE state

@pytest.mark.asyncio
async def test_scheduler_readiness_check():
    """Block is ready only when all required inputs are available."""
    # A -> C, B -> C: C should not start until both A and B are done

@pytest.mark.asyncio
async def test_scheduler_empty_workflow():
    """Empty workflow completes immediately."""
    # No nodes, no edges: scheduler.execute() returns immediately

# --- Pause / Resume ---

@pytest.mark.asyncio
async def test_scheduler_pause():
    """Pause mid-execution: scheduler returns checkpoint."""
    # A -> B -> C: pause after A completes
    # Assert checkpoint contains A's results
    # Assert B and C are not yet started

@pytest.mark.asyncio
async def test_scheduler_resume_from_checkpoint():
    """Resume from checkpoint: skip completed blocks."""
    # Save checkpoint after A, resume
    # Assert B and C execute, A is skipped
    # Assert final results match full execution
```

### 2.3 `tests/core/test_collection.py` (ADR-020)

```python
# --- Collection construction and invariants ---

def test_collection_homogeneous():
    """Collection enforces homogeneous item types."""
    # Create Collection[Image] with 3 Images → OK
    # Attempt Collection with Image + DataFrame → TypeError

def test_collection_empty():
    """Empty Collection is valid."""
    # Collection([], item_type=Image) → length=0

def test_collection_single_item():
    """Single item is Collection with length=1."""
    # Collection([one_image]) → length=1
    # unpack_single() returns the image

def test_collection_pack_unpack_roundtrip():
    """pack() then unpack() returns original items."""
    # Block.pack(items) → Collection → Block.unpack() → same items

def test_collection_map_items():
    """map_items applies func to each item."""
    # Block.map_items(lambda x: transform(x), collection)
    # Assert result is Collection with transformed items

def test_collection_storage_refs():
    """storage_refs() returns list of StorageReference for cross-process serialisation."""
    # Each item has storage_ref → collection.storage_refs() returns [ref1, ref2, ...]

# --- Collection type checking ---

def test_port_accepts_collection():
    """Port with accepted_types=[Image] accepts Collection[Image]."""
    # validate_connection(source=Collection[Image], target=Image port) → OK

def test_port_rejects_wrong_collection():
    """Port with accepted_types=[Image] rejects Collection[DataFrame]."""
    # validate_connection(source=Collection[DataFrame], target=Image port) → Error

@pytest.mark.asyncio
async def test_batch_result_accumulation():
    """BatchResult tracks succeeded, failed, skipped counts."""
    # Run batch with some failures
    # Assert BatchResult fields are accurate
```

### 2.4 `tests/engine/test_resources.py`

```python
# --- ResourceManager ---

def test_acquire_release_cpu():
    """Acquire CPU workers, release them, verify count."""
    from scieasy.engine.resources import ResourceManager, ResourceRequest
    mgr = ResourceManager(cpu_workers=4, gpu_slots=0, memory_mb=8192)

    req = ResourceRequest(cpu=2)
    token = mgr.acquire(req)
    assert mgr.available_cpu == 2

    mgr.release(token)
    assert mgr.available_cpu == 4

def test_acquire_release_gpu():
    """Acquire GPU slot, release it."""
    mgr = ResourceManager(cpu_workers=4, gpu_slots=2, memory_mb=8192)
    req = ResourceRequest(gpu=1)
    token = mgr.acquire(req)
    assert mgr.available_gpu == 1
    mgr.release(token)
    assert mgr.available_gpu == 2

def test_acquire_blocks_when_exhausted():
    """Acquire blocks or raises when resources exhausted."""
    mgr = ResourceManager(cpu_workers=1, gpu_slots=1, memory_mb=1024)
    req = ResourceRequest(gpu=1)
    token1 = mgr.acquire(req)
    # Second acquire should block or raise
    # (depends on implementation: blocking vs. exception)

def test_gpu_slot_exhaustion_forces_serial():
    """When GPU slots are exhausted, parallel dispatch falls back to serial."""
    # 10 items, 1 GPU slot
    # Assert items processed one at a time through GPU block

def test_memory_budget_enforcement():
    """Memory budget prevents over-allocation."""
    mgr = ResourceManager(cpu_workers=4, gpu_slots=0, memory_mb=100)
    req = ResourceRequest(memory_mb=60)
    token1 = mgr.acquire(req)
    # Second 60 MB request should block (only 40 MB remaining)
```

### 2.5 `tests/engine/test_checkpoint.py`

```python
# --- WorkflowCheckpoint ---

def test_checkpoint_save_load(tmp_path):
    """Save checkpoint to disk, load it back, verify contents."""
    from scieasy.engine.checkpoint import WorkflowCheckpoint
    checkpoint = WorkflowCheckpoint(
        block_states={"A": "DONE", "B": "RUNNING", "C": "IDLE"},
        intermediate_refs={"A_output": "ref://storage/a_result"},
        pending_block="B",
        config_snapshot={"A": {"param": 1}, "B": {"param": 2}},
    )
    path = tmp_path / "checkpoint.json"
    checkpoint.save(path)

    loaded = WorkflowCheckpoint.load(path)
    assert loaded.block_states == {"A": "DONE", "B": "RUNNING", "C": "IDLE"}
    assert loaded.pending_block == "B"

def test_checkpoint_skip_completed():
    """Resume from checkpoint skips blocks marked DONE."""
    # Checkpoint: A=DONE, B=IDLE, C=IDLE
    # Resume should start from B, not re-run A

@pytest.mark.asyncio
async def test_checkpoint_crash_recovery(tmp_path):
    """Simulate crash mid-execution, resume from checkpoint."""
    # Execute A -> B -> C
    # Save checkpoint after A completes
    # "Crash" (stop scheduler)
    # Resume from checkpoint
    # Assert B and C execute
    # Assert final result matches full execution

def test_checkpoint_data_integrity(tmp_path):
    """Checkpoint references point to valid stored data."""
    # Save checkpoint with storage references
    # Load checkpoint
    # Verify each storage reference can be read

@pytest.mark.asyncio
async def test_pause_creates_checkpoint():
    """DAGScheduler.pause() creates and returns a checkpoint."""
    # Start execution, pause after first block
    # Assert checkpoint is returned
    # Assert checkpoint has correct block states
```

### 2.6 `tests/engine/test_events.py`

```python
# --- EventBus ---

def test_event_bus_emit_subscribe():
    """Subscribe to event, emit it, callback receives event."""
    from scieasy.engine.events import EventBus, EngineEvent
    bus = EventBus()
    received = []
    bus.subscribe("block_state_changed", lambda e: received.append(e))
    bus.emit(EngineEvent(type="block_state_changed", data={"block": "A", "state": "DONE"}))
    assert len(received) == 1
    assert received[0].data["block"] == "A"

def test_event_bus_multiple_subscribers():
    """Multiple subscribers receive the same event."""
    bus = EventBus()
    r1, r2 = [], []
    bus.subscribe("progress", lambda e: r1.append(e))
    bus.subscribe("progress", lambda e: r2.append(e))
    bus.emit(EngineEvent(type="progress", data={"pct": 50}))
    assert len(r1) == 1
    assert len(r2) == 1

def test_event_bus_unsubscribe():
    """Unsubscribed callback no longer receives events."""
    bus = EventBus()
    received = []
    sub_id = bus.subscribe("test", lambda e: received.append(e))
    bus.unsubscribe(sub_id)
    bus.emit(EngineEvent(type="test", data={}))
    assert len(received) == 0

def test_event_bus_different_types():
    """Subscriber to type A does not receive type B events."""
    bus = EventBus()
    received = []
    bus.subscribe("type_a", lambda e: received.append(e))
    bus.emit(EngineEvent(type="type_b", data={}))
    assert len(received) == 0

@pytest.mark.asyncio
async def test_scheduler_emits_events():
    """DAGScheduler emits block_state_changed events during execution."""
    # Build workflow, subscribe to events, execute
    # Assert events received for each block state change

@pytest.mark.asyncio
async def test_scheduler_emits_workflow_complete():
    """DAGScheduler emits workflow_complete event when done."""
    # Execute workflow, assert workflow_complete event emitted

@pytest.mark.asyncio
async def test_scheduler_emits_workflow_error():
    """DAGScheduler emits workflow_error event on block failure."""
    # Execute workflow with failing block
    # Assert workflow_error event emitted
```

### 2.7 `tests/engine/test_runners.py`

```python
# --- LocalRunner ---

@pytest.mark.asyncio
async def test_local_runner_executes_block():
    """LocalRunner executes a block in-process."""
    from scieasy.engine.runners.local import LocalRunner
    # Create ProcessBlock, run via LocalRunner
    # Assert result matches expected

@pytest.mark.asyncio
async def test_local_runner_captures_error():
    """LocalRunner captures and reports block execution errors."""
    # Create block that raises
    # Run via LocalRunner
    # Assert error is captured, not swallowed

def test_local_runner_timeout():
    """LocalRunner enforces execution timeout."""
    # Create block that sleeps forever
    # Run with timeout
    # Assert TimeoutError or similar
```

---

## 3. Integration Tests

### File: `tests/integration/test_multimodal_workflow.py`

```python
@pytest.mark.asyncio
async def test_simplified_multimodal_pipeline(tmp_path):
    """
    Simplified version of Appendix A scenario:
    Load CSV -> Process (normalize) -> Split (80/20) -> Save outputs

    Tests DAG scheduling, data flow, lineage recording.
    """
    # 1. Create input CSV with metabolite data
    # 2. Build WorkflowDefinition with 4 nodes
    # 3. Execute via DAGScheduler
    # 4. Verify output files exist
    # 5. Verify lineage records exist for all blocks

@pytest.mark.asyncio
async def test_three_block_linear_pipeline(tmp_path):
    """IOBlock(load) -> ProcessBlock(merge) -> IOBlock(save)."""
    # Most basic multi-block test
    # Verify data flows correctly through all three blocks

@pytest.mark.asyncio
async def test_branching_pipeline(tmp_path):
    """
    Load -> Split (train/test)
         -> Process(train) -> Save
         -> Process(test) -> Save

    Tests fan-out execution.
    """

@pytest.mark.asyncio
async def test_pipeline_with_code_block(tmp_path):
    """
    IOBlock(load) -> CodeBlock(inline transform) -> IOBlock(save)

    Tests CodeBlock integration in a DAG.
    """

@pytest.mark.asyncio
async def test_pipeline_with_batch(tmp_path):
    """
    10 CSV files -> IOBlock(batch load) -> ProcessBlock(batch) -> Save

    Tests batch execution mode.
    """

@pytest.mark.asyncio
async def test_pipeline_checkpoint_resume(tmp_path):
    """
    A -> B -> C: pause after A, resume, verify final result.
    """
```

---

## 4. Edge Case / Regression Tests

```python
# Cycle detection
def test_cycle_in_complex_graph():
    """A -> B -> C -> D -> B: detect cycle even in longer loops."""

# Disconnected subgraphs
def test_disconnected_subgraphs():
    """Two independent chains: A->B and C->D. Both should execute."""

# Single block workflow
@pytest.mark.asyncio
async def test_single_block_workflow():
    """Workflow with just one block (no edges)."""

# Block with no outputs
@pytest.mark.asyncio
async def test_block_with_no_downstream():
    """Leaf block with no consumers still executes."""

# Batch with 0 items
@pytest.mark.asyncio
async def test_batch_zero_items():
    """Batch with empty input list completes with empty results."""

# Batch with 1 item
@pytest.mark.asyncio
async def test_batch_single_item():
    """Batch with one item behaves identically to non-batch."""

# Checkpoint with no completed blocks
def test_checkpoint_all_idle(tmp_path):
    """Checkpoint where all blocks are IDLE (workflow just started)."""

# Resource manager with zero resources
def test_resource_manager_zero_gpu():
    """ResourceManager with 0 GPU slots: GPU requests always block/fail."""
```

---

## 5. Comprehensive Agent Tests

```bash
# Run all Phase 5 tests
pytest tests/engine/ -v --cov=scieasy.engine --cov-report=term-missing

# Run DAG tests only
pytest tests/engine/test_dag.py -v

# Run scheduler tests only (async)
pytest tests/engine/test_scheduler.py -v

# Run batch tests only
pytest tests/engine/test_batch.py -v

# Run checkpoint tests only
pytest tests/engine/test_checkpoint.py -v

# Run integration tests
pytest tests/integration/ -v --cov=scieasy --cov-report=term-missing

# Full pipeline: all tests including engine + integration
pytest tests/ -v --cov=scieasy --cov-report=term-missing

# Full CI locally
make lint && make typecheck && make test
```

---

## 6. Coverage Targets

| Module | Tests | Target Coverage |
|--------|-------|-----------------|
| `engine/dag.py` | 14 | 90%+ |
| `engine/scheduler.py` | 8 | 85%+ |
| `engine/batch.py` | 8 | 85%+ |
| `engine/resources.py` | 5 | 80%+ |
| `engine/checkpoint.py` | 5 | 85%+ |
| `engine/events.py` | 7 | 90%+ |
| `engine/runners/` | 3 | 75%+ |
| Integration tests | 6 | N/A (cross-cutting) |
| **Total Phase 5** | **56** | **85%+ engine layer** |

---

## 7. Fixtures & Helpers

```python
# tests/engine/conftest.py
import pytest
from scieasy.workflow.definition import WorkflowDefinition, NodeDef, EdgeDef


@pytest.fixture
def linear_workflow():
    """A -> B -> C linear pipeline."""
    return WorkflowDefinition(
        nodes=[
            NodeDef(id="A", block_type="io_block", config={"direction": "input", "path": "..."}),
            NodeDef(id="B", block_type="process_merge", config={}),
            NodeDef(id="C", block_type="io_block", config={"direction": "output", "path": "..."}),
        ],
        edges=[
            EdgeDef(source_node="A", source_port="data", target_node="B", target_port="left"),
            EdgeDef(source_node="B", source_port="merged", target_node="C", target_port="data"),
        ],
    )


@pytest.fixture
def diamond_workflow():
    """A -> B, A -> C, B -> D, C -> D diamond."""
    return WorkflowDefinition(
        nodes=[
            NodeDef(id="A", block_type="io_block", config={}),
            NodeDef(id="B", block_type="process_merge", config={}),
            NodeDef(id="C", block_type="process_split", config={}),
            NodeDef(id="D", block_type="io_block", config={}),
        ],
        edges=[
            EdgeDef(source_node="A", source_port="data", target_node="B", target_port="left"),
            EdgeDef(source_node="A", source_port="data", target_node="C", target_port="data"),
            EdgeDef(source_node="B", source_port="merged", target_node="D", target_port="left"),
            EdgeDef(source_node="C", source_port="head", target_node="D", target_port="right"),
        ],
    )


@pytest.fixture
def cyclic_workflow():
    """A -> B -> C -> A (invalid, has cycle)."""
    return WorkflowDefinition(
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


class MockBlock:
    """A mock block for testing scheduler without real block execution."""
    def __init__(self, name, delay=0, should_fail=False):
        self.name = name
        self.delay = delay
        self.should_fail = should_fail
        self.state = "IDLE"
        self.call_count = 0

    async def run(self, inputs, config):
        self.call_count += 1
        if self.delay:
            import asyncio
            await asyncio.sleep(self.delay)
        if self.should_fail:
            raise RuntimeError(f"Block {self.name} intentionally failed")
        self.state = "DONE"
        return {"output": f"{self.name}_result"}
```

---

## 8. How to Run

```bash
# All Phase 5 tests
pytest tests/engine/ tests/integration/ -v --cov=scieasy.engine --cov-report=term-missing

# Quick smoke test
pytest tests/engine/ -x -q

# Only async tests
pytest tests/engine/ -k "async" -v

# With verbose debugging
pytest tests/engine/ -v -s --tb=long
```
