"""WebSocket handler — bidirectional real-time block state and cancellation.

ADR-018: WebSocket becomes bidirectional. Server pushes block state changes;
client sends cancel requests and interactive completions.
"""

from __future__ import annotations

from fastapi import WebSocket

# TODO(ADR-018): Implement bidirectional WebSocket handler.
#
# Function signature:
#   async def websocket_handler(websocket: WebSocket, event_bus: EventBus) -> None
#
# Protocol:
#   1. await websocket.accept()
#   2. Start two concurrent tasks:
#
#   INBOUND LOOP (client → server):
#     async for message in websocket:
#       data = json.loads(message)
#       if data["type"] == "cancel_block":
#           event_bus.emit(EngineEvent(event_type=CANCEL_BLOCK_REQUEST,
#                                      block_id=data["block_id"],
#                                      data={"workflow_id": data["workflow_id"]}))
#       elif data["type"] == "cancel_workflow":
#           event_bus.emit(EngineEvent(event_type=CANCEL_WORKFLOW_REQUEST,
#                                      data={"workflow_id": data["workflow_id"]}))
#       elif data["type"] == "interactive_complete":
#           # Forward to appropriate event
#
#   OUTBOUND LOOP (server → client):
#     Subscribe to: BLOCK_READY, BLOCK_RUNNING, BLOCK_PAUSED, BLOCK_DONE,
#       BLOCK_ERROR, BLOCK_CANCELLED, BLOCK_SKIPPED, WORKFLOW_COMPLETED
#     On each event:
#       await websocket.send_json(serialise_event(event))
#
#   CANCEL PROPAGATION MESSAGE:
#     When BLOCK_CANCELLED is followed by BLOCK_SKIPPED events, aggregate
#     into a single cancel_propagation message listing all skipped blocks
#     and their skip reasons.
#
# Helper:
#   def serialise_event(event: EngineEvent) -> dict
#     Convert EngineEvent to WebSocket JSON protocol format.


async def websocket_handler(websocket: WebSocket) -> None:
    """Handle a WebSocket connection for real-time workflow updates.

    TODO(ADR-018): Implement bidirectional protocol as described above.
    Add event_bus parameter. Start inbound + outbound concurrent loops.
    """
    raise NotImplementedError
