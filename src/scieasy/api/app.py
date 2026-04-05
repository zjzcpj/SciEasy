"""FastAPI app factory, lifespan, CORS, and realtime endpoints."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from scieasy.api.routes import ai, blocks, data, projects, workflows
from scieasy.api.runtime import ApiRuntime
from scieasy.api.spa import SPAStaticFiles
from scieasy.api.sse import sse_handler
from scieasy.api.ws import websocket_handler
from scieasy.engine.runners.process_handle import ProcessRegistry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create and tear down the shared API runtime."""
    runtime = ApiRuntime()
    app.state.runtime = runtime
    app.state.registry = ProcessRegistry()
    try:
        yield
    finally:
        for run in runtime.workflow_runs.values():
            if not run.task.done():
                run.task.cancel()
        app.state.registry.terminate_all(grace_period_sec=5.0)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="SciEasy API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(workflows.router)
    app.include_router(blocks.router)
    app.include_router(data.router)
    app.include_router(projects.router)
    app.include_router(ai.router)

    @app.get("/api/logs/stream")
    async def logs_stream(request: Request) -> object:
        return await sse_handler(request)

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        runtime = app.state.runtime
        await websocket_handler(websocket, runtime.event_bus)

    # SPA static files (production) or redirect to API docs (development).
    # Must be registered AFTER all /api/* and /ws routes.
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", SPAStaticFiles(directory=str(static_dir), html=True), name="spa")
    else:

        @app.get("/", include_in_schema=False)
        async def root() -> RedirectResponse:
            return RedirectResponse(url="/docs")

    return app
