"""Project CRUD, workspace management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/")
async def create_project(name: str, description: str = "") -> dict[str, Any]:
    """Create a new project workspace.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.get("/")
async def list_projects() -> list[dict[str, Any]]:
    """List all projects accessible to the current user.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.get("/{project_id}")
async def get_project(project_id: str) -> dict[str, Any]:
    """Retrieve a single project by identifier.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.put("/{project_id}")
async def update_project(project_id: str, name: str | None = None, description: str | None = None) -> dict[str, Any]:
    """Update project metadata.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str) -> None:
    """Delete a project and its associated resources.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
