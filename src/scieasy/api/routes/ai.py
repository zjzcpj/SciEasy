"""AI block generation, workflow suggestion, param optimisation endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from scieasy.api.schemas import (
    AIGenerateBlockRequest,
    AIGenerateBlockResponse,
    AIOptimizeParamsRequest,
    AIOptimizeParamsResponse,
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


@router.post("/optimize-params", response_model=AIOptimizeParamsResponse)
async def optimize_params_endpoint(body: AIOptimizeParamsRequest) -> dict[str, Any]:
    """Suggest improved parameter values for a block using AI.

    Analyses intermediate results and the block's config schema to
    propose parameter changes that may improve workflow outcomes.
    """
    try:
        from scieasy.ai.optimization.param_optimizer import optimize_params

        result = optimize_params(
            block_id=body.block_id,
            intermediate_results=body.intermediate_results,
        )
        return result
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Parameter optimization not yet available",
        ) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
