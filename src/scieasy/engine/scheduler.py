"""DAGScheduler -- event-driven workflow execution with cancellation and skip propagation.

ADR-018: Replaces the synchronous for-loop scheduler with an event-driven
architecture. Reacts to EventBus events, propagates SKIPPED to downstream
blocks with unsatisfiable inputs, and supports per-block and whole-workflow
cancellation.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from scieasy.blocks.base.state import BlockState
from scieasy.engine.dag import build_dag, topological_sort
from scieasy.engine.events import (
    BLOCK_CANCELLED,
    BLOCK_DONE,
    BLOCK_ERROR,
    BLOCK_RUNNING,
    BLOCK_SKIPPED,
    CANCEL_BLOCK_REQUEST,
    CANCEL_WORKFLOW_REQUEST,
    WORKFLOW_COMPLETED,
    WORKFLOW_STARTED,
    EngineEvent,
    EventBus,
)
from scieasy.engine.resources import ResourceRequest
from scieasy.workflow.definition import WorkflowDefinition

if TYPE_CHECKING:
    from scieasy.blocks.registry import BlockRegistry

logger = logging.getLogger(__name__)


@dataclass
class RunHandle:
    """Handle for a single block execution in progress.

    Fields:
        run_id: str -- unique identifier for this run.
        process_handle: ProcessHandle | None -- from engine.runners.process_handle.
            None when the run has not yet been dispatched.
        result: Any | None -- asyncio.Future[dict[str, Any]] or resolved dict.
            Resolves when the subprocess exits with output references.
    """

    run_id: str = ""
    process_handle: Any = None
    result: Any = None


class DAGScheduler:
    """Execute a workflow by reacting to EventBus events.

    The scheduler builds a DAG from the workflow definition, computes
    topological order, and dispatches blocks as their predecessors complete.
    On error or cancellation, downstream blocks are marked SKIPPED.

    Parameters
    ----------
    workflow:
        The workflow to execute.
    event_bus:
        EventBus instance for publish/subscribe coordination.
    resource_manager:
        ResourceManager for dispatch gating (can_dispatch check).
    process_registry:
        ProcessRegistry for active subprocess tracking.
    runner:
        BlockRunner implementation (e.g. LocalRunner) for executing blocks.
    registry:
        Optional BlockRegistry for resolving NodeDef.block_type to Block
        instances.  When provided, _dispatch instantiates a real Block
        before passing it to the runner.  When None (default), the raw
        NodeDef is forwarded.
    """

    def __init__(
        self,
        workflow: WorkflowDefinition,
        event_bus: EventBus,
        resource_manager: Any,
        process_registry: Any,
        runner: Any,
        registry: BlockRegistry | None = None,
    ) -> None:
        self._workflow = workflow
        self._event_bus = event_bus
        self._resource_manager = resource_manager
        self._process_registry = process_registry
        self._runner = runner
        self._registry = registry

        self._dag = build_dag(workflow)
        self._order = topological_sort(self._dag)

        # Block state tracking: IDLE -> READY -> RUNNING -> DONE/ERROR/CANCELLED/SKIPPED
        self._block_states: dict[str, BlockState] = {n: BlockState.IDLE for n in self._dag.nodes}
        self._block_outputs: dict[str, Any] = {}
        self.skip_reasons: dict[str, str] = {}

        self._completed_event = asyncio.Event()
        self._paused = False
        self._reset_lock = asyncio.Lock()

        # Subscribe to lifecycle events
        self._event_bus.subscribe(BLOCK_DONE, self._on_block_done)
        self._event_bus.subscribe(BLOCK_ERROR, self._on_block_error)
        self._event_bus.subscribe(CANCEL_BLOCK_REQUEST, self._on_cancel_block)
        self._event_bus.subscribe(CANCEL_WORKFLOW_REQUEST, self._on_cancel_workflow)

    async def execute(self) -> None:
        """Begin executing the workflow from its current state.

        Emits ``WORKFLOW_STARTED``, finds initially ready blocks (those with
        no predecessors), dispatches them, then waits until all blocks reach
        a terminal state before emitting ``WORKFLOW_COMPLETED``.
        """
        await self._event_bus.emit(EngineEvent(event_type=WORKFLOW_STARTED))

        # Handle empty workflow
        if not self._dag.nodes:
            self._completed_event.set()
            await self._event_bus.emit(EngineEvent(event_type=WORKFLOW_COMPLETED))
            return

        # Dispatch initially ready blocks (only those still idle)
        for node_id in self._order:
            if self._block_states[node_id] == BlockState.IDLE and self._check_readiness(node_id):
                self._block_states[node_id] = BlockState.READY
                await self._dispatch(node_id)

        # Wait until all blocks reach terminal state
        await self._completed_event.wait()

        await self._event_bus.emit(EngineEvent(event_type=WORKFLOW_COMPLETED))

    async def _dispatch(self, node_id: str) -> None:
        """Dispatch a single block for execution.

        Checks pause state and resource availability before running.
        Gathers inputs from upstream outputs, invokes the runner, stores
        the result, and emits the appropriate lifecycle event.
        """
        if self._paused:
            return

        if not self._resource_manager.can_dispatch(ResourceRequest()):
            # Will retry when resources free up (on next block_done)
            return

        self._block_states[node_id] = BlockState.RUNNING
        await self._event_bus.emit(EngineEvent(event_type=BLOCK_RUNNING, block_id=node_id))

        # Gather inputs from upstream outputs using edge_map
        inputs = self._gather_inputs(node_id)
        node = self._dag.nodes[node_id]
        config = node.config

        try:
            # Resolve NodeDef.block_type -> Block instance via registry (#119).
            block = (
                self._registry.instantiate(node.block_type, config)
                if self._registry is not None
                else node  # backward compat for tests with mock runners
            )
            result = await self._runner.run(block, inputs, config)
            self._block_outputs[node_id] = result
            self._block_states[node_id] = BlockState.DONE
            await self._event_bus.emit(
                EngineEvent(
                    event_type=BLOCK_DONE,
                    block_id=node_id,
                    data={"outputs": result},
                )
            )
        except Exception as exc:
            logger.exception("Block %s failed with exception", node_id)
            self._block_states[node_id] = BlockState.ERROR
            await self._event_bus.emit(
                EngineEvent(
                    event_type=BLOCK_ERROR,
                    block_id=node_id,
                    data={"error": str(exc)},
                )
            )

    def _gather_inputs(self, node_id: str) -> dict[str, Any]:
        """Collect inputs for *node_id* from upstream block outputs.

        Uses the DAG's ``edge_map`` to resolve which upstream output port
        feeds each input port. Returns a mapping of input port name to
        the corresponding output value.
        """
        inputs: dict[str, Any] = {}

        for edge in self._dag.edges:
            tgt_node, tgt_port = edge.target.split(":", 1)
            if tgt_node != node_id:
                continue

            src_node, src_port = edge.source.split(":", 1)
            upstream_outputs = self._block_outputs.get(src_node, {})
            if isinstance(upstream_outputs, dict) and src_port in upstream_outputs:
                inputs[tgt_port] = upstream_outputs[src_port]
            elif isinstance(upstream_outputs, dict):
                # If no specific port, pass entire output dict
                inputs[tgt_port] = upstream_outputs

        return inputs

    async def _on_block_done(self, event: EngineEvent) -> None:
        """Handle a block completion: find and dispatch newly ready blocks."""
        if event.block_id is None:
            return

        # Check all blocks that depend on the completed block
        for node_id in self._order:
            if self._block_states[node_id] != BlockState.IDLE:
                continue
            if self._check_readiness(node_id):
                self._block_states[node_id] = BlockState.READY
                await self._dispatch(node_id)

        self._check_completion()

    async def _on_block_error(self, event: EngineEvent) -> None:
        """Handle a block error: propagate skip to downstream blocks."""
        if event.block_id is None:
            return

        self._block_states[event.block_id] = BlockState.ERROR
        await self._propagate_skip(event.block_id, "error")
        self._check_completion()

    async def _on_cancel_block(self, event: EngineEvent) -> None:
        """Handle a block cancellation request.

        Terminates the subprocess if running, marks the block as CANCELLED,
        and propagates SKIPPED to downstream blocks.
        """
        if event.block_id is None:
            return

        block_id = event.block_id

        # Terminate the process if it's running
        if self._process_registry is not None:
            handle = self._process_registry.get_handle(block_id)
            if handle is not None:
                handle.terminate()

        # Cancel via runner if available
        if hasattr(self._runner, "cancel"):
            try:
                await self._runner.cancel(block_id)
            except Exception:
                logger.exception("Failed to cancel block %s via runner", block_id)

        self._block_states[block_id] = BlockState.CANCELLED
        await self._event_bus.emit(EngineEvent(event_type=BLOCK_CANCELLED, block_id=block_id))

        await self._propagate_skip(block_id, "cancelled")
        self._check_completion()

    async def _on_cancel_workflow(self, event: EngineEvent) -> None:
        """Handle a workflow cancellation: cancel all running blocks."""
        running_blocks = [bid for bid, state in self._block_states.items() if state == BlockState.RUNNING]

        for block_id in running_blocks:
            # Terminate the process
            if self._process_registry is not None:
                handle = self._process_registry.get_handle(block_id)
                if handle is not None:
                    handle.terminate()

            if hasattr(self._runner, "cancel"):
                try:
                    await self._runner.cancel(block_id)
                except Exception:
                    logger.exception(
                        "Failed to cancel block %s during workflow cancel",
                        block_id,
                    )

            self._block_states[block_id] = BlockState.CANCELLED
            await self._event_bus.emit(EngineEvent(event_type=BLOCK_CANCELLED, block_id=block_id))

        # Mark all remaining idle/ready blocks as skipped
        for block_id, state in list(self._block_states.items()):
            if state in (BlockState.IDLE, BlockState.READY):
                self._block_states[block_id] = BlockState.SKIPPED
                self.skip_reasons[block_id] = "workflow cancelled"
                await self._event_bus.emit(EngineEvent(event_type=BLOCK_SKIPPED, block_id=block_id))

        self._check_completion()

    async def _propagate_skip(self, failed_id: str, reason: str) -> None:
        """BFS downstream from *failed_id*, marking blocks SKIPPED.

        A block is skipped if any of its required predecessors has not
        produced output (i.e., is in a non-done terminal state).

        Parameters
        ----------
        failed_id:
            The block that failed or was cancelled.
        reason:
            Human-readable reason string (e.g. "error", "cancelled").
        """
        queue = list(self._dag.adjacency.get(failed_id, []))

        while queue:
            node_id = queue.pop(0)
            if self._block_states[node_id] in (
                BlockState.DONE,
                BlockState.ERROR,
                BlockState.CANCELLED,
                BlockState.SKIPPED,
            ):
                continue

            # Check if all predecessors have produced output
            predecessors = self._dag.reverse_adjacency.get(node_id, [])
            all_satisfied = all(self._block_states[p] == BlockState.DONE for p in predecessors)

            if not all_satisfied:
                self._block_states[node_id] = BlockState.SKIPPED
                self.skip_reasons[node_id] = f"upstream {failed_id} {reason}"
                await self._event_bus.emit(EngineEvent(event_type=BLOCK_SKIPPED, block_id=node_id))
                queue.extend(self._dag.adjacency.get(node_id, []))

    def _check_readiness(self, node_id: str) -> bool:
        """Return True if all predecessors of *node_id* are in DONE state."""
        predecessors = self._dag.reverse_adjacency.get(node_id, [])
        return all(self._block_states[p] == BlockState.DONE for p in predecessors)

    def _check_completion(self) -> None:
        """Set the completed event if all blocks are in a terminal state."""
        terminal = {BlockState.DONE, BlockState.ERROR, BlockState.CANCELLED, BlockState.SKIPPED}
        if all(s in terminal for s in self._block_states.values()):
            self._completed_event.set()

    async def pause(self) -> None:
        """Request a graceful pause after the current blocks complete."""
        self._paused = True

    async def resume(self) -> None:
        """Resume a previously paused workflow execution.

        Re-checks all idle blocks for readiness and dispatches any that
        are now ready.
        """
        self._paused = False

        for node_id in self._order:
            if self._block_states[node_id] == BlockState.IDLE and self._check_readiness(node_id):
                self._block_states[node_id] = BlockState.READY
                await self._dispatch(node_id)

    def set_state(self, block_id: str, state: BlockState) -> None:
        """Manually override the execution state of a single block.

        Parameters
        ----------
        block_id:
            The block whose state to override.
        state:
            The new BlockState value.
        """
        self._block_states[block_id] = state

    async def reset_block(self, block_id: str) -> None:
        """Reset a block and its dependency chain for selective re-run.

        Algorithm (ADR-018):
            1. Validate block exists.
            2. Set target block to IDLE, clear cached outputs and skip reasons.
            3. Walk upstream: recursively reset non-DONE predecessors to IDLE.
            4. Walk downstream: reset SKIPPED blocks to IDLE.
            5. Re-evaluate readiness and dispatch ready blocks.
        """
        async with self._reset_lock:
            if block_id not in self._block_states:
                raise ValueError(f"Unknown block: {block_id}")

            # Step 2: Reset target block.
            self._block_states[block_id] = "idle"
            self._block_outputs.pop(block_id, None)
            self.skip_reasons.pop(block_id, None)

            # Step 3: Walk upstream — recursively reset non-DONE predecessors.
            self._reset_upstream(block_id, visited=set())

            # Step 4: Walk downstream — reset SKIPPED blocks.
            self._reset_downstream_skipped(block_id)

            # Step 5: Re-evaluate and dispatch (batch ready blocks first).
            ready_blocks = []
            for node_id in self._order:
                if self._block_states[node_id] == "idle" and self._check_readiness(node_id):
                    self._block_states[node_id] = "ready"
                    ready_blocks.append(node_id)

            for node_id in ready_blocks:
                await self._dispatch(node_id)

    def _reset_upstream(self, block_id: str, visited: set[str]) -> None:
        """Recursively reset non-DONE upstream blocks to IDLE."""
        if block_id in visited:
            return
        visited.add(block_id)
        predecessors = self._dag.reverse_adjacency.get(block_id, [])
        for pred in predecessors:
            if self._block_states[pred] != "done":
                self._block_states[pred] = "idle"
                self._block_outputs.pop(pred, None)
                self.skip_reasons.pop(pred, None)
                self._reset_upstream(pred, visited)

    def _reset_downstream_skipped(self, block_id: str) -> None:
        """BFS downstream from block_id, reset SKIPPED blocks to IDLE."""
        queue = list(self._dag.adjacency.get(block_id, []))
        visited: set[str] = set()
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            if self._block_states[node_id] == "skipped":
                self._block_states[node_id] = "idle"
                self._block_outputs.pop(node_id, None)
                self.skip_reasons.pop(node_id, None)
                queue.extend(self._dag.adjacency.get(node_id, []))

    def save_checkpoint(self, checkpoint_manager: Any = None) -> None:
        """Persist the current execution state to durable storage.

        ADR-018: Delegates to CheckpointManager if provided.
        """
        if checkpoint_manager is None:
            return
        from datetime import datetime

        from scieasy.engine.checkpoint import WorkflowCheckpoint, serialize_intermediate_refs

        checkpoint = WorkflowCheckpoint(
            workflow_id=self._workflow.id if hasattr(self._workflow, "id") else "unknown",
            timestamp=datetime.now(),
            block_states={k: v.value for k, v in self._block_states.items()},
            intermediate_refs=serialize_intermediate_refs(self._block_outputs),
            skip_reasons=dict(self.skip_reasons),
        )
        checkpoint_manager.save(checkpoint)
