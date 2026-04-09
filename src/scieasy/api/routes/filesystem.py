"""Filesystem browsing endpoint for the universal file/directory picker.

Provides ``GET /api/filesystem/browse?path=...`` which returns a single
level of directory listing.  Unlike the project tree endpoint this is
**not** restricted to the project root -- users need to browse to
executables, scripts, and data outside the project directory.

Security:
    * The path must exist and be a directory.
    * Symbolic-link targets are not followed beyond one level.
    * Hidden files (dot-prefixed on Unix) are excluded by default.
    * On Windows all entries are returned (hidden-flag filtering is a
      future enhancement).
"""

from __future__ import annotations

import os
import platform
import string
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/filesystem", tags=["filesystem"])


class FilesystemEntry(BaseModel):
    """A single entry in a directory listing."""

    name: str
    type: str  # "file" | "directory"
    size: int | None = None


class FilesystemBrowseResponse(BaseModel):
    """Response from the filesystem browse endpoint."""

    path: str
    entries: list[FilesystemEntry]


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
            # Skip entries we cannot stat (e.g. broken symlinks).
            continue

    return dirs + files


@router.get("/browse", response_model=FilesystemBrowseResponse)
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
