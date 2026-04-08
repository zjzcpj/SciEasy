"""DAGScheduler -- event-driven workflow execution with cancellation and skip propagation."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from scieasy.blocks.base.state import BlockState
from scieasy.engine.dag import build_dag, get_downstream_blocks, topological_sort
from scieasy.engine.events import (
    BLOCK_CANCELLED,
    BLOCK_DONE,
    BLOCK_ERROR,
    BLOCK_RUNNING,
    BLOCK_SKIPPED,
    CANCEL_BLOCK_REQUEST,
    CANCEL_WORKFLOW_REQUEST,
    PROCESS_EXITED,
    WORKFLOW_COMPLETED,
    WORKFLOW_STARTED,
    EngineEvent,
    EventBus,
)
from scieasy.engine.resources import ResourceRequest
from scieasy.workflow.definition import WorkflowDefinition

if TYPE_CHECKING:
    from scieasy.blocks.registry import BlockRegistry
    from scieasy.engine.lineage_recorder import LineageRecorder

logger = logging.getLogger(__name__)


@dataclass
class RunHandle:
    """Handle for a single block execution in progress."""

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
    checkpoint_manager:
        Optional checkpoint manager for persisting execution state.
    """

    def __init__(
        self,
        workflow: WorkflowDefinition,
        event_bus: EventBus,
        resource_manager: Any,
        process_registry: Any,
        runner: Any,
        registry: BlockRegistry | None = None,
        checkpoint_manager: Any | None = None,
        lineage_recorder: LineageRecorder | None = None,
    ) -> None:
        self._workflow = workflow
        self._event_bus = event_bus
        self._resource_manager = resource_manager
        self._process_registry = process_registry
        self._runner = runner
        self._registry = registry
        self._checkpoint_manager = checkpoint_manager
        self._lineage_recorder = lineage_recorder

        self._dag = build_dag(workflow)
        self._order = topological_sort(self._dag)

        # Block state tracking: IDLE -> READY -> RUNNING -> DONE/ERROR/CANCELLED/SKIPPED
        self._block_states: dict[str, BlockState] = {n: BlockState.IDLE for n in self._dag.nodes}
        self._block_outputs: dict[str, Any] = {}
        self.skip_reasons: dict[str, str] = {}

        # Active asyncio.Task per block (ADR-018 Addendum 1). Populated by
        # ``_dispatch`` when a block's ``_run_and_finalize`` task is created
        # and popped by that task's ``finally`` clause on exit.
        self._active_tasks: dict[str, asyncio.Task[None]] = {}

        self._completed_event = asyncio.Event()
        self._paused = False
        self._reset_lock = asyncio.Lock()

        self._event_bus.subscribe(BLOCK_DONE, self._on_block_done)
        self._event_bus.subscribe(BLOCK_ERROR, self._on_block_error)
        self._event_bus.subscribe(CANCEL_BLOCK_REQUEST, self._on_cancel_block)
        self._event_bus.subscribe(CANCEL_WORKFLOW_REQUEST, self._on_cancel_workflow)
        self._event_bus.subscribe(PROCESS_EXITED, self._on_process_exited)

    async def execute(self) -> None:
        """Begin executing the workflow from its current state.

        Independent DAG branches run concurrently: ``_dispatch`` creates an
        ``asyncio.Task`` per block (ADR-018 Addendum 1). The method body is
        wrapped in ``try/finally`` so that any exception triggers
        ``_cancel_active_tasks_on_shutdown`` to terminate subprocess
        handles and cancel pre-subprocess tasks, preventing zombie
        processes on engine-level failure.
        """
        await self._event_bus.emit(EngineEvent(event_type=WORKFLOW_STARTED, data={"workflow_id": self._workflow.id}))

        if not self._dag.nodes:
            self._completed_event.set()
            await self._event_bus.emit(
                EngineEvent(event_type=WORKFLOW_COMPLETED, data={"workflow_id": self._workflow.id})
            )
            return

        try:
            # Initial dispatch of root-ready blocks. Each _dispatch call
            # creates a task and returns immediately; successor dispatches
            # are triggered by _on_block_done -> _dispatch_newly_ready.
            for node_id in self._order:
                if self._block_states[node_id] == BlockState.IDLE and self._check_readiness(node_id):
                    self._block_states[node_id] = BlockState.READY
                    await self._dispatch(node_id)
            await self._completed_event.wait()
        finally:
            await self._cancel_active_tasks_on_shutdown()

        await self._event_bus.emit(EngineEvent(event_type=WORKFLOW_COMPLETED, data={"workflow_id": self._workflow.id}))

    async def _dispatch(self, node_id: str) -> None:
        """Synchronous prelude for dispatching a single block.

        Per ADR-018 Addendum 1, this method performs only the work that
        must run on the scheduler coroutine itself — paused/resource
        checks, state transition to RUNNING, BLOCK_RUNNING emission,
        lineage start, input gathering, and block instantiation — and
        then wraps the long-running ``runner.run`` call in an
        ``asyncio.Task`` via ``_run_and_finalize``. The task is stored in
        ``self._active_tasks`` and the method returns immediately so
        that independent branches can run concurrently.

        If ``_paused`` is True or ``ResourceManager.can_dispatch`` returns
        False, the block stays in its current state (READY) and the
        method returns without creating a task — it will be retried on
        the next successor event via ``_dispatch_newly_ready``.
        """
        if self._paused:
            return

        if not self._resource_manager.can_dispatch(ResourceRequest()):
            # Stay READY; retried by _dispatch_newly_ready on the next
            # resource-freeing event (BLOCK_DONE / PROCESS_EXITED).
            return

        # A task already exists for this block — guard against double
        # dispatch that could otherwise replace the live task reference.
        if node_id in self._active_tasks:
            return

        self._block_states[node_id] = BlockState.RUNNING
        await self._event_bus.emit(
            EngineEvent(
                event_type=BLOCK_RUNNING,
                block_id=node_id,
                data={"workflow_id": self._workflow.id},
            )
        )

        if self._lineage_recorder is not None:
            self._lineage_recorder.record_start(node_id)

        inputs = self._gather_inputs(node_id)
        node = self._dag.nodes[node_id]

        try:
            block = self._instantiate_block(node_id)
        except Exception as exc:
            # Block instantiation failed before a task could be created.
            # Transition directly to ERROR and emit BLOCK_ERROR so that
            # skip propagation fires via the normal event path.
            logger.exception("Block %s failed to instantiate", node_id)
            self._block_states[node_id] = BlockState.ERROR
            await self._event_bus.emit(
                EngineEvent(
                    event_type=BLOCK_ERROR,
                    block_id=node_id,
                    data={"workflow_id": self._workflow.id, "error": str(exc)},
                )
            )
            self.save_checkpoint(self._checkpoint_manager)
            return

        task = asyncio.create_task(
            self._run_and_finalize(node_id, block, inputs, node.config),
            name=f"dispatch:{node_id}",
        )
        self._active_tasks[node_id] = task

    async def _run_and_finalize(
        self,
        node_id: str,
        block: Any,
        inputs: dict[str, Any],
        config: dict[str, Any],
    ) -> None:
        """Long-running task body for a single block (ADR-018 Addendum 1).

        Awaits ``runner.run``, transitions state to DONE (or ERROR on
        exception, unless the block was already CANCELLED), emits the
        terminal event, and always removes the block from
        ``self._active_tasks`` in its ``finally`` clause.
        """
        try:
            try:
                result = await self._runner.run(block, inputs, config)
            except asyncio.CancelledError:
                # Task was cancelled externally (e.g. via _on_cancel_block
                # pre-subprocess path). State transition to CANCELLED is
                # handled by the caller; re-raise so asyncio can finalise.
                raise
            except Exception as exc:
                if self._block_states.get(node_id) == BlockState.CANCELLED:
                    logger.info("Block %s exited after cancellation", node_id)
                    self.save_checkpoint(self._checkpoint_manager)
                    return
                logger.exception("Block %s failed with exception", node_id)
                self._block_states[node_id] = BlockState.ERROR
                await self._event_bus.emit(
                    EngineEvent(
                        event_type=BLOCK_ERROR,
                        block_id=node_id,
                        data={"workflow_id": self._workflow.id, "error": str(exc)},
                    )
                )
                self.save_checkpoint(self._checkpoint_manager)
                return

            self._block_outputs[node_id] = result
            self._block_states[node_id] = BlockState.DONE
            await self._event_bus.emit(
                EngineEvent(
                    event_type=BLOCK_DONE,
                    block_id=node_id,
                    data={"workflow_id": self._workflow.id, "outputs": result},
                )
            )
            self.save_checkpoint(self._checkpoint_manager)
        finally:
            # Always pop the task entry so _check_completion can observe
            # "no active tasks" once the final block finalises.
            self._active_tasks.pop(node_id, None)
            self._check_completion()

    def _instantiate_block(self, node_id: str) -> Any:
        """Instantiate the concrete block for a DAG node.

        Uses the BlockRegistry when available. Falls back to the raw
        NodeDef for backward compatibility with tests using mock runners.
        """
        node = self._dag.nodes[node_id]
        if self._registry is not None:
            block = self._registry.instantiate(node.block_type, node.config)
            block.id = node_id
            return block
        node.id = node_id
        return node

    def _gather_inputs(self, node_id: str) -> dict[str, Any]:
        """Collect inputs for *node_id* from upstream block outputs."""
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
                inputs[tgt_port] = upstream_outputs
        return inputs

    async def _dispatch_newly_ready(self) -> None:
        """Dispatch blocks that became ready or were previously throttled.

        Called from ``_on_block_done`` and ``_on_process_exited`` after
        a terminal event. Scans the topological order for:

        * IDLE blocks whose predecessors are all DONE — transition to
          READY and dispatch.
        * READY blocks with no active task — previously refused by
          ``ResourceManager.can_dispatch`` and now eligible for a retry.

        ``_dispatch`` is itself idempotent: if ``can_dispatch`` still
        returns False, the block stays READY and no task is created.
        """
        for node_id in self._order:
            state = self._block_states[node_id]
            if state == BlockState.IDLE and self._check_readiness(node_id):
                self._block_states[node_id] = BlockState.READY
                await self._dispatch(node_id)
            elif state == BlockState.READY and node_id not in self._active_tasks:
                # Previously blocked by can_dispatch / paused; retry now.
                await self._dispatch(node_id)

    async def _on_block_done(self, event: EngineEvent) -> None:
        """Handle a block completion and dispatch newly ready blocks."""
        if event.block_id is None:
            return

        await self._dispatch_newly_ready()

        self._check_completion()
        self.save_checkpoint(self._checkpoint_manager)

    async def _on_block_error(self, event: EngineEvent) -> None:
        """Handle a block error and propagate skips downstream."""
        if event.block_id is None:
            return

        self._block_states[event.block_id] = BlockState.ERROR
        await self._propagate_skip(event.block_id, "error")
        self._check_completion()
        self.save_checkpoint(self._checkpoint_manager)

    async def _on_cancel_block(self, event: EngineEvent) -> None:
        """Handle a block cancellation request.

        Per ADR-018 Addendum 1, cancellation branches on whether a
        ``ProcessHandle`` has been registered for the block yet:

        * **Handle present** (block is executing inside a subprocess):
          call ``handle.terminate()`` and let the worker unwind
          naturally. ``_run_and_finalize`` observes the CANCELLED state
          on its exception path and exits without emitting BLOCK_ERROR.
        * **Handle absent** (block is still in its pre-subprocess setup
          window or has no subprocess at all): call ``task.cancel()``
          on the active task. ``_run_and_finalize`` receives a
          ``CancelledError`` and unwinds via its ``finally`` clause.
        * **No handle, no active task**: the block is pre-dispatch or
          was set externally (e.g. tests that pre-assign RUNNING). In
          that case we simply transition to CANCELLED without
          terminating or cancelling anything.
        """
        if event.block_id is None:
            return

        block_id = event.block_id
        handle = None
        if self._process_registry is not None:
            handle = self._process_registry.get_handle(block_id)

        # Mark CANCELLED before terminating/cancelling so that
        # _run_and_finalize's exception path sees the CANCELLED state
        # and does not re-emit BLOCK_ERROR.
        self._block_states[block_id] = BlockState.CANCELLED

        if handle is not None:
            # Authoritative path per ADR-019 — SIGTERM/SIGKILL the worker.
            try:
                handle.terminate()
            except Exception:
                logger.exception("Failed to terminate subprocess for block %s", block_id)
        else:
            # No subprocess handle yet: cancel the pre-subprocess task
            # so that the setup phase aborts with CancelledError.
            task = self._active_tasks.get(block_id)
            if task is not None and not task.done():
                task.cancel()

        if hasattr(self._runner, "cancel"):
            try:
                await self._runner.cancel(block_id)
            except Exception:
                logger.exception("Failed to cancel block %s via runner", block_id)

        await self._event_bus.emit(
            EngineEvent(
                event_type=BLOCK_CANCELLED,
                block_id=block_id,
                data={"workflow_id": self._workflow.id},
            )
        )
        await self._propagate_skip(block_id, "cancelled")
        self._check_completion()
        self.save_checkpoint(self._checkpoint_manager)

    async def _on_cancel_workflow(self, event: EngineEvent) -> None:
        """Handle a workflow cancellation: cancel all running blocks.

        Applies the same handle-vs-task branch as ``_on_cancel_block``
        (ADR-018 Addendum 1). Any block still IDLE/READY at the time of
        the cancel request is transitioned to SKIPPED with reason
        "workflow cancelled".
        """
        running_blocks = [bid for bid, state in self._block_states.items() if state == BlockState.RUNNING]

        for block_id in running_blocks:
            handle = None
            if self._process_registry is not None:
                handle = self._process_registry.get_handle(block_id)

            # Mark CANCELLED before terminating/cancelling so that
            # _run_and_finalize observes the CANCELLED state.
            self._block_states[block_id] = BlockState.CANCELLED

            if handle is not None:
                try:
                    handle.terminate()
                except Exception:
                    logger.exception(
                        "Failed to terminate subprocess for block %s during workflow cancel",
                        block_id,
                    )
            else:
                task = self._active_tasks.get(block_id)
                if task is not None and not task.done():
                    task.cancel()

            if hasattr(self._runner, "cancel"):
                try:
                    await self._runner.cancel(block_id)
                except Exception:
                    logger.exception("Failed to cancel block %s during workflow cancel", block_id)

            await self._event_bus.emit(
                EngineEvent(
                    event_type=BLOCK_CANCELLED,
                    block_id=block_id,
                    data={"workflow_id": self._workflow.id},
                )
            )

        for block_id, state in list(self._block_states.items()):
            if state in (BlockState.IDLE, BlockState.READY):
                self._block_states[block_id] = BlockState.SKIPPED
                self.skip_reasons[block_id] = "workflow cancelled"
                await self._event_bus.emit(
                    EngineEvent(
                        event_type=BLOCK_SKIPPED,
                        block_id=block_id,
                        data={"workflow_id": self._workflow.id},
                    )
                )

        self._check_completion()
        self.save_checkpoint(self._checkpoint_manager)

    async def _on_process_exited(self, event: EngineEvent) -> None:
        """Handle an unexpected subprocess exit detected by ProcessMonitor.

        If the block is RUNNING and not yet in a terminal state, transition
        to ERROR and emit BLOCK_ERROR so that skip propagation and completion
        checks fire through the normal path.

        PAUSED blocks (AppBlock case) are left alone \u2014 the FileWatcher
        manages output collection and will handle the process exit.
        """
        block_id = event.block_id
        if block_id is None or block_id not in self._block_states:
            return

        current = self._block_states[block_id]

        # Already in a terminal state \u2014 ignore.
        terminal = {BlockState.DONE, BlockState.ERROR, BlockState.CANCELLED, BlockState.SKIPPED}
        if current in terminal:
            return

        # PAUSED: AppBlock subprocess exited. FileWatcher handles it.
        if current == BlockState.PAUSED:
            return

        # RUNNING: subprocess crashed / OOM-killed / externally terminated.
        if current == BlockState.RUNNING:
            exit_info = event.data.get("exit_info")
            error_detail = "Process exited unexpectedly"
            if isinstance(exit_info, dict):
                sig = exit_info.get("signal_number")
                code = exit_info.get("exit_code")
                if sig:
                    error_detail = f"Process killed by signal {sig}"
                elif code is not None:
                    error_detail = f"Process exited with code {code}"
            elif exit_info is not None:
                sig = getattr(exit_info, "signal_number", None)
                code = getattr(exit_info, "exit_code", None)
                if sig:
                    error_detail = f"Process killed by signal {sig}"
                elif code is not None:
                    error_detail = f"Process exited with code {code}"

            self._block_states[block_id] = BlockState.ERROR
            await self._event_bus.emit(
                EngineEvent(
                    event_type=BLOCK_ERROR,
                    block_id=block_id,
                    data={"workflow_id": self._workflow.id, "error": error_detail},
                )
            )
            # Retry any READY blocks that were previously throttled and
            # dispatch successors whose predecessors are now all DONE.
            await self._dispatch_newly_ready()
            self._check_completion()

    async def _propagate_skip(self, failed_id: str, reason: str) -> None:
        """Breadth-first skip propagation downstream from *failed_id*."""
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

            predecessors = self._dag.reverse_adjacency.get(node_id, [])
            all_satisfied = all(self._block_states[p] == BlockState.DONE for p in predecessors)

            if not all_satisfied:
                self._block_states[node_id] = BlockState.SKIPPED
                self.skip_reasons[node_id] = f"upstream {failed_id} {reason}"
                await self._event_bus.emit(
                    EngineEvent(
                        event_type=BLOCK_SKIPPED,
                        block_id=node_id,
                        data={"workflow_id": self._workflow.id},
                    )
                )
                queue.extend(self._dag.adjacency.get(node_id, []))

    def _check_readiness(self, node_id: str) -> bool:
        """Return True if all predecessors of *node_id* are in DONE state."""
        predecessors = self._dag.reverse_adjacency.get(node_id, [])
        return all(self._block_states[p] == BlockState.DONE for p in predecessors)

    def _check_completion(self) -> None:
        """Set the completed event when every block has reached a terminal
        state **and** no dispatched task is still running.

        The ``_active_tasks`` guard (ADR-018 Addendum 1) prevents
        ``execute()`` from returning before the final
        ``_run_and_finalize`` coroutine has finished its cleanup.
        """
        terminal = {BlockState.DONE, BlockState.ERROR, BlockState.CANCELLED, BlockState.SKIPPED}
        if all(s in terminal for s in self._block_states.values()) and not self._active_tasks:
            self._completed_event.set()

    async def _cancel_active_tasks_on_shutdown(self) -> None:
        """Best-effort cleanup of any tasks still running on shutdown.

        Called from ``execute()``'s ``finally`` block (ADR-018
        Addendum 1). Iterates every entry in ``self._active_tasks``:

        1. If a ``ProcessHandle`` is registered, terminate the
           subprocess via the ADR-019 path.
        2. If the task is still not done, cancel it and await its
           completion. Swallows any exception because this runs inside
           a ``finally`` clause and must not mask the original error.
        """
        for block_id, task in list(self._active_tasks.items()):
            handle = None
            if self._process_registry is not None:
                handle = self._process_registry.get_handle(block_id)
            if handle is not None:
                try:
                    handle.terminate()
                except Exception:
                    logger.exception(
                        "Shutdown: failed to terminate process for block %s",
                        block_id,
                    )
            if not task.done():
                task.cancel()
                # Shutdown path: swallow any exception (including the
                # ``CancelledError`` raised by ``task.cancel()``) so the
                # original exception that triggered ``finally`` is not
                # masked.
                with contextlib.suppress(BaseException):
                    await task

    async def pause(self) -> None:
        """Request a graceful pause after current blocks complete."""
        self._paused = True

    async def _drain_active_tasks(self) -> None:
        """Await all dispatched tasks, including any successors they trigger.

        Used by callers that do not otherwise wait on
        ``self._completed_event`` (``resume``, ``reset_block``) but must
        still block until the tasks they just scheduled have finished.
        A snapshot is awaited in each iteration because ``_on_block_done``
        can add new entries to ``_active_tasks`` while we wait.
        """
        while self._active_tasks:
            tasks = list(self._active_tasks.values())
            await asyncio.gather(*tasks, return_exceptions=True)

    async def resume(self) -> None:
        """Resume a previously paused workflow execution."""
        self._paused = False
        for node_id in self._order:
            if self._block_states[node_id] == BlockState.READY:
                await self._dispatch(node_id)
            elif self._block_states[node_id] == BlockState.IDLE and self._check_readiness(node_id):
                self._block_states[node_id] = BlockState.READY
                await self._dispatch(node_id)
        await self._drain_active_tasks()

    async def cancel_workflow(self) -> None:
        """Cancel the current workflow execution."""
        await self._on_cancel_workflow(
            EngineEvent(
                event_type=CANCEL_WORKFLOW_REQUEST,
                data={"workflow_id": self._workflow.id},
            )
        )

    async def cancel_block(self, block_id: str) -> None:
        """Cancel a single block inside the current workflow."""
        await self._on_cancel_block(
            EngineEvent(
                event_type=CANCEL_BLOCK_REQUEST,
                block_id=block_id,
                data={"workflow_id": self._workflow.id},
            )
        )

    def block_states(self) -> dict[str, BlockState]:
        """Return a snapshot of current block execution states."""
        return dict(self._block_states)

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
            5. Re-evaluate readiness and batch-dispatch ready blocks.
        """
        async with self._reset_lock:
            if block_id not in self._block_states:
                raise ValueError(f"Unknown block: {block_id}")

            # Step 2: Reset target block.
            self._block_states[block_id] = BlockState.IDLE
            self._block_outputs.pop(block_id, None)
            self.skip_reasons.pop(block_id, None)

            # Step 3: Walk upstream -- recursively reset non-DONE predecessors.
            self._reset_upstream(block_id, visited=set())

            # Step 4: Walk downstream -- reset SKIPPED blocks.
            self._reset_downstream_skipped(block_id)

            # Step 5: Re-evaluate readiness, collect ready IDs, then dispatch.
            ready_ids: list[str] = []
            for node_id in self._order:
                if self._block_states[node_id] == BlockState.IDLE and self._check_readiness(node_id):
                    self._block_states[node_id] = BlockState.READY
                    ready_ids.append(node_id)
            for node_id in ready_ids:
                await self._dispatch(node_id)

        # Drain outside the reset lock: _run_and_finalize → _on_block_done
        # acquires no locks but still touches scheduler state, and the
        # caller expects reset_block to return only after the dispatched
        # tasks have finished.
        await self._drain_active_tasks()

    def _reset_upstream(self, block_id: str, visited: set[str]) -> None:
        """Recursively reset non-DONE upstream blocks to IDLE."""
        if block_id in visited:
            return
        visited.add(block_id)
        predecessors = self._dag.reverse_adjacency.get(block_id, [])
        for pred in predecessors:
            if self._block_states[pred] != BlockState.DONE:
                self._block_states[pred] = BlockState.IDLE
                self._block_outputs.pop(pred, None)
                self.skip_reasons.pop(pred, None)
                self._reset_upstream(pred, visited)

    def _reset_downstream_skipped(self, block_id: str) -> None:
        """Breadth-first reset of downstream SKIPPED blocks."""
        queue = list(self._dag.adjacency.get(block_id, []))
        visited: set[str] = set()
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            if self._block_states[node_id] == BlockState.SKIPPED:
                self._block_states[node_id] = BlockState.IDLE
                self._block_outputs.pop(node_id, None)
                self.skip_reasons.pop(node_id, None)
                queue.extend(self._dag.adjacency.get(node_id, []))

    def save_checkpoint(self, checkpoint_manager: Any = None) -> None:
        """Persist the current execution state to durable storage."""
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

    def _ancestors_of(self, block_id: str) -> set[str]:
        """Return all upstream nodes for *block_id*."""
        visited: set[str] = set()
        queue = list(self._dag.reverse_adjacency.get(block_id, []))
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self._dag.reverse_adjacency.get(current, []))
        return visited

    async def execute_from(self, block_id: str) -> None:
        """Re-run the workflow from *block_id* using checkpointed upstream outputs."""
        if block_id not in self._block_states:
            raise ValueError(f"Unknown block: {block_id}")
        if self._checkpoint_manager is None:
            raise ValueError("Selective execution requires a checkpoint manager.")

        checkpoint = self._checkpoint_manager.load(self._workflow.id)
        if checkpoint is None:
            raise FileNotFoundError("No checkpoint is available for this workflow.")

        ancestors = self._ancestors_of(block_id)
        missing = [ancestor for ancestor in ancestors if ancestor not in checkpoint.intermediate_refs]
        if missing:
            raise ValueError("Cannot execute from block without cached upstream outputs: " + ", ".join(sorted(missing)))

        descendants = set(get_downstream_blocks(self._dag, block_id)) | {block_id}
        self._completed_event = asyncio.Event()

        # #404 / #408 / ADR-027 Addendum 1: Wire-format dicts from the
        # checkpoint are assigned directly to _block_outputs WITHOUT calling
        # deserialize_intermediate_refs().  The wire-format dict carries a
        # metadata.type_chain field that _reconstruct_one() inside the worker
        # subprocess uses to instantiate the correct typed DataObject.
        # Calling deserialize_intermediate_refs() here would produce ViewProxy
        # objects that are not JSON-serialisable and would break
        # spawn_block_process().
        for node_id in self._order:
            if node_id in ancestors:
                self._block_states[node_id] = BlockState.DONE
                self._block_outputs[node_id] = checkpoint.intermediate_refs[node_id]
                self.skip_reasons.pop(node_id, None)
            elif node_id in descendants:
                self._block_states[node_id] = BlockState.IDLE
                self._block_outputs.pop(node_id, None)
                self.skip_reasons.pop(node_id, None)
            else:
                self._block_states[node_id] = BlockState(checkpoint.block_states.get(node_id, "idle"))
                if node_id in checkpoint.intermediate_refs:
                    self._block_outputs[node_id] = checkpoint.intermediate_refs[node_id]

        await self._event_bus.emit(
            EngineEvent(
                event_type=WORKFLOW_STARTED,
                data={"workflow_id": self._workflow.id, "mode": "execute_from", "block_id": block_id},
            )
        )

        try:
            for node_id in self._order:
                if self._block_states[node_id] == BlockState.IDLE and self._check_readiness(node_id):
                    self._block_states[node_id] = BlockState.READY
                    await self._dispatch(node_id)
            await self._completed_event.wait()
        finally:
            await self._cancel_active_tasks_on_shutdown()

        await self._event_bus.emit(
            EngineEvent(
                event_type=WORKFLOW_COMPLETED,
                data={"workflow_id": self._workflow.id, "mode": "execute_from", "block_id": block_id},
            )
        )
