"""FastAPI app factory, lifespan, CORS, middleware."""

from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    This factory wires up:

    * CORS middleware
    * route routers (workflows, blocks, data, ai, projects)
    * WebSocket and SSE endpoints
    * lifespan context manager for startup/shutdown

    Returns
    -------
    FastAPI
        A fully configured but *not yet started* application instance.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
