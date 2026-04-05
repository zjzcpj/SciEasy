"""FastAPI app factory, lifespan, CORS, middleware."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from scieasy.engine.runners.process_handle import ProcessRegistry


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle -- startup and shutdown.

    On startup: creates a shared :class:`ProcessRegistry` for tracking
    block subprocesses.

    On shutdown: terminates all active subprocesses with a 5-second
    grace period before forced kill (ADR-017/019).
    """
    app.state.registry = ProcessRegistry()
    yield
    app.state.registry.terminate_all(grace_period_sec=5.0)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    This factory wires up:

    * lifespan context manager for startup/shutdown
    * CORS middleware (TODO: Phase 7)
    * route routers (TODO: Phase 7)
    * WebSocket and SSE endpoints (TODO: Phase 7)

    Returns
    -------
    FastAPI
        A fully configured but *not yet started* application instance.
    """
    app = FastAPI(
        title="SciEasy",
        description="AI-native workflow runtime for multimodal scientific data",
        version="0.1.0-dev",
        lifespan=_lifespan,
    )
    # TODO: Add CORS middleware, route routers, WS/SSE endpoints (Phase 7).
    return app
