"""DAGScheduler — event-driven workflow execution with cancellation and skip propagation.

ADR-018: Replaces the synchronous for-loop scheduler with an event-driven
architecture. Reacts to EventBus events, propagates SKIPPED to downstream
blocks with unsatisfiable inputs, and supports per-block and whole-workflow
cancellation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# TODO(ADR-018): Import from engine.events, engine.runners, engine.resources.
# These are engine-internal imports (allowed by import-linter).


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

    TODO(ADR-018): Event-driven scheduler implementation.

    Constructor:
        __init__(self, workflow, event_bus, resource_manager, process_registry, runner)
        - Wires up EventBus subscriptions for:
          BLOCK_DONE, BLOCK_ERROR, BLOCK_CANCELLED, BLOCK_SKIPPED,
          CANCEL_BLOCK_REQUEST, CANCEL_WORKFLOW_REQUEST

    Core methods:
        async execute() — emit WORKFLOW_STARTED, find initial ready blocks, dispatch,
                         wait for all blocks to reach terminal state, emit WORKFLOW_COMPLETED.
        async pause() — request graceful pause after current blocks complete.
        async resume() — resume from paused state.

    Event handlers:
        _on_block_done(event) — release resources, find newly ready blocks, dispatch.
        _on_block_error(event) — call _propagate_skip() for downstream.
        _on_cancel_block(event) — terminate subprocess via ProcessHandle, emit
                                  BLOCK_CANCELLED, call _propagate_skip().
        _on_cancel_workflow(event) — terminate all active processes, emit
                                     BLOCK_CANCELLED for each.

    Skip propagation:
        _propagate_skip(failed_block_id) — walk DAG downstream, mark blocks SKIPPED
            if ALL required inputs are unsatisfiable. Optional inputs don't trigger skip.
            Propagation is identical for ERROR and CANCELLED source states.

    Readiness:
        _check_readiness(block_id) -> bool — all required inputs have data.

    State tracking:
        skip_reasons: dict[str, str] — maps block_id to human-readable skip reason.
    """

    def __init__(self, workflow: Any, **kwargs: Any) -> None:
        # TODO(ADR-018): Accept event_bus, resource_manager, process_registry, runner.
        # Wire up EventBus subscriptions.
        raise NotImplementedError

    async def execute(self) -> None:
        """Begin executing the workflow from its current state."""
        # TODO(ADR-018): Emit WORKFLOW_STARTED, find initial ready blocks, dispatch.
        raise NotImplementedError

    async def pause(self) -> None:
        """Request a graceful pause after the current blocks complete."""
        raise NotImplementedError

    async def resume(self) -> None:
        """Resume a previously paused workflow execution."""
        raise NotImplementedError

    def set_state(self, block_id: str, state: Any) -> None:
        """Manually override the execution state of a single block."""
        raise NotImplementedError

    def save_checkpoint(self) -> None:
        """Persist the current execution state to durable storage."""
        raise NotImplementedError
