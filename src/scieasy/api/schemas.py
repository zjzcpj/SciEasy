"""Pydantic models for all API request/response shapes."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


class WorkflowCreate(BaseModel):
    """Request body for creating a new workflow."""

    id: str
    description: str = ""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []


class WorkflowResponse(BaseModel):
    """Response body returned when reading a workflow."""

    id: str
    version: str = "1.0.0"
    description: str = ""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------


class BlockListResponse(BaseModel):
    """Response body for the block palette listing."""

    blocks: list[dict[str, Any]] = []


class BlockConnectionValidation(BaseModel):
    """Request body for validating a proposed port connection."""

    source_block: str
    source_port: str
    target_block: str
    target_port: str


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


class DataUploadResponse(BaseModel):
    """Response body after a successful data upload."""

    ref: str
    type_name: str
    metadata: dict[str, Any] = {}


class DataPreviewResponse(BaseModel):
    """Response body for a lightweight data preview."""

    ref: str
    type_name: str
    preview: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------


class AIGenerateBlockRequest(BaseModel):
    """Request body for AI block generation."""

    description: str
    block_category: str | None = None


class AIGenerateBlockResponse(BaseModel):
    """Response body after AI block generation."""

    code: str
    block_name: str
    validation_passed: bool


class AISuggestWorkflowRequest(BaseModel):
    """Request body for AI workflow suggestion."""

    data_description: str
    goal: str


class AISuggestWorkflowResponse(BaseModel):
    """Response body after AI workflow suggestion."""

    workflow: dict[str, Any] = {}
    explanation: str = ""


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


# -- ADR-018: Cancellation schemas ----------------------------------------


class CancelBlockRequest(BaseModel):
    """Request body for cancelling a single block (ADR-018)."""

    block_id: str


class CancelWorkflowRequest(BaseModel):
    """Request body for cancelling an entire workflow (ADR-018).

    Empty body — workflow_id comes from the URL path parameter.
    """


class CancelPropagationResponse(BaseModel):
    """Response body after cancellation propagation (ADR-018)."""

    cancelled_blocks: list[str] = []
    skipped_blocks: list[str] = []
    skip_reasons: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all endpoints on failure."""

    detail: str
    error_code: str | None = None
