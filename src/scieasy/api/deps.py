"""FastAPI dependency injection (engine, registry, etc.)."""

from __future__ import annotations

from typing import Any


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
