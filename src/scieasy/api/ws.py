"""WebSocket handler --- real-time block state and interactive signals."""

from __future__ import annotations

from fastapi import WebSocket


async def websocket_handler(websocket: WebSocket) -> None:
    """Handle a WebSocket connection for real-time workflow updates.

    The handler is responsible for:

    * accepting the connection
    * streaming block state transitions and log events
    * receiving interactive signals (e.g. manual-block approvals)
    * closing gracefully on disconnect

    Parameters
    ----------
    websocket:
        The incoming WebSocket connection managed by FastAPI / Starlette.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
