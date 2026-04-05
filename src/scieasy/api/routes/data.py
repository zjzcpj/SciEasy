"""Data upload, metadata, and preview endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from scieasy.api.deps import get_runtime
from scieasy.api.runtime import ApiRuntime
from scieasy.api.schemas import DataMetadataResponse, DataPreviewResponse, DataUploadResponse

router = APIRouter(prefix="/api/data", tags=["data"])
UploadFileParam = Annotated[UploadFile, File(...)]
RuntimeDep = Annotated[ApiRuntime, Depends(get_runtime)]


@router.post("/upload", response_model=DataUploadResponse)
async def upload_data(
    file: UploadFileParam,
    runtime: RuntimeDep,
) -> DataUploadResponse:
    """Upload a data file and register it in the active project."""
    payload = runtime.upload_file(file.filename or "upload.bin", await file.read())
    return DataUploadResponse(**payload)


@router.get("/{data_ref}", response_model=DataMetadataResponse)
@router.get("/{data_ref}/metadata", response_model=DataMetadataResponse, include_in_schema=False)
async def get_data_metadata(data_ref: str, runtime: RuntimeDep) -> DataMetadataResponse:
    """Return metadata for a stored data object."""
    try:
        record = runtime.get_data_record(data_ref)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DataMetadataResponse(ref=record.id, type_name=record.type_name, metadata=record.metadata)


@router.get("/{data_ref}/preview", response_model=DataPreviewResponse)
async def preview_data(data_ref: str, runtime: RuntimeDep) -> DataPreviewResponse:
    """Return a lightweight preview of a stored data object."""
    try:
        record = runtime.get_data_record(data_ref)
        preview = runtime.preview_data(data_ref)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DataPreviewResponse(ref=record.id, type_name=record.type_name, preview=preview)
