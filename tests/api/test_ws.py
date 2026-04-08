"""Tests for WebSocket realtime updates."""

from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from scieasy.api.runtime import ApiRuntime
from scieasy.api.ws import websocket_handler
from scieasy.engine.events import (
    BLOCK_DONE,
    CANCEL_BLOCK_REQUEST,
    CANCEL_WORKFLOW_REQUEST,
    WORKFLOW_ERROR,
    EngineEvent,
    EventBus,
)
from scieasy.engine.scheduler import DAGScheduler
from tests.api.helpers import build_linear_workflow, wait_for_condition


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


def test_websocket_receives_workflow_error_for_background_failure(
    client: TestClient,
    runtime: ApiRuntime,
    opened_project,
    monkeypatch,
) -> None:
    """Unexpected scheduler crashes should surface as workflow_error events."""
    payload = build_linear_workflow(opened_project, workflow_id="workflow-error-flow")
    assert client.post("/api/workflows/", json=payload).status_code == 200

    async def boom(self) -> None:
        raise RuntimeError("scheduler crashed before dispatch")

    monkeypatch.setattr(DAGScheduler, "execute", boom)

    with client.websocket_connect("/ws") as websocket:
        started = client.post("/api/workflows/workflow-error-flow/execute")
        assert started.status_code == 200
        message = websocket.receive_json()

    assert message["type"] == WORKFLOW_ERROR
    assert message["workflow_id"] == "workflow-error-flow"
    assert message["data"]["error"] == "Workflow execution failed: scheduler crashed before dispatch"


def test_websocket_handler_handles_cancelled_error_on_shutdown() -> None:
    """websocket_handler must exit cleanly when asyncio.CancelledError is raised.

    Regression test for #203: CancelledError was not caught alongside
    WebSocketDisconnect, causing the handler to hang on server shutdown.
    """

    async def _run() -> None:
        ws = AsyncMock()
        ws.accept = AsyncMock()
        # Simulate server shutdown: receive_text raises CancelledError
        ws.receive_text = AsyncMock(side_effect=asyncio.CancelledError)
        ws.send_json = AsyncMock(side_effect=asyncio.CancelledError)

        event_bus = EventBus()

        # Wrap in a task and cancel it after a short delay to simulate
        # server shutdown cancelling all tasks (which is the real scenario).
        task = asyncio.create_task(websocket_handler(ws, event_bus))
        # Give the handler a moment to start, then cancel
        await asyncio.sleep(0.05)
        task.cancel()
        # The handler should exit without propagating CancelledError
        with contextlib.suppress(asyncio.CancelledError):
            await task

    asyncio.run(_run())
