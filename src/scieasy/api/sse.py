"""Server-Sent Events --- log streaming from execution."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import StreamingResponse


async def sse_handler(request: Request) -> StreamingResponse:
    """Stream execution logs to the client via Server-Sent Events.

    Parameters
    ----------
    request:
        The incoming HTTP request.  Used to detect client disconnects.

    Returns
    -------
    StreamingResponse
        A ``text/event-stream`` response that yields log lines as SSE
        frames until the execution completes or the client disconnects.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
