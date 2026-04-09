"""FastAPI app factory, lifespan, CORS, and realtime endpoints."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from scieasy.api.routes import ai, blocks, data, filesystem, projects, workflows
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
    cors_origins_raw = os.getenv("SCIEASY_CORS_ORIGINS", "").strip()
    if cors_origins_raw == "*":
        origins: list[str] = ["*"]
    elif cors_origins_raw:
        origins = [o.strip() for o in cors_origins_raw.split(",")]
    else:
        origins = [
            "http://localhost:5173",
            "http://localhost:8000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8000",
        ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(workflows.router)
    app.include_router(blocks.router)
    app.include_router(data.router)
    app.include_router(filesystem.router)
    app.include_router(projects.router)
    app.include_router(ai.router)

    @app.get("/api/logs/stream")
    async def logs_stream(request: Request) -> object:
        return await sse_handler(request)

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        runtime = app.state.runtime
        await websocket_handler(websocket, runtime.event_bus)

    # SPA static files. Must be registered AFTER all /api/* and /ws routes.
    # Two locations are checked, in order:
    #   1. Packaged assets at ``scieasy/api/static/`` — populated by the
    #      setuptools build hook from ``frontend/dist/`` when building wheels.
    #   2. Editable-install fallback at ``<repo-root>/frontend/dist/`` — so
    #      developers can ``pip install -e . && (cd frontend && npm run build)``
    #      and get the SPA without running the full wheel build.
    # If neither is present, ``GET /`` redirects to the API docs so users
    # still land on something useful.
    static_dir = _resolve_spa_static_dir()
    if static_dir is not None:
        app.mount("/", SPAStaticFiles(directory=str(static_dir), html=True), name="spa")
    else:

        @app.get("/", include_in_schema=False)
        async def root() -> RedirectResponse:
            return RedirectResponse(url="/docs")

    return app


def _resolve_spa_static_dir() -> Path | None:
    """Locate the built SPA assets, preferring packaged over dev layout.

    Returns the first directory that contains an ``index.html``, or ``None``
    if no built SPA is available. See ``create_app`` for the resolution
    order and rationale.
    """
    packaged = Path(__file__).parent / "static"
    if (packaged / "index.html").is_file():
        return packaged

    # Walk up from ``src/scieasy/api/app.py`` to the repo root and look for
    # ``frontend/dist/``. Only used for editable installs where ``__file__``
    # is still inside the source tree.
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "frontend" / "dist"
        if (candidate / "index.html").is_file():
            # #406: Warn developers when frontend/src has files newer than
            # dist/index.html — the built SPA may be stale.  This check is
            # best-effort (errors are silently swallowed) and emits a warning
            # only; it never blocks startup.
            src_dir = parent / "frontend" / "src"
            if src_dir.exists():
                try:
                    src_mtime = max(
                        (f.stat().st_mtime for f in src_dir.rglob("*") if f.is_file()),
                        default=0.0,
                    )
                    dist_mtime = (candidate / "index.html").stat().st_mtime
                    if src_mtime > dist_mtime:
                        import logging

                        logging.getLogger(__name__).warning(
                            "frontend/dist may be stale (frontend/src has newer files than "
                            "dist/index.html). Run 'cd frontend && npm run build' to rebuild."
                        )
                except Exception:
                    pass
            return candidate
        if (parent / "pyproject.toml").is_file():
            # Reached the repo root without finding frontend/dist/
            break
    return None
