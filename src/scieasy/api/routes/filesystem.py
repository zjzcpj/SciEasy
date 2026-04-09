"""Filesystem browsing and reveal endpoints for the project tree and universal file picker."""

from __future__ import annotations

import os
import platform
import string
import subprocess
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from scieasy.api.deps import get_runtime
from scieasy.api.runtime import ApiRuntime

router = APIRouter(tags=["filesystem"])
RuntimeDep = Annotated[ApiRuntime, Depends(get_runtime)]


# ---------------------------------------------------------------------------
# Shared models
# ---------------------------------------------------------------------------


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


class FilesystemEntry(BaseModel):
    """A single entry in a filesystem browse listing."""

    name: str
    type: str  # "file" | "directory"
    size: int | None = None


class FilesystemBrowseResponse(BaseModel):
    """Response from the filesystem browse endpoint."""

    path: str
    entries: list[FilesystemEntry]


# ---------------------------------------------------------------------------
# Project tree endpoint (scoped to project root)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Universal filesystem browse endpoint (NOT project-scoped)
# ---------------------------------------------------------------------------


def _is_hidden(name: str) -> bool:
    """Return ``True`` for dot-prefixed names on non-Windows platforms."""
    if platform.system() == "Windows":
        return False
    return name.startswith(".")


def _list_roots() -> list[FilesystemEntry]:
    """Return filesystem roots (drive letters on Windows, ``/`` on Unix)."""
    if platform.system() == "Windows":
        entries: list[FilesystemEntry] = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.isdir(drive):
                entries.append(FilesystemEntry(name=drive, type="directory"))
        return entries
    return [FilesystemEntry(name="/", type="directory")]


def _list_directory(directory: Path) -> list[FilesystemEntry]:
    """Return one level of *directory* contents (dirs first, alpha)."""
    dirs: list[FilesystemEntry] = []
    files: list[FilesystemEntry] = []

    try:
        children = sorted(directory.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        return []

    for child in children:
        if _is_hidden(child.name):
            continue
        try:
            if child.is_dir():
                dirs.append(FilesystemEntry(name=child.name, type="directory"))
            else:
                try:
                    size = child.stat().st_size
                except OSError:
                    size = None
                files.append(FilesystemEntry(name=child.name, type="file", size=size))
        except (PermissionError, OSError):
            continue

    return dirs + files


@router.get("/api/filesystem/browse", response_model=FilesystemBrowseResponse)
async def browse_filesystem(
    path: str = Query("", description="Directory path to list. Empty string returns filesystem roots."),
) -> FilesystemBrowseResponse:
    """Return one level of directory listing at *path*.

    If *path* is empty, returns the filesystem roots (drive letters on
    Windows; ``/`` on Linux/macOS).
    """
    if not path:
        return FilesystemBrowseResponse(path="", entries=_list_roots())

    target = Path(path)
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Path does not exist: {path}")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

    entries = _list_directory(target)
    return FilesystemBrowseResponse(path=str(target), entries=entries)


# ---------------------------------------------------------------------------
# Reveal in native file explorer
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Native OS file/directory dialog
# ---------------------------------------------------------------------------


class NativeDialogRequest(BaseModel):
    """Request body for the native file/directory dialog."""

    mode: str = Field(..., pattern="^(file|directory)$", description="Dialog type: 'file' or 'directory'")
    initial_dir: str | None = Field(None, description="Optional starting directory for the dialog")


class NativeDialogResponse(BaseModel):
    """Response from the native dialog endpoint."""

    path: str | None = Field(None, description="Selected path, or null if cancelled")


# Per-session last-used directory (in-memory, resets on restart).
_last_used_directory: str | None = None


def _native_dialog_windows(mode: str, initial_dir: str | None) -> str | None:
    """Open a native Windows file/directory dialog via PowerShell."""
    if mode == "directory":
        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$d = New-Object System.Windows.Forms.FolderBrowserDialog;"
            f"$d.SelectedPath = '{initial_dir or ''}';"
            "if ($d.ShowDialog() -eq 'OK') {{ $d.SelectedPath }} else {{ '' }}"
        )
    else:
        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$d = New-Object System.Windows.Forms.OpenFileDialog;"
            f"$d.InitialDirectory = '{initial_dir or ''}';"
            "if ($d.ShowDialog() -eq 'OK') {{ $d.FileName }} else {{ '' }}"
        )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
        capture_output=True,
        text=True,
        timeout=120,
    )
    selected = result.stdout.strip()
    return selected if selected else None


def _native_dialog_macos(mode: str, initial_dir: str | None) -> str | None:
    """Open a native macOS file/directory dialog via osascript."""
    if mode == "directory":
        if initial_dir:
            script = f'choose folder with prompt "Select Directory" default location POSIX file "{initial_dir}"'
        else:
            script = 'choose folder with prompt "Select Directory"'
    else:
        if initial_dir:
            script = f'choose file with prompt "Select File" default location POSIX file "{initial_dir}"'
        else:
            script = 'choose file with prompt "Select File"'
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=120,
    )
    selected = result.stdout.strip()
    if not selected:
        return None
    # osascript returns "alias Macintosh HD:Users:foo:..." — convert to POSIX
    if selected.startswith("alias "):
        # Convert colon-separated HFS path to POSIX
        parts = selected[len("alias ") :].split(":")
        # First part is the volume name — on default installs, map to /
        posix = "/" + "/".join(parts[1:])
        # Remove trailing slash if present
        return posix.rstrip("/") or "/"
    return selected


def _native_dialog_linux(mode: str, initial_dir: str | None) -> str | None:
    """Open a native Linux file/directory dialog via zenity."""
    cmd = ["zenity", "--file-selection"]
    if mode == "directory":
        cmd.append("--directory")
    if initial_dir:
        cmd.extend(["--filename", initial_dir + "/"])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    selected = result.stdout.strip()
    return selected if selected else None


@router.post("/api/filesystem/native-dialog", response_model=NativeDialogResponse)
async def native_file_dialog(body: NativeDialogRequest) -> NativeDialogResponse:
    """Open a native OS file or directory dialog and return the selected path.

    Uses platform-specific subprocess calls (PowerShell on Windows, osascript
    on macOS, zenity on Linux). Returns ``{"path": null}`` if the user cancels.
    """
    global _last_used_directory

    # Determine starting directory: request param > last-used > home
    initial_dir = body.initial_dir
    if not initial_dir or not Path(initial_dir).is_dir():
        initial_dir = _last_used_directory
    if not initial_dir or not Path(initial_dir).is_dir():
        initial_dir = str(Path.home())

    system = platform.system()
    try:
        if system == "Windows":
            selected = _native_dialog_windows(body.mode, initial_dir)
        elif system == "Darwin":
            selected = _native_dialog_macos(body.mode, initial_dir)
        else:
            selected = _native_dialog_linux(body.mode, initial_dir)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Native dialog command not available on this platform ({system})",
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=504,
            detail="Dialog timed out (user may have left the dialog open)",
        ) from exc

    # Track last-used directory for the session
    if selected:
        parent = str(Path(selected).parent) if Path(selected).is_file() else selected
        _last_used_directory = parent

    return NativeDialogResponse(path=selected)
