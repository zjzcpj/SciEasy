"""AI block generation, workflow suggestion, param optimisation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from scieasy.api.schemas import (
    AIGenerateBlockRequest,
    AIGenerateBlockResponse,
    AISuggestWorkflowRequest,
    AISuggestWorkflowResponse,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/generate-block", response_model=AIGenerateBlockResponse)
async def generate_block(body: AIGenerateBlockRequest) -> dict[str, Any]:
    """Generate a new block from a natural-language description.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.post("/suggest-workflow", response_model=AISuggestWorkflowResponse)
async def suggest_workflow(body: AISuggestWorkflowRequest) -> dict[str, Any]:
    """Suggest a complete workflow DAG given data and an analysis goal.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.post("/optimize-params")
async def optimize_params(block_id: str, intermediate_results: dict[str, Any]) -> dict[str, Any]:
    """Suggest parameter adjustments based on intermediate outputs.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
