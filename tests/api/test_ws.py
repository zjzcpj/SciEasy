"""Tests for WebSocket realtime updates."""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from scieasy.api.runtime import ApiRuntime
from scieasy.engine.events import BLOCK_DONE, CANCEL_BLOCK_REQUEST, CANCEL_WORKFLOW_REQUEST, EngineEvent
from tests.api.helpers import wait_for_condition


def test_websocket_receives_serialised_engine_events(client: TestClient, runtime: ApiRuntime) -> None:
    """Outbound workflow events should be pushed to connected clients."""
    with client.websocket_connect("/ws") as websocket:
        asyncio.run(
            runtime.event_bus.emit(
                EngineEvent(
                    event_type=BLOCK_DONE,
                    block_id="node-1",
                    data={"workflow_id": "wf-1", "outputs": {"port": "value"}},
                )
            )
        )
        message = websocket.receive_json()

    assert message["type"] == BLOCK_DONE
    assert message["block_id"] == "node-1"
    assert message["workflow_id"] == "wf-1"
    assert message["data"]["outputs"] == {"port": "value"}


def test_websocket_inbound_messages_emit_cancel_events(client: TestClient, runtime: ApiRuntime) -> None:
    """Inbound cancel messages should fan out onto the EventBus."""
    seen: list[tuple[str, str | None, str | None]] = []

    def capture(event: EngineEvent) -> None:
        seen.append((event.event_type, event.block_id, event.data.get("workflow_id")))

    runtime.event_bus.subscribe(CANCEL_BLOCK_REQUEST, capture)
    runtime.event_bus.subscribe(CANCEL_WORKFLOW_REQUEST, capture)
    try:
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"type": "cancel_block", "workflow_id": "wf-2", "block_id": "node-3"})
            websocket.send_json({"type": "cancel_workflow", "workflow_id": "wf-2"})

        wait_for_condition(lambda: len(seen) == 2, timeout=2.0)
    finally:
        runtime.event_bus.unsubscribe(CANCEL_BLOCK_REQUEST, capture)
        runtime.event_bus.unsubscribe(CANCEL_WORKFLOW_REQUEST, capture)

    assert (CANCEL_BLOCK_REQUEST, "node-3", "wf-2") in seen
    assert (CANCEL_WORKFLOW_REQUEST, None, "wf-2") in seen
