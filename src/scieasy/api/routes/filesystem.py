"""Filesystem browsing and reveal endpoints for the project tree."""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from scieasy.api.deps import get_runtime
from scieasy.api.runtime import ApiRuntime

router = APIRouter(tags=["filesystem"])
RuntimeDep = Annotated[ApiRuntime, Depends(get_runtime)]


class TreeEntry(BaseModel):
    """A single file or directory entry in a project tree listing."""

    name: str
    type: str  # "file" or "directory"
    size: int | None = None


class TreeResponse(BaseModel):
    """Response body for a single-level directory listing."""

    entries: list[TreeEntry] = Field(default_factory=list)


class RevealRequest(BaseModel):
    """Request body for the filesystem reveal action."""

    path: str


@router.get(
    "/api/projects/{project_id}/tree",
    response_model=TreeResponse,
)
async def project_tree(
    project_id: str,
    runtime: RuntimeDep,
    path: str = Query("", description="Relative path within the project root"),
) -> TreeResponse:
    """Return one level of directory listing for a project (lazy loading).

    Directories are listed first, then files, both sorted alphabetically.
    Path traversal via ``..`` is rejected.
    """
    # Resolve project root
    project = runtime.known_projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    project_root = Path(project.path).resolve()

    # Security: reject path traversal
    if ".." in path.split("/") or ".." in path.split("\\"):
        raise HTTPException(status_code=400, detail="Path traversal is not allowed")

    target = (project_root / path).resolve()
    # Ensure target is within project root
    try:
        target.relative_to(project_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Path is outside project root") from exc

    if not target.is_dir():
        raise HTTPException(status_code=404, detail="Directory not found")

    dirs: list[TreeEntry] = []
    files: list[TreeEntry] = []
    try:
        for child in target.iterdir():
            # Skip hidden files/directories
            if child.name.startswith("."):
                continue
            if child.is_dir():
                dirs.append(TreeEntry(name=child.name, type="directory"))
            elif child.is_file():
                try:
                    size = child.stat().st_size
                except OSError:
                    size = None
                files.append(TreeEntry(name=child.name, type="file", size=size))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Permission denied") from exc

    dirs.sort(key=lambda e: e.name.lower())
    files.sort(key=lambda e: e.name.lower())
    return TreeResponse(entries=dirs + files)


@router.post("/api/filesystem/reveal")
async def reveal_in_explorer(body: RevealRequest) -> dict[str, str]:
    """Open the native file explorer and select/reveal the given path."""
    target = Path(body.path).resolve()
    if not target.exists():
        raise HTTPException(status_code=404, detail="Path does not exist")

    system = platform.system()
    try:
        if system == "Windows":
            subprocess.Popen(["explorer", "/select,", str(target)])
        elif system == "Darwin":
            subprocess.Popen(["open", "-R", str(target)])
        else:
            # Linux/other: open the parent directory
            parent = str(target.parent) if target.is_file() else str(target)
            subprocess.Popen(["xdg-open", parent])
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not find the file explorer command for this platform",
        ) from exc

    return {"status": "ok"}
