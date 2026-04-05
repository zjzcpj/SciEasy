"""FastAPI dependency injection (engine, registry, etc.)."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from scieasy.engine.runners.process_handle import ProcessRegistry


def get_engine() -> Any:
    """Return the shared workflow execution engine instance.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


def get_block_registry() -> Any:
    """Return the shared block registry instance.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


def get_type_registry() -> Any:
    """Return the shared type registry instance.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


def get_lineage_store() -> Any:
    """Return the shared lineage / provenance store instance.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


def get_process_registry(request: Request) -> ProcessRegistry:
    """Retrieve the shared ProcessRegistry from app state.

    The registry is created during the application lifespan startup
    (see :func:`scieasy.api.app._lifespan`).

    Parameters
    ----------
    request : Request
        The current FastAPI request (injected automatically).

    Returns
    -------
    ProcessRegistry
        The shared process registry instance.

    Raises
    ------
    RuntimeError
        If called before the application lifespan has started.
    """
    registry: ProcessRegistry | None = getattr(request.app.state, "registry", None)
    if registry is None:
        raise RuntimeError("ProcessRegistry not initialized -- app lifespan not started")
    return registry
