"""Block palette listing, connection validation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from scieasy.api.schemas import BlockConnectionValidation, BlockListResponse

router = APIRouter(prefix="/api/blocks", tags=["blocks"])


@router.get("/", response_model=BlockListResponse)
async def list_blocks() -> dict[str, Any]:
    """Return the full block palette available in the current registry.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.get("/{block_type}/schema")
async def get_block_schema(block_type: str) -> dict[str, Any]:
    """Return the JSON Schema for a block type's parameters and ports.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.post("/validate-connection")
async def validate_connection(body: BlockConnectionValidation) -> dict[str, Any]:
    """Validate whether two ports can be connected.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
