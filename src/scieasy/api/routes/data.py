"""Data upload, metadata, preview endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, UploadFile

from scieasy.api.schemas import DataPreviewResponse, DataUploadResponse

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("/upload", response_model=DataUploadResponse)
async def upload_data(file: UploadFile) -> dict[str, Any]:
    """Upload a data file and register it in the object store.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.get("/{data_ref}/metadata")
async def get_data_metadata(data_ref: str) -> dict[str, Any]:
    """Return metadata for a stored data object.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError


@router.get("/{data_ref}/preview", response_model=DataPreviewResponse)
async def preview_data(data_ref: str) -> dict[str, Any]:
    """Return a lightweight preview of a stored data object.

    Raises
    ------
    NotImplementedError
        Phase-1 skeleton --- not yet implemented.
    """
    raise NotImplementedError
