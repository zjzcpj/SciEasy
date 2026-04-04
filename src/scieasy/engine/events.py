"""Engine event bus — publish/subscribe backbone for runtime coordination.

ADR-018: EventBus becomes the runtime backbone. All state changes, cancellation,
process lifecycle, and checkpoint events flow through this bus.
ADR-017: PROCESS_SPAWNED and PROCESS_EXITED events added for subprocess tracking.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# -- Event type constants (ADR-017, ADR-018) --------------------------------

BLOCK_READY = "block_ready"
BLOCK_RUNNING = "block_running"
BLOCK_PAUSED = "block_paused"
BLOCK_DONE = "block_done"
BLOCK_ERROR = "block_error"
BLOCK_CANCELLED = "block_cancelled"            # ADR-018
BLOCK_SKIPPED = "block_skipped"                # ADR-018
CANCEL_BLOCK_REQUEST = "cancel_block_request"  # ADR-018
CANCEL_WORKFLOW_REQUEST = "cancel_workflow_request"  # ADR-018
PROCESS_SPAWNED = "process_spawned"            # ADR-017/019
PROCESS_EXITED = "process_exited"              # ADR-017/019
WORKFLOW_STARTED = "workflow_started"           # ADR-018
WORKFLOW_COMPLETED = "workflow_completed"       # ADR-018
CHECKPOINT_SAVED = "checkpoint_saved"          # ADR-018


@dataclass
class EngineEvent:
    """A single event emitted by the engine during workflow execution."""

    event_type: str
    block_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# -- Subscription matrix (ADR-018) ------------------------------------------
#
# Component          | Subscribes to
# -------------------|------------------------------------------------------
# DAGScheduler       | BLOCK_READY, BLOCK_DONE, BLOCK_ERROR, BLOCK_CANCELLED,
#                    | BLOCK_SKIPPED, CANCEL_BLOCK_REQUEST, CANCEL_WORKFLOW_REQUEST
# ResourceManager    | BLOCK_DONE, BLOCK_ERROR, BLOCK_CANCELLED,
#                    | PROCESS_SPAWNED, PROCESS_EXITED
# ProcessRegistry    | PROCESS_SPAWNED, PROCESS_EXITED
# WebSocket handler  | all BLOCK_* events, WORKFLOW_COMPLETED
# LineageRecorder    | BLOCK_DONE, BLOCK_ERROR, BLOCK_CANCELLED, BLOCK_SKIPPED
# CheckpointManager  | all terminal state events + CHECKPOINT_SAVED


class EventBus:
    """Publish/subscribe dispatcher for EngineEvent instances.

    TODO(ADR-018): Implement concrete EventBus.

    Internal storage:
        _subscribers: dict[str, list[Callable[[EngineEvent], None]]]

    Methods:
        async emit(event): broadcast event to all subscribers of event.event_type.
            Calls each callback. If callback is a coroutine, await it.
        subscribe(event_type, callback): register callback for event_type.
        unsubscribe(event_type, callback): deregister callback for event_type.
    """

    def __init__(self) -> None:
        # TODO(ADR-018): Initialize _subscribers dict.
        raise NotImplementedError

    async def emit(self, event: EngineEvent) -> None:
        """Broadcast *event* to all subscribers of its event_type."""
        # TODO(ADR-018): Iterate _subscribers[event.event_type], call each.
        raise NotImplementedError

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[EngineEvent], None],
    ) -> None:
        """Register *callback* to receive events of the given type."""
        # TODO(ADR-018): Append callback to _subscribers[event_type].
        raise NotImplementedError

    def unsubscribe(
        self,
        event_type: str,
        callback: Callable[[EngineEvent], None],
    ) -> None:
        """Remove a previously registered *callback* for *event_type*."""
        # TODO(ADR-018): Remove callback from _subscribers[event_type].
        raise NotImplementedError
