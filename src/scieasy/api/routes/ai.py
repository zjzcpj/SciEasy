"""AI block generation, workflow suggestion, param optimisation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from scieasy.api.schemas import (
    AIGenerateBlockRequest,
    AIGenerateBlockResponse,
    AISuggestWorkflowRequest,
    AISuggestWorkflowResponse,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/generate-block", response_model=AIGenerateBlockResponse)
async def generate_block(body: AIGenerateBlockRequest) -> dict[str, Any]:
    """Return a clear Phase 9 placeholder for block generation."""
    raise HTTPException(status_code=501, detail="AI block generation will arrive in Phase 9.")


@router.post("/suggest-workflow", response_model=AISuggestWorkflowResponse)
async def suggest_workflow(body: AISuggestWorkflowRequest) -> dict[str, Any]:
    """Return a clear Phase 9 placeholder for workflow suggestion."""
    raise HTTPException(status_code=501, detail="AI workflow suggestion will arrive in Phase 9.")


@router.post("/optimize-params")
async def optimize_params(block_id: str, intermediate_results: dict[str, Any]) -> dict[str, Any]:
    """Return a clear Phase 9 placeholder for parameter optimization."""
    raise HTTPException(status_code=501, detail="AI parameter optimization will arrive in Phase 9.")
