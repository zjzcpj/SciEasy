"""DAGScheduler -- event-driven workflow execution with cancellation and skip propagation."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from scieasy.engine.dag import build_dag, get_downstream_blocks, topological_sort
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

logger = logging.getLogger(__name__)


@dataclass
class RunHandle:
    """Handle for a single block execution in progress."""

    run_id: str = ""
    process_handle: Any = None
    result: Any = None


class DAGScheduler:
    """Execute a workflow by reacting to EventBus events."""

    def __init__(
        self,
        workflow: WorkflowDefinition,
        event_bus: EventBus,
        resource_manager: Any,
        process_registry: Any,
        runner: Any,
        block_registry: Any | None = None,
        checkpoint_manager: Any | None = None,
    ) -> None:
        self._workflow = workflow
        self._event_bus = event_bus
        self._resource_manager = resource_manager
        self._process_registry = process_registry
        self._runner = runner
        self._block_registry = block_registry
        self._checkpoint_manager = checkpoint_manager

        self._dag = build_dag(workflow)
        self._order = topological_sort(self._dag)

        self._block_states: dict[str, str] = {node_id: "idle" for node_id in self._dag.nodes}
        self._block_outputs: dict[str, Any] = {}
        self.skip_reasons: dict[str, str] = {}

        self._completed_event = asyncio.Event()
        self._paused = False

        self._event_bus.subscribe(BLOCK_DONE, self._on_block_done)
        self._event_bus.subscribe(BLOCK_ERROR, self._on_block_error)
        self._event_bus.subscribe(CANCEL_BLOCK_REQUEST, self._on_cancel_block)
        self._event_bus.subscribe(CANCEL_WORKFLOW_REQUEST, self._on_cancel_workflow)

    async def execute(self) -> None:
        """Begin executing the workflow from its current state."""
        await self._event_bus.emit(EngineEvent(event_type=WORKFLOW_STARTED, data={"workflow_id": self._workflow.id}))

        if not self._dag.nodes:
            self._completed_event.set()
            await self._event_bus.emit(
                EngineEvent(event_type=WORKFLOW_COMPLETED, data={"workflow_id": self._workflow.id})
            )
            return

        for node_id in self._order:
            if self._block_states[node_id] == "idle" and self._check_readiness(node_id):
                self._block_states[node_id] = "ready"
                await self._dispatch(node_id)

        await self._completed_event.wait()
        await self._event_bus.emit(EngineEvent(event_type=WORKFLOW_COMPLETED, data={"workflow_id": self._workflow.id}))

    async def _dispatch(self, node_id: str) -> None:
        """Dispatch a single block for execution."""
        if self._paused:
            return

        if not self._resource_manager.can_dispatch(ResourceRequest()):
            return

        self._block_states[node_id] = "running"
        await self._event_bus.emit(
            EngineEvent(
                event_type=BLOCK_RUNNING,
                block_id=node_id,
                data={"workflow_id": self._workflow.id},
            )
        )

        inputs = self._gather_inputs(node_id)
        node = self._dag.nodes[node_id]
        block = self._instantiate_block(node_id)

        try:
            result = await self._runner.run(block, inputs, node.config)
            self._block_outputs[node_id] = result
            self._block_states[node_id] = "done"
            await self._event_bus.emit(
                EngineEvent(
                    event_type=BLOCK_DONE,
                    block_id=node_id,
                    data={"workflow_id": self._workflow.id, "outputs": result},
                )
            )
            self.save_checkpoint(self._checkpoint_manager)
        except Exception as exc:
            if self._block_states.get(node_id) == "cancelled":
                logger.info("Block %s exited after cancellation", node_id)
                self._check_completion()
                self.save_checkpoint(self._checkpoint_manager)
                return
            logger.exception("Block %s failed with exception", node_id)
            self._block_states[node_id] = "error"
            await self._event_bus.emit(
                EngineEvent(
                    event_type=BLOCK_ERROR,
                    block_id=node_id,
                    data={"workflow_id": self._workflow.id, "error": str(exc)},
                )
            )
            self.save_checkpoint(self._checkpoint_manager)

    def _instantiate_block(self, node_id: str) -> Any:
        """Instantiate the concrete block for a DAG node."""
        node = self._dag.nodes[node_id]
        if self._block_registry is not None:
            try:
                block = self._block_registry.instantiate(node.block_type, config=node.config)
                block.id = node_id
                return block
            except Exception:
                logger.exception("Falling back to raw DAG node for block %s", node_id)
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

    async def _on_block_done(self, event: EngineEvent) -> None:
        """Handle a block completion and dispatch newly ready blocks."""
        if event.block_id is None:
            return

        for node_id in self._order:
            if self._block_states[node_id] != "idle":
                continue
            if self._check_readiness(node_id):
                self._block_states[node_id] = "ready"
                await self._dispatch(node_id)

        self._check_completion()
        self.save_checkpoint(self._checkpoint_manager)

    async def _on_block_error(self, event: EngineEvent) -> None:
        """Handle a block error and propagate skips downstream."""
        if event.block_id is None:
            return

        self._block_states[event.block_id] = "error"
        await self._propagate_skip(event.block_id, "error")
        self._check_completion()
        self.save_checkpoint(self._checkpoint_manager)

    async def _on_cancel_block(self, event: EngineEvent) -> None:
        """Handle a block cancellation request."""
        if event.block_id is None:
            return

        block_id = event.block_id
        if self._process_registry is not None:
            handle = self._process_registry.get_handle(block_id)
            if handle is not None:
                handle.terminate()

        if hasattr(self._runner, "cancel"):
            try:
                await self._runner.cancel(block_id)
            except Exception:
                logger.exception("Failed to cancel block %s via runner", block_id)

        self._block_states[block_id] = "cancelled"
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
        """Handle a workflow cancellation request."""
        running_blocks = [block_id for block_id, state in self._block_states.items() if state == "running"]

        for block_id in running_blocks:
            if self._process_registry is not None:
                handle = self._process_registry.get_handle(block_id)
                if handle is not None:
                    handle.terminate()

            if hasattr(self._runner, "cancel"):
                try:
                    await self._runner.cancel(block_id)
                except Exception:
                    logger.exception("Failed to cancel block %s during workflow cancel", block_id)

            self._block_states[block_id] = "cancelled"
            await self._event_bus.emit(
                EngineEvent(
                    event_type=BLOCK_CANCELLED,
                    block_id=block_id,
                    data={"workflow_id": self._workflow.id},
                )
            )

        for block_id, state in list(self._block_states.items()):
            if state in ("idle", "ready"):
                self._block_states[block_id] = "skipped"
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

    async def _propagate_skip(self, failed_id: str, reason: str) -> None:
        """Breadth-first skip propagation downstream from *failed_id*."""
        queue = list(self._dag.adjacency.get(failed_id, []))

        while queue:
            node_id = queue.pop(0)
            if self._block_states[node_id] in {"done", "error", "cancelled", "skipped"}:
                continue

            predecessors = self._dag.reverse_adjacency.get(node_id, [])
            all_satisfied = all(self._block_states[pred] == "done" for pred in predecessors)

            if not all_satisfied:
                self._block_states[node_id] = "skipped"
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
        """Return True if all predecessors of *node_id* are done."""
        predecessors = self._dag.reverse_adjacency.get(node_id, [])
        return all(self._block_states[pred] == "done" for pred in predecessors)

    def _check_completion(self) -> None:
        """Set the completed event if all blocks are terminal."""
        terminal = {"done", "error", "cancelled", "skipped"}
        if all(state in terminal for state in self._block_states.values()):
            self._completed_event.set()

    async def pause(self) -> None:
        """Request a graceful pause after current blocks complete."""
        self._paused = True

    async def resume(self) -> None:
        """Resume a previously paused workflow execution."""
        self._paused = False
        for node_id in self._order:
            if self._block_states[node_id] == "ready":
                await self._dispatch(node_id)
            elif self._block_states[node_id] == "idle" and self._check_readiness(node_id):
                self._block_states[node_id] = "ready"
                await self._dispatch(node_id)

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

    def block_states(self) -> dict[str, str]:
        """Return a snapshot of current block execution states."""
        return dict(self._block_states)

    def set_state(self, block_id: str, state: str) -> None:
        """Manually override the execution state of a single block."""
        self._block_states[block_id] = state

    async def reset_block(self, block_id: str) -> None:
        """Reset a block and its dependency chain for selective re-run."""
        if block_id not in self._block_states:
            raise ValueError(f"Unknown block: {block_id}")

        self._block_states[block_id] = "idle"
        self._block_outputs.pop(block_id, None)
        self.skip_reasons.pop(block_id, None)

        self._reset_upstream(block_id, visited=set())
        self._reset_downstream_skipped(block_id)

        for node_id in self._order:
            if self._block_states[node_id] == "idle" and self._check_readiness(node_id):
                self._block_states[node_id] = "ready"
                await self._dispatch(node_id)

    def _reset_upstream(self, block_id: str, visited: set[str]) -> None:
        """Recursively reset non-DONE upstream blocks to IDLE."""
        if block_id in visited:
            return
        visited.add(block_id)
        for predecessor in self._dag.reverse_adjacency.get(block_id, []):
            if self._block_states[predecessor] != "done":
                self._block_states[predecessor] = "idle"
                self._block_outputs.pop(predecessor, None)
                self.skip_reasons.pop(predecessor, None)
                self._reset_upstream(predecessor, visited)

    def _reset_downstream_skipped(self, block_id: str) -> None:
        """Breadth-first reset of downstream SKIPPED blocks."""
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
        """Persist the current execution state to durable storage."""
        if checkpoint_manager is None:
            return

        from datetime import datetime

        from scieasy.engine.checkpoint import WorkflowCheckpoint

        checkpoint = WorkflowCheckpoint(
            workflow_id=self._workflow.id if hasattr(self._workflow, "id") else "unknown",
            timestamp=datetime.now(),
            block_states=dict(self._block_states),
            intermediate_refs=dict(self._block_outputs),
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

        for node_id in self._order:
            if node_id in ancestors:
                self._block_states[node_id] = "done"
                self._block_outputs[node_id] = checkpoint.intermediate_refs[node_id]
                self.skip_reasons.pop(node_id, None)
            elif node_id in descendants:
                self._block_states[node_id] = "idle"
                self._block_outputs.pop(node_id, None)
                self.skip_reasons.pop(node_id, None)
            else:
                self._block_states[node_id] = checkpoint.block_states.get(node_id, "idle")
                if node_id in checkpoint.intermediate_refs:
                    self._block_outputs[node_id] = checkpoint.intermediate_refs[node_id]

        await self._event_bus.emit(
            EngineEvent(
                event_type=WORKFLOW_STARTED,
                data={"workflow_id": self._workflow.id, "mode": "execute_from", "block_id": block_id},
            )
        )

        for node_id in self._order:
            if self._block_states[node_id] == "idle" and self._check_readiness(node_id):
                self._block_states[node_id] = "ready"
                await self._dispatch(node_id)

        await self._completed_event.wait()
        await self._event_bus.emit(
            EngineEvent(
                event_type=WORKFLOW_COMPLETED,
                data={"workflow_id": self._workflow.id, "mode": "execute_from", "block_id": block_id},
            )
        )
