"""Workflow CRUD and execution endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from scieasy.api.deps import get_runtime
from scieasy.api.runtime import ApiRuntime
from scieasy.api.schemas import (
    CancelPropagationResponse,
    ExecuteFromRequest,
    ExecuteFromResponse,
    WorkflowCreate,
    WorkflowEdge,
    WorkflowExecutionResponse,
    WorkflowNode,
    WorkflowResponse,
)
from scieasy.blocks.base.state import BlockState

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
RuntimeDep = Annotated[ApiRuntime, Depends(get_runtime)]


def _workflow_response(definition: Any) -> WorkflowResponse:
    return WorkflowResponse(
        id=definition.id,
        version=definition.version,
        description=definition.description,
        nodes=[
            WorkflowNode(
                id=node.id,
                block_type=node.block_type,
                config=node.config,
                execution_mode=node.execution_mode,
                layout=node.layout,
            )
            for node in definition.nodes
        ],
        edges=[WorkflowEdge(source=edge.source, target=edge.target) for edge in definition.edges],
        metadata=definition.metadata,
    )


@router.get("/list", response_model=list[str])
async def list_workflows(runtime: RuntimeDep) -> list[str]:
    """List workflow IDs available in the active project."""
    try:
        return runtime.list_project_workflows()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import", response_model=WorkflowResponse)
async def import_workflow(file: UploadFile, runtime: RuntimeDep) -> WorkflowResponse:
    """Import an external YAML workflow file into the active project."""
    if not file.filename or not file.filename.endswith((".yaml", ".yml")):
        raise HTTPException(status_code=400, detail="Only .yaml/.yml files are accepted.")
    try:
        content = await file.read()
        import tempfile

        from scieasy.workflow.serializer import load_yaml, save_yaml

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="wb") as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            definition = load_yaml(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

        save_yaml(definition, runtime.workflow_path(definition.id))
        return _workflow_response(definition)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import-path", response_model=WorkflowResponse)
async def import_workflow_from_path(body: dict, runtime: RuntimeDep) -> WorkflowResponse:
    """Import a workflow from a filesystem path (returned by the browse dialog)."""
    file_path = body.get("path")
    if not file_path:
        raise HTTPException(status_code=400, detail="Missing 'path' field.")
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    if path.suffix.lower() not in (".yaml", ".yml"):
        raise HTTPException(status_code=400, detail="Only .yaml/.yml files are accepted.")
    try:
        from scieasy.workflow.serializer import load_yaml, save_yaml

        definition = load_yaml(path)
        save_yaml(definition, runtime.workflow_path(definition.id))
        return _workflow_response(definition)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(body: WorkflowCreate, runtime: RuntimeDep) -> WorkflowResponse:
    """Create a new workflow from the supplied graph definition."""
    try:
        definition = runtime.save_workflow(body.model_dump())
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _workflow_response(definition)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, runtime: RuntimeDep) -> WorkflowResponse:
    """Retrieve a workflow by its identifier."""
    try:
        definition = runtime.load_workflow(workflow_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _workflow_response(definition)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    body: WorkflowCreate,
    runtime: RuntimeDep,
) -> WorkflowResponse:
    """Replace a workflow definition."""
    if workflow_id != body.id:
        raise HTTPException(status_code=400, detail="Workflow path/body IDs must match.")
    definition = runtime.save_workflow(body.model_dump())
    return _workflow_response(definition)


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str, runtime: RuntimeDep) -> None:
    """Delete a workflow."""
    runtime.delete_workflow(workflow_id)


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(workflow_id: str, runtime: RuntimeDep) -> WorkflowExecutionResponse:
    """Start execution of a workflow."""
    try:
        result = runtime.start_workflow(workflow_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return WorkflowExecutionResponse(**result)


@router.post("/{workflow_id}/pause", response_model=WorkflowExecutionResponse)
async def pause_workflow(workflow_id: str, runtime: RuntimeDep) -> WorkflowExecutionResponse:
    """Pause a running workflow."""
    try:
        run = runtime.get_run(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await run.scheduler.pause()
    return WorkflowExecutionResponse(workflow_id=workflow_id, status="paused", message="Pause requested.")


@router.post("/{workflow_id}/resume", response_model=WorkflowExecutionResponse)
async def resume_workflow(workflow_id: str, runtime: RuntimeDep) -> WorkflowExecutionResponse:
    """Resume a paused workflow."""
    try:
        run = runtime.get_run(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await run.scheduler.resume()
    return WorkflowExecutionResponse(workflow_id=workflow_id, status="running", message="Workflow resumed.")


@router.post("/{workflow_id}/cancel", response_model=CancelPropagationResponse)
async def cancel_workflow(workflow_id: str, runtime: RuntimeDep) -> CancelPropagationResponse:
    """Cancel an entire workflow."""
    try:
        run = runtime.get_run(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await run.scheduler.cancel_workflow()
    block_states = run.scheduler.block_states()
    cancelled = sorted(block_id for block_id, state in block_states.items() if state == BlockState.CANCELLED)
    skipped = sorted(block_id for block_id, state in block_states.items() if state == BlockState.SKIPPED)
    return CancelPropagationResponse(
        cancelled_blocks=cancelled,
        skipped_blocks=skipped,
        skip_reasons=dict(run.scheduler.skip_reasons),
    )


@router.post("/{workflow_id}/blocks/{block_id}/cancel", response_model=CancelPropagationResponse)
async def cancel_block(
    workflow_id: str,
    block_id: str,
    runtime: RuntimeDep,
) -> CancelPropagationResponse:
    """Cancel a single block within a workflow."""
    try:
        run = runtime.get_run(workflow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    await run.scheduler.cancel_block(block_id)
    block_states = run.scheduler.block_states()
    cancelled = [node_id for node_id, state in block_states.items() if state == BlockState.CANCELLED]
    skipped = [node_id for node_id, state in block_states.items() if state == BlockState.SKIPPED]
    return CancelPropagationResponse(
        cancelled_blocks=sorted(cancelled),
        skipped_blocks=sorted(skipped),
        skip_reasons=dict(run.scheduler.skip_reasons),
    )


@router.post("/{workflow_id}/execute-from", response_model=ExecuteFromResponse)
async def execute_from_workflow(
    workflow_id: str,
    body: ExecuteFromRequest,
    runtime: RuntimeDep,
) -> ExecuteFromResponse:
    """Re-run a workflow from a specific block using checkpointed inputs."""
    try:
        result = runtime.start_workflow(workflow_id, execute_from=body.block_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ExecuteFromResponse(**result)
