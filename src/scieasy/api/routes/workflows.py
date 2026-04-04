"""Workflow CRUD, execute, pause, resume endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from scieasy.api.schemas import WorkflowCreate, WorkflowResponse

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(body: WorkflowCreate) -> dict[str, Any]:
    """Create a new workflow from the supplied graph definition.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str) -> dict[str, Any]:
    """Retrieve a workflow by its identifier.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, body: WorkflowCreate) -> dict[str, Any]:
    """Replace a workflow definition.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str) -> None:
    """Delete a workflow.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: str) -> dict[str, Any]:
    """Start execution of a workflow.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: str) -> dict[str, Any]:
    """Pause a running workflow.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.post("/{workflow_id}/resume")
async def resume_workflow(workflow_id: str) -> dict[str, Any]:
    """Resume a paused workflow.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


# -- ADR-018: Cancellation endpoints ----------------------------------------


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str) -> dict[str, Any]:
    """Cancel an entire workflow (ADR-018).

    Terminates all active block subprocesses and propagates SKIPPED
    to downstream blocks with unsatisfiable inputs.

    TODO(ADR-018): Emit CANCEL_WORKFLOW_REQUEST via EventBus.
    Return CancelPropagationResponse with cancelled/skipped blocks.
    """
    raise NotImplementedError


@router.post("/{workflow_id}/blocks/{block_id}/cancel")
async def cancel_block(workflow_id: str, block_id: str) -> dict[str, Any]:
    """Cancel a single block within a workflow (ADR-018).

    Terminates the block's subprocess and propagates SKIPPED to
    downstream blocks whose required inputs are now unsatisfiable.

    TODO(ADR-018): Emit CANCEL_BLOCK_REQUEST via EventBus.
    Return CancelPropagationResponse with cancelled/skipped blocks.
    """
    raise NotImplementedError
