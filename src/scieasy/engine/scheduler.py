"""DAGScheduler -- walk DAG in topo-order, dispatch blocks, propagate state."""

from __future__ import annotations

from typing import Any

from scieasy.blocks.base.block import Block
from scieasy.blocks.base.result import BlockResult
from scieasy.blocks.base.state import BlockState
from scieasy.blocks.registry import BlockRegistry
from scieasy.engine.checkpoint import WorkflowCheckpoint, save_checkpoint
from scieasy.engine.dag import DAGNode, build_dag, topological_sort
from scieasy.engine.events import EngineEvent, EventBus
from scieasy.engine.runners.local import LocalRunner
from scieasy.workflow.definition import WorkflowDefinition


class DAGScheduler:
    """Execute a workflow by walking its DAG in topological order.

    The scheduler owns the lifecycle of a single workflow execution: it
    resolves the execution order, dispatches each block to a runner,
    manages pause/resume semantics, and persists checkpoints.
    """

    def __init__(
        self,
        workflow: WorkflowDefinition,
        registry: BlockRegistry | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._workflow = workflow
        self._dag: dict[str, DAGNode] = build_dag(workflow)
        self._order: list[str] = topological_sort(self._dag)
        self._registry = registry
        self._runner = LocalRunner()
        self._event_bus = event_bus or EventBus()

        # Execution state per node.
        self._block_states: dict[str, BlockState] = {
            nid: BlockState.IDLE for nid in self._dag
        }
        self._block_instances: dict[str, Block] = {}
        self._results: dict[str, BlockResult] = {}
        self._outputs: dict[str, dict[str, Any]] = {}
        self._paused = False
        self._completed = False

    @property
    def block_states(self) -> dict[str, BlockState]:
        """Return a copy of current block states."""
        return dict(self._block_states)

    @property
    def results(self) -> dict[str, BlockResult]:
        """Return a copy of execution results."""
        return dict(self._results)

    @property
    def outputs(self) -> dict[str, dict[str, Any]]:
        """Return all intermediate/final outputs keyed by node ID."""
        return dict(self._outputs)

    async def execute(self) -> dict[str, dict[str, Any]]:
        """Begin or continue executing the workflow from its current state.

        Returns
        -------
        dict[str, dict[str, Any]]
            Mapping of node ID to output dict for all completed nodes.
        """
        self._paused = False
        self._completed = False

        self._event_bus.emit(EngineEvent(
            event_type="workflow_started",
            data={"workflow_id": self._workflow.id},
        ))

        for node_id in self._order:
            if self._paused:
                break

            # Skip already-completed nodes (e.g. after resume).
            if self._block_states[node_id] == BlockState.DONE:
                continue

            # Check all dependencies are DONE.
            dag_node = self._dag[node_id]
            deps_ready = all(
                self._block_states[dep] == BlockState.DONE
                for dep in dag_node.dependencies
            )
            if not deps_ready:
                self._block_states[node_id] = BlockState.ERROR
                self._event_bus.emit(EngineEvent(
                    event_type="block_state_changed",
                    block_id=node_id,
                    data={"state": BlockState.ERROR.value, "reason": "dependencies not met"},
                ))
                raise RuntimeError(
                    f"Node '{node_id}' has unmet dependencies — this should not happen "
                    "in a valid topological ordering."
                )

            # Gather inputs from upstream outputs.
            inputs = self._gather_inputs(node_id)

            # Instantiate block.
            block = self._instantiate_block(dag_node)
            self._block_instances[node_id] = block

            self._event_bus.emit(EngineEvent(
                event_type="block_state_changed",
                block_id=node_id,
                data={"state": "running"},
            ))

            # Dispatch to runner.
            result = await self._runner.run(block, inputs, dag_node.config)
            self._results[node_id] = result

            if result.error is not None:
                self._block_states[node_id] = BlockState.ERROR
                self._event_bus.emit(EngineEvent(
                    event_type="block_state_changed",
                    block_id=node_id,
                    data={"state": "error", "error": str(result.error)},
                ))
                self._event_bus.emit(EngineEvent(
                    event_type="workflow_error",
                    block_id=node_id,
                    data={"error": str(result.error)},
                ))
                raise RuntimeError(
                    f"Block '{node_id}' ({dag_node.block_type}) failed: {result.error}"
                ) from result.error

            self._block_states[node_id] = BlockState.DONE
            self._outputs[node_id] = result.outputs
            self._event_bus.emit(EngineEvent(
                event_type="block_state_changed",
                block_id=node_id,
                data={"state": "done", "duration_ms": result.duration_ms},
            ))

        if not self._paused:
            self._completed = True
            self._event_bus.emit(EngineEvent(
                event_type="workflow_complete",
                data={"workflow_id": self._workflow.id},
            ))

        return dict(self._outputs)

    async def pause(self) -> WorkflowCheckpoint:
        """Request a graceful pause after the current block completes.

        Returns a checkpoint that can be used to resume later.
        """
        self._paused = True
        checkpoint = self._make_checkpoint()
        self._event_bus.emit(EngineEvent(
            event_type="workflow_paused",
            data={"workflow_id": self._workflow.id},
        ))
        return checkpoint

    async def resume(self, checkpoint: WorkflowCheckpoint | None = None) -> dict[str, dict[str, Any]]:
        """Resume a previously paused workflow execution.

        Parameters
        ----------
        checkpoint:
            If provided, restore state from this checkpoint before resuming.
        """
        if checkpoint is not None:
            self._restore_checkpoint(checkpoint)
        return await self.execute()

    def set_state(self, block_id: str, state: BlockState) -> None:
        """Manually override the execution state of a single block."""
        if block_id not in self._block_states:
            raise KeyError(f"Unknown block ID '{block_id}'")
        self._block_states[block_id] = state

    def save_checkpoint_to(self, path: str) -> None:
        """Persist the current execution state to a file."""
        checkpoint = self._make_checkpoint()
        save_checkpoint(checkpoint, path)

    def _gather_inputs(self, node_id: str) -> dict[str, Any]:
        """Collect inputs for a node from upstream outputs via edge mapping."""
        dag_node = self._dag[node_id]
        inputs: dict[str, Any] = {}
        for target_port, (src_node_id, src_port) in dag_node.input_edges.items():
            src_outputs = self._outputs.get(src_node_id, {})
            if src_port in src_outputs:
                inputs[target_port] = src_outputs[src_port]
        return inputs

    def _instantiate_block(self, dag_node: DAGNode) -> Block:
        """Create a block instance from a DAG node."""
        if self._registry is not None:
            return self._registry.instantiate(dag_node.block_type, config=dag_node.config)
        raise RuntimeError(
            f"No BlockRegistry provided and cannot instantiate '{dag_node.block_type}'. "
            "Provide a registry to the DAGScheduler constructor."
        )

    def _make_checkpoint(self) -> WorkflowCheckpoint:
        """Build a checkpoint from current execution state."""
        from datetime import datetime

        # Find the next pending block.
        pending = None
        for nid in self._order:
            if self._block_states[nid] not in (BlockState.DONE, BlockState.ERROR):
                pending = nid
                break

        return WorkflowCheckpoint(
            workflow_id=self._workflow.id,
            timestamp=datetime.now(),
            block_states={nid: state.value for nid, state in self._block_states.items()},
            intermediate_refs={nid: out for nid, out in self._outputs.items()},
            pending_block=pending,
        )

    def _restore_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Restore execution state from a checkpoint."""
        for nid, state_str in checkpoint.block_states.items():
            if nid in self._block_states:
                self._block_states[nid] = BlockState(state_str)
        for nid, outputs in checkpoint.intermediate_refs.items():
            if isinstance(outputs, dict):
                self._outputs[nid] = outputs
