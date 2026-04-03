"""DAGScheduler -- walk DAG in topo-order, dispatch blocks, propagate state."""

from __future__ import annotations

from typing import Any


class DAGScheduler:
    """Execute a workflow by walking its DAG in topological order.

    The scheduler owns the lifecycle of a single workflow execution: it
    resolves the execution order, dispatches each block to a runner,
    manages pause/resume semantics, and persists checkpoints.
    """

    def __init__(self, workflow: Any) -> None:
        """Initialise the scheduler with a workflow definition.

        Parameters
        ----------
        workflow:
            A ``WorkflowDefinition`` (or equivalent) describing the graph
            to execute.
        """
        raise NotImplementedError

    async def execute(self) -> None:
        """Begin or continue executing the workflow from its current state."""
        raise NotImplementedError

    async def pause(self) -> None:
        """Request a graceful pause after the current block completes."""
        raise NotImplementedError

    async def resume(self) -> None:
        """Resume a previously paused workflow execution."""
        raise NotImplementedError

    def set_state(self, block_id: str, state: Any) -> None:
        """Manually override the execution state of a single block.

        Parameters
        ----------
        block_id:
            Identifier of the block whose state should change.
        state:
            New state value to assign.
        """
        raise NotImplementedError

    def save_checkpoint(self) -> None:
        """Persist the current execution state to durable storage."""
        raise NotImplementedError
